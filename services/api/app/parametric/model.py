"""Parametric trigger estimation (PRD §17) — SAMPLE policies; planning estimates, not payout decisions.

Trigger probability = share of track-set members whose modelled max sustained wind at the zone
centre reaches the trigger threshold. Expected payout = probability × payout; high-end = payout if
the trigger is met in the high case. Post-event verification uses the replay's reconstructed track.
"""
from datetime import datetime, timedelta

from app.forecast_ingest import track as trk
from app.geo import km

LABEL = "Planning estimate for liquidity preparation – not a payout decision. Sample policies."

POLICIES = [
    {"policy_id": "PP-OD-ZA", "state": "OD", "zone": "Zone A – Puri coastal fisher households (sample)",
     "lat": 19.81, "lon": 85.84, "radius_km": 50, "trigger_wind_kmh": 120, "payout_crore": 25.0},
    {"policy_id": "PP-OD-ZB", "state": "OD", "zone": "Zone B – Gop–Kakatpur farm households (sample)",
     "lat": 19.99, "lon": 86.12, "radius_km": 50, "trigger_wind_kmh": 150, "payout_crore": 18.0},
    {"policy_id": "PP-WB-ZA", "state": "WB", "zone": "Zone A – Sundarbans island households (sample)",
     "lat": 21.75, "lon": 88.35, "radius_km": 50, "trigger_wind_kmh": 120, "payout_crore": 30.0},
]


def max_wind_near(pts: list[trk.TrackPt], lat: float, lon: float, radius_km: float, rmw_km: float) -> float:
    best = 0.0
    for p in trk.interpolate(pts, 1.0):
        d = km(p.lat, p.lon, lat, lon)
        best = max(best, trk.wind_at(p.vmax, max(0.0, d - radius_km), rmw_km))
    return best


def estimate(result: dict, rmw_km: float) -> list[dict]:
    sc = result["scenario"]
    pts = trk.from_parse(result["track"]["points"], sc["forecast_issued_at"])
    out = []
    for pol in [p for p in POLICIES if p["state"] == sc["state"]]:
        winds = [max_wind_near(m, pol["lat"], pol["lon"], pol["radius_km"], rmw_km) for _, m in trk.track_set(pts)]
        prob = sum(1 for w in winds if w >= pol["trigger_wind_kmh"]) / len(winds)
        out.append({**pol, "trigger_definition": f"Max sustained wind ≥ {pol['trigger_wind_kmh']} km/h within "
                                                 f"{pol['radius_km']} km", "trigger_probability": round(prob, 2),
                    "expected_payout_crore": round(prob * pol["payout_crore"], 1),
                    "high_payout_crore": pol["payout_crore"] if max(winds) >= pol["trigger_wind_kmh"] else 0.0,
                    "member_max_winds_kmh": [round(w) for w in winds], "label": LABEL, "is_sample": True})
    return out


def verify(policy: dict, truth_track: list[dict], landfall_time: str, rmw_km: float) -> dict:
    lf = datetime.fromisoformat(landfall_time)
    pts = [trk.TrackPt(lf + timedelta(hours=p["hours_from_landfall"]), p["lat"],
                       p["lon"], p["max_wind_kmh"], p["central_pressure_hpa"], 0) for p in truth_track]
    w = max_wind_near(pts, policy["lat"], policy["lon"], policy["radius_km"], rmw_km)
    return {"policy_id": policy["policy_id"], "observed_max_wind_kmh": round(w), "trigger_met": w >= policy["trigger_wind_kmh"],
            "source": "Replay reconstructed track (sample) – real verification uses IMD best track / observations",
            "label": LABEL}
