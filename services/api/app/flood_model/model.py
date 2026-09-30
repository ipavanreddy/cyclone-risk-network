"""Rainfall flood likelihood (PRD §12) — transparent demo model.

Rainfall (72 h from bulletin issue): parametric rain field around the forecast track,
    rate = R0 × min(1.3, Vmax/150) × (1 inside Rmw, else exp(−(r − Rmw)/120 km))  [mm/h]
  or, in Earth Engine mode, GPM IMERG observed accumulation for the replay window.

Likelihood: logistic model
    z = −5.5 + 0.02·rain_mm + 2.2·lowness + 1.6·drainage + 2.0·antecedent
    lowness  = clamp((6 m − elevation)/6 m)            (low-lying land)
    drainage = exp(−distance_to_channel / 1.5 km)      (proximity to rivers / flow accumulation proxy)
    p = 1 / (1 + e^−z)

The PRD target is a Vertex AI gradient-boosted model trained on Sentinel-1 flood extents; it plugs in
behind `likelihood()` with the same inputs. Until then this heuristic is labelled as a demo model.
"""
import math
from datetime import datetime, timedelta

from app.forecast_ingest.track import TrackPt, interpolate
from app.geo import KM_PER_DEG, clamp, km

MODEL_NAME = "tatraksha-flood-likelihood-heuristic"
MODEL_VERSION = "0.1.0-demo"
LABEL = "Demo heuristic flood-likelihood model (Vertex AI model not yet trained)"


def rainfall_72h(pts: list[TrackPt], grid, issued_at: datetime, rmw_km: float, r0_mm_h: float) -> list[float]:
    hourly = [p for p in interpolate(pts, 1.0) if issued_at <= p.time <= issued_at + timedelta(hours=72)]
    bb = grid.bbox
    clat, clon = (bb["lat_min"] + bb["lat_max"]) / 2, (bb["lon_min"] + bb["lon_max"]) / 2
    hourly = [p for p in hourly if km(p.lat, p.lon, clat, clon) < 700]
    n = grid.rows * grid.cols
    rain = [0.0] * n
    for p in hourly:
        coslat = math.cos(math.radians(p.lat))
        scale = r0_mm_h * min(1.3, p.vmax / 150.0)
        for r in range(grid.rows):
            dy = (grid.lat(r) - p.lat) * KM_PER_DEG
            for c in range(grid.cols):
                d = math.hypot(dy, (grid.lon(c) - p.lon) * KM_PER_DEG * coslat)
                rain[r * grid.cols + c] += scale * (1.0 if d < rmw_km else math.exp(-(d - rmw_km) / 120.0))
    return [round(v, 1) for v in rain]


def likelihood(rain_mm: float, elevation_m: float, dist_channel_km: float, antecedent: float) -> float:
    lowness = clamp((6.0 - elevation_m) / 6.0)
    drainage = math.exp(-dist_channel_km / 1.5)
    z = -5.5 + 0.02 * rain_mm + 2.2 * lowness + 1.6 * drainage + 2.0 * antecedent
    return 1.0 / (1.0 + math.exp(-z))


def band(p: float) -> str:
    return "high" if p >= 0.65 else "medium" if p >= 0.35 else "low"


def run(base, rain: list[float], antecedent: float, rain_source: str) -> dict:
    n = len(rain)
    prob = [0.0] * n
    for i in range(n):
        if not base.water[i]:
            prob[i] = round(likelihood(rain[i], base.elevation_m[i], base.dist_channel_km[i], antecedent), 3)
    land = [i for i in range(n) if not base.water[i]]
    return {
        "label": LABEL,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "rain_source": rain_source,
        "rain_72h_mm": rain,
        "flood_likelihood": prob,
        "max_rain_72h_mm": max(rain[i] for i in land) if land else 0,
        "share_high": round(sum(1 for i in land if prob[i] >= 0.65) / max(1, len(land)), 3),
        "assumptions": [
            "Parametric rain field around the forecast track (R0 scaled by intensity, 120 km e-folding).",
            "Logistic likelihood from rainfall, low-lying terrain, drainage proximity and antecedent wetness.",
            "Bands: high ≥ 0.65, medium ≥ 0.35.",
        ],
    }
