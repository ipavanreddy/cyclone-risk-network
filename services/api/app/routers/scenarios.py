"""Scenario, forecast, hazard, exposure and situation-report endpoints (PRD §37)."""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app import maps, pipeline
from app.forecast_ingest import service as ingest
from app.geospatial import earth_engine
from app.render import hazard_png
from app.replays import list_replays, parse_scenario_id
from app.situation_reasoning import service as sitrep

router = APIRouter(prefix="/api", tags=["scenarios"])
LAYERS = ["surge_expected", "surge_high", "flood_likelihood", "rain_72h", "wind_max", "gale_arrival", "water"]


def result_or_404(scenario_id: str) -> dict:
    try:
        return pipeline.run(scenario_id)
    except KeyError:
        raise HTTPException(404, f"unknown scenario {scenario_id}") from None


class ScenarioCreate(BaseModel):
    mode: str = "replay"
    replay_id: str = "fani-2019"
    step: str = "T72"


class BulletinIn(BaseModel):
    text: str


class TrackVerify(BaseModel):
    verified_by: str
    role: str = "District Disaster Management Officer"
    track: list[dict] | None = None


class SitrepIn(BaseModel):
    requested_by: str = "District Disaster Management Officer (demo)"
    role: str = "District Disaster Management Officer"


def summary(r: dict) -> dict:
    return {k: r[k] for k in ("scenario", "bulletin", "track", "surge", "flood", "wind", "key_numbers",
                              "freshness", "risk_model", "network")} | {"grid": r["grid"]}


@router.get("/replays")
def replays() -> list[dict]:
    return list_replays()


@router.post("/scenarios")
def create_scenario(body: ScenarioCreate) -> dict:
    if body.mode != "replay":
        raise HTTPException(400, "live mode is not part of the MVP; use mode='replay'")
    match = [r for r in list_replays() if r["replay_id"] == body.replay_id]
    if not match:
        raise HTTPException(404, f"unknown replay {body.replay_id}")
    return summary(result_or_404(f"{match[0]['code']}-{body.step}"))


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict:
    return summary(result_or_404(scenario_id))


@router.post("/bulletins/parse")
def parse_bulletin(body: BulletinIn) -> dict:
    if len(body.text.strip()) < 40:
        raise HTTPException(400, "bulletin text too short")
    return ingest.parse(body.text)


@router.post("/scenarios/{scenario_id}/track/verify")
def verify_track(scenario_id: str, body: TrackVerify) -> dict:
    try:
        _, step, parsed, _, _ = pipeline.scenario_track(scenario_id)
    except KeyError:
        raise HTTPException(404, f"unknown scenario {scenario_id}") from None
    if body.role not in ("District Disaster Management Officer", "State EOC Officer"):
        raise HTTPException(403, "unknown role")
    return ingest.verify_track(scenario_id, body.verified_by, body.role, body.track, parsed)


@router.post("/scenarios/{scenario_id}/surge")
def run_surge(scenario_id: str) -> dict:
    r = result_or_404(scenario_id)
    return {"scenario_id": scenario_id, **r["surge"]}


@router.post("/scenarios/{scenario_id}/flood")
def run_flood(scenario_id: str) -> dict:
    r = result_or_404(scenario_id)
    return {"scenario_id": scenario_id, **r["flood"]}


@router.get("/scenarios/{scenario_id}/hazards")
def hazards(scenario_id: str, layer: list[str] = Query(default=[])) -> dict:
    r = result_or_404(scenario_id)
    wanted = layer or LAYERS
    bad = [x for x in wanted if x not in LAYERS]
    if bad:
        raise HTTPException(400, f"unknown layers {bad}; choose from {LAYERS}")
    return {"scenario_id": scenario_id, "grid": r["grid"], "layers": {k: r["layers"][k] for k in wanted},
            "labels": {"surge": r["surge"]["label"], "flood": r["flood"]["label"]},
            "model": {"surge": [r["surge"]["model_name"], r["surge"]["model_version"]],
                      "flood": [r["flood"]["model_name"], r["flood"]["model_version"]]},
            "track": r["track"], "landfall": r["scenario"]["forecast_landfall"]}


@router.get("/scenarios/{scenario_id}/hazards.png")
def hazards_png(scenario_id: str, layer: str = "composite") -> Response:
    if layer not in ("composite", "surge", "flood", "wind"):
        raise HTTPException(400, "layer must be composite|surge|flood|wind")
    return Response(hazard_png(result_or_404(scenario_id), layer), media_type="image/png")


@router.get("/scenarios/{scenario_id}/hazards/ee-tiles")
def ee_tiles(scenario_id: str) -> dict:
    r = result_or_404(scenario_id)
    replay, _ = parse_scenario_id(scenario_id)
    lf = r["scenario"]["forecast_landfall"]
    tiles = earth_engine.inundation_tiles(replay, lf["lat"], lf["lon"],
                                          r["surge"]["peak_surge_expected_m"] + r["surge"]["tide_m"]["expected"],
                                          replay.scenario["model_params"]["surge_inland_decay_m_per_km"])
    return {"mode": "real" if tiles else "demo", "tiles": tiles}


@router.get("/scenarios/{scenario_id}/exposure")
def exposure(scenario_id: str, district: str | None = None) -> dict:
    r = result_or_404(scenario_id)
    if district and district != r["scenario"]["district"]:
        raise HTTPException(404, f"district {district} not in scenario")
    return {"scenario_id": scenario_id, "district": r["scenario"]["district"], "key_numbers": r["key_numbers"],
            "assets": r["assets"], "network": r["network"]}


@router.get("/scenarios/{scenario_id}/villages")
def villages(scenario_id: str, sort: str = "risk") -> list[dict]:
    r = result_or_404(scenario_id)
    vs = list(r["villages"])
    if sort == "name":
        vs.sort(key=lambda v: v["name"])
    elif sort == "population":
        vs.sort(key=lambda v: -v["population"])
    return vs


@router.get("/scenarios/{scenario_id}/shelters/reachability")
def shelters(scenario_id: str) -> dict:
    r = result_or_404(scenario_id)
    return {"scenario_id": scenario_id, "rule": r["network"]["rule"], "roads_cut": r["network"]["roads_cut"],
            "cut_edges": r["network"]["cut_edges"],
            "shelters": [a for a in r["assets"] if a["type"] == "shelter"],
            "villages": [{k: v[k] for k in ("village_code", "name", "shelter_reachable", "nearest_reachable_shelter",
                                            "shelter_distance_km")} for v in r["villages"]]}


@router.get("/scenarios/{scenario_id}/villages/{village_code}/route")
def village_route(scenario_id: str, village_code: str) -> dict:
    """Google Routes drive time (normal conditions) from a village to its nearest shelter that our flood/surge
    road-network model still considers reachable, plus the Google-geocoded locality."""
    r = result_or_404(scenario_id)
    v = next((x for x in r["villages"] if x["village_code"] == village_code), None)
    if v is None:
        raise HTTPException(404, f"unknown village {village_code}")
    shelter = next((a for a in r["assets"] if a["asset_id"] == v["nearest_reachable_shelter"]), None)
    route = maps.drive_route(v["lat"], v["lon"], shelter["lat"], shelter["lon"]) if shelter else None
    return {"scenario_id": scenario_id, "village_code": village_code, "village": v["name"],
            "shelter_reachable": v["shelter_reachable"],
            "shelter": {k: shelter[k] for k in ("asset_id", "name", "lat", "lon")} if shelter else None,
            "network_distance_km": v["shelter_distance_km"], "google_route": route,
            "google_locality": maps.reverse_geocode(round(v["lat"], 4), round(v["lon"], 4)),
            "mode": "real" if route else "demo"}


@router.get("/geocode")
def geocode(q: str = Query(min_length=3, max_length=200)) -> dict:
    from app import integrations

    if not integrations.maps_enabled():
        return {"query": q, "mode": "demo", "found": False, "note": "MAPS_API_KEY not configured"}
    try:
        res = maps.geocode(q)
        integrations.clear_error("maps_routes")
        return {"mode": "real", **res}
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("maps_routes", exc)
        raise HTTPException(502, "geocoding failed") from None


@router.post("/scenarios/{scenario_id}/sitrep")
def create_sitrep(scenario_id: str, body: SitrepIn | None = None) -> dict:
    body = body or SitrepIn()
    return sitrep.generate(result_or_404(scenario_id), body.requested_by, body.role)


@router.get("/scenarios/{scenario_id}/sitrep")
def latest_sitrep(scenario_id: str) -> dict:
    result_or_404(scenario_id)
    rec = sitrep.latest(scenario_id)
    if rec is None:
        raise HTTPException(404, "no situation report yet")
    return rec


@router.get("/scenarios/{scenario_id}/validation")
def validation(scenario_id: str) -> dict:
    r = result_or_404(scenario_id)
    rows = [v for v in r["validation"]["villages"] if v["observed_flooded"] is not None]
    tp = sum(1 for v in rows if v["predicted_flooded"] and v["observed_flooded"])
    fp = sum(1 for v in rows if v["predicted_flooded"] and not v["observed_flooded"])
    fn = sum(1 for v in rows if not v["predicted_flooded"] and v["observed_flooded"])
    tn = len(rows) - tp - fp - fn
    return {**r["validation"], "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "hit_rate": round(tp / (tp + fn), 2) if tp + fn else None,
            "false_alarm_ratio": round(fp / (tp + fp), 2) if tp + fp else None}
