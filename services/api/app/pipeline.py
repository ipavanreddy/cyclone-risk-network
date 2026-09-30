"""Deterministic hazard → exposure pipeline for one scenario (PRD §32):
bulletin parse → track set + wind → surge → rainfall flood → exposure + road cut-off + Village Risk."""
import hashlib
import json
import threading
from datetime import UTC, datetime, timedelta

from app.exposure import network, risk
from app.flood_model import model as flood_model
from app.forecast_ingest import service as ingest
from app.forecast_ingest import track as trk
from app.geospatial import earth_engine
from app.replays import Replay, parse_scenario_id
from app.surge import model as surge_model

WIND_HIGH_KMH = 150
_cache: dict[str, dict] = {}
_lock = threading.Lock()


def _neigh_max(grid, arr: list[float], lat: float, lon: float) -> float:
    """Village footprint ≈ 3×3 cells (~4 km): take the maximum."""
    i = grid.index(lat, lon)
    if i is None:
        return 0.0
    r, c = divmod(i, grid.cols)
    vals = [arr[rr * grid.cols + cc] for rr in range(r - 1, r + 2) for cc in range(c - 1, c + 2)
            if 0 <= rr < grid.rows and 0 <= cc < grid.cols]
    return max(vals) if vals else 0.0


def _cell(grid, arr, lat, lon, default=0.0):
    i = grid.index(lat, lon)
    return arr[i] if i is not None else default


def scenario_track(scenario_id: str) -> tuple[Replay, dict, dict, list[dict], dict | None]:
    replay, step = parse_scenario_id(scenario_id)
    parsed = ingest.parse_for_scenario(scenario_id, step["bulletin_text"])
    verification = ingest.get_verification(scenario_id)
    track = verification["track"] if verification else parsed["parse"]["track"]
    return replay, step, parsed, track, verification


def run(scenario_id: str) -> dict:
    replay, step, parsed, track, verification = scenario_track(scenario_id)
    key = scenario_id + hashlib.sha1(json.dumps(track, sort_keys=True).encode()).hexdigest()[:10]
    with _lock:
        if key not in _cache:
            _cache[key] = _compute(scenario_id, replay, step, parsed, track, verification)
        result = _cache[key]
    # verification status can change without the track changing
    result["scenario"]["track_verified"] = verification is not None
    result["scenario"]["track_verification"] = verification
    return result


def _compute(scenario_id: str, replay: Replay, step: dict, parsed: dict, track: list[dict],
             verification: dict | None) -> dict:
    mp = replay.scenario["model_params"]
    issued = datetime.fromisoformat(step["issued_at"])
    pts = trk.from_parse(track, step["issued_at"])
    base = earth_engine.enrich_base(replay) or replay.base
    grid = base.grid
    lf = trk.landfall(pts, base.coast)
    lf_time = datetime.fromisoformat(lf["time"])

    wind, arrival = trk.wind_field(pts, grid, mp["rmw_km"], lf_time)
    surge = surge_model.run(base, pts, surge_model.SurgeParams(
        rmw_km=mp["rmw_km"], shelf_factor=mp["shelf_factor"], tide_expected_m=mp["tide_m"]["expected"],
        tide_high_m=mp["tide_m"]["high"], inland_decay_m_per_km=mp["surge_inland_decay_m_per_km"]))
    ee_rain = earth_engine.gpm_rainfall(replay, issued, issued + timedelta(hours=72))
    if ee_rain:
        rain, rain_source = ee_rain, "GPM IMERG observed accumulation (Earth Engine; perfect-forecast proxy in replay)"
    else:
        rain = flood_model.rainfall_72h(pts, grid, issued, mp["rmw_km"], mp["rain_r0_mm_h"])
        rain_source = "Parametric rain field around forecast track (demo)"
    flood = flood_model.run(base, rain, mp["antecedent_wetness"], rain_source)

    se, sh, fl = surge["depth_expected"], surge["depth_high"], flood["flood_likelihood"]
    shelters = [a for a in replay.assets if a.type == "shelter"]
    net = network.analyse(grid, replay.roads, se, fl, replay.scenario["hub"]["id"],
                          [s.asset_id for s in shelters], [v.village_code for v in replay.villages])
    ee_exposure = earth_engine.village_exposure(replay) or {}

    villages = []
    for v in replay.villages:
        pop = int(ee_exposure.get(v.village_code, {}).get("population") or v.population)
        reach = net["villages"][v.village_code]
        h = {
            "surge_depth_expected_m": round(_neigh_max(grid, se, v.lat, v.lon), 2),
            "surge_depth_high_m": round(_neigh_max(grid, sh, v.lat, v.lon), 2),
            "flood_likelihood": round(_neigh_max(grid, fl, v.lat, v.lon), 2),
            "rain_72h_mm": round(_cell(grid, rain, v.lat, v.lon), 0),
            "max_wind_kmh": round(_cell(grid, wind, v.lat, v.lon), 0),
            "gale_arrival_hours_before_landfall": _cell(grid, arrival, v.lat, v.lon, None),
        }
        f = risk.factors(h["surge_depth_expected_m"], h["surge_depth_high_m"], h["flood_likelihood"],
                         h["max_wind_kmh"], pop, v.vulnerability_index, reach["shelter_reachable"])
        s, contrib = risk.score(f, replay.state.risk_weights)
        villages.append({**v.model_dump(), "population": pop, **h, **reach, "risk_score": s,
                         "risk_band": risk.band(s), "factors": {k: round(x, 3) for k, x in f.items()},
                         "contributions": contrib,
                         "buildings": ee_exposure.get(v.village_code, {}).get("buildings")})
    villages.sort(key=lambda x: -x["risk_score"])
    for rank, v in enumerate(villages, start=1):
        v["priority_rank"] = rank

    # shelter load: 50 % of residents of High/Very High villages need public shelter (sample assumption)
    load: dict[str, int] = {}
    for v in villages:
        if v["risk_band"] in ("High", "Very High") and v["nearest_reachable_shelter"]:
            load[v["nearest_reachable_shelter"]] = load.get(v["nearest_reachable_shelter"], 0) + v["population"] // 2
    assets = []
    for a in replay.assets:
        hz = []
        d_exp, d_high = _cell(grid, se, a.lat, a.lon), _cell(grid, sh, a.lat, a.lon)
        p_fl, w = _cell(grid, fl, a.lat, a.lon), _cell(grid, wind, a.lat, a.lon)
        if d_exp >= 0.1:
            hz.append("surge")
        elif d_high >= 0.3:
            hz.append("surge (high case)")
        if p_fl >= 0.65:
            hz.append("flood")
        if w >= WIND_HIGH_KMH:
            hz.append("wind")
        item = {**a.model_dump(), "hazards": hz, "exposed": bool(hz), "surge_depth_expected_m": round(d_exp, 2),
                "surge_depth_high_m": round(d_high, 2), "flood_likelihood": round(p_fl, 2), "max_wind_kmh": round(w)}
        if a.type == "shelter":
            item.update({"safe": a.asset_id in net["safe_shelters"], "cut_off": a.asset_id in net["cut_off_shelters"],
                         "assigned_evacuees": load.get(a.asset_id, 0),
                         "over_capacity": load.get(a.asset_id, 0) > (a.capacity or 0)})
        assets.append(item)

    high = [v for v in villages if v["risk_band"] in ("High", "Very High")]
    safe_ids = set(net["safe_shelters"])
    reachable_ids = {v["nearest_reachable_shelter"] for v in villages if v["nearest_reachable_shelter"]}
    key_numbers = {
        "people_high_risk": sum(v["population"] for v in high),
        "villages_high_risk": len(high),
        "people_in_surge_zone": sum(v["population"] for v in villages if v["surge_depth_expected_m"] > 0),
        "substations_exposed": sum(1 for a in assets if a["type"] == "substation" and a["exposed"]),
        "hospitals_exposed": sum(1 for a in assets if a["type"] == "hospital" and a["exposed"]),
        "shelters_exposed": sum(1 for a in assets if a["type"] == "shelter" and a["exposed"]),
        "shelters_cut_off": len(net["cut_off_shelters"]),
        "villages_without_reachable_shelter": sum(1 for v in villages if not v["shelter_reachable"]),
        "roads_cut": len(net["roads_cut"]),
        "evacuation_demand": sum(load.values()),
        "reachable_shelter_capacity": sum(a.capacity or 0 for a in shelters
                                          if a.asset_id in safe_ids and a.asset_id in reachable_ids),
    }

    hours_to_landfall = round((lf_time - issued).total_seconds() / 3600, 1)
    cone = trk.cone_polygon(pts)
    members = [{"k": k, "line": [[round(p.lat, 3), round(p.lon, 3)] for p in m]} for k, m in trk.track_set(pts)]
    obs = {o["village_code"]: o["observed_flooded"] for o in replay.observed_flood["villages"]}
    return {
        "scenario": {
            "scenario_id": scenario_id, "replay_id": replay.replay_id, "cyclone_name": replay.scenario["cyclone_name"],
            "mode": "replay", "state": replay.state.state, "state_name": replay.state.state_name,
            "district": replay.scenario["district"], "step": step["step"],
            "hours_before_actual_landfall": step["hours_before_landfall"],
            "forecast_issued_at": step["issued_at"], "bulletin_no": step["bulletin_no"],
            "source": replay.metadata["scenario"].source, "track": track, "track_set_size": len(trk.TRACK_SET_K),
            "created_at": datetime.now(UTC).isoformat(), "track_verified": verification is not None,
            "forecast_landfall": {"time": lf["time"], "lat": round(lf["lat"], 3), "lon": round(lf["lon"], 3),
                                  "max_wind_kmh": round(lf["vmax"]), "central_pressure_hpa": lf["pc"]},
            "hours_to_forecast_landfall": hours_to_landfall,
            "stage": stage_for(hours_to_landfall),
            "languages": replay.state.languages, "issuing_authority": replay.state.issuing_authority,
        },
        "bulletin": {"text": step["bulletin_text"], **parsed},
        "track": {"points": track, "cone": cone, "members": members,
                  "cone_radius_at_landfall_km": round(trk.cone_radius_km(hours_to_landfall)),
                  "error_table_km": trk.ERROR_TABLE_KM},
        "grid": {**grid.__dict__, "bbox": grid.bbox},
        "layers": {"surge_expected": se, "surge_high": sh, "flood_likelihood": fl, "rain_72h": rain,
                   "wind_max": wind, "gale_arrival": arrival, "water": base.water},
        "surge": {k: v for k, v in surge.items() if k not in ("depth_expected", "depth_high")},
        "flood": {k: v for k, v in flood.items() if k not in ("rain_72h_mm", "flood_likelihood")},
        "wind": {"model": "Modified Rankine vortex (Rmw %s km)" % mp["rmw_km"],
                 "max_kmh": max(wind), "high_wind_threshold_kmh": WIND_HIGH_KMH},
        "villages": villages,
        "assets": assets,
        "network": {**{k: v for k, v in net.items() if k != "villages"}, "roads": _road_lines(replay, net)},
        "key_numbers": key_numbers,
        "validation": {
            "method": "Predicted (surge expected > 0 or flood likelihood ≥ 0.65) vs observed flooded villages",
            "observed_source": replay.metadata["observed_flood"].model_dump(),
            "villages": [{"village_code": v["village_code"], "name": v["name"],
                          "predicted_flooded": v["surge_depth_expected_m"] > 0 or v["flood_likelihood"] >= 0.65,
                          "observed_flooded": obs.get(v["village_code"])} for v in villages],
        },
        "freshness": freshness(replay, step, base),
        "risk_model": {"weights": replay.state.risk_weights, "bands": risk.BANDS,
                       "doc": risk.__doc__.strip()},
    }


def _road_lines(replay: Replay, net: dict) -> list[dict]:
    nodes = {n["id"]: n for n in replay.roads["nodes"]}
    cut = {e["edge_id"] for e in net["cut_edges"]}
    return [{"edge_id": e["edge_id"], "road": e["road"], "kind": e["kind"], "cut": e["edge_id"] in cut,
             "coords": [[nodes[e["from"]]["lat"], nodes[e["from"]]["lon"]], [nodes[e["to"]]["lat"], nodes[e["to"]]["lon"]]]}
            for e in replay.roads["edges"]]


def stage_for(hours: float) -> str:
    if hours > 54:
        return "watch"
    if hours > 30:
        return "warning"
    if hours > 9:
        return "evacuation_order"
    return "final_warning"


def freshness(replay: Replay, step: dict, base) -> list[dict]:
    newer = [s for s in replay.scenario["steps"] if s["hours_before_landfall"] < step["hours_before_landfall"]]
    return [
        {"source": "Official bulletin (replay sample)", "timestamp": step["issued_at"],
         "note": f"Bulletin {step['bulletin_no']}; replay clock = issue time",
         "newer_available": bool(newer), "is_sample": True},
        {"source": "Terrain / water base layers", "timestamp": base.metadata.reference_timestamp,
         "note": base.metadata.source, "is_sample": base.metadata.is_sample},
        {"source": "Villages", "timestamp": replay.metadata["villages"].reference_timestamp,
         "note": replay.metadata["villages"].source, "is_sample": True},
        {"source": "Shelters & assets", "timestamp": replay.metadata["assets"].reference_timestamp,
         "note": replay.metadata["assets"].source, "is_sample": True},
        {"source": "Road network", "timestamp": replay.metadata["roads"].reference_timestamp,
         "note": replay.metadata["roads"].source, "is_sample": True},
    ]


def start_warmup() -> None:
    """Pre-compute every replay step in the background at startup (Gemini parses come from the Cloud Storage
    cache), so the first dashboard request after a Cloud Run cold start is fast. Skipped in forced demo mode."""
    import logging
    import threading

    from app.config import settings
    from app.replays import list_replays

    if settings.force_demo_mode:
        return

    def warm() -> None:
        for rp in list_replays():
            for st in rp["steps"]:
                try:
                    run(st["scenario_id"])
                except Exception as exc:  # noqa: BLE001
                    logging.getLogger(__name__).warning("warm-up %s failed: %s", st["scenario_id"], exc)

    threading.Thread(target=warm, name="pipeline-warmup", daemon=True).start()
