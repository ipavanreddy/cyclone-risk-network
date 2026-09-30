"""Screening-level storm surge model (PRD §11). "Screening estimate – defer to official surge guidance."

Transparent formula (same as geospatial/earth-engine/tatraksha_ee/surge.py):

  peak surge S = 0.01 m/hPa × Δp  +  C_w × V² × shelf_factor
      Δp  = 1010 − central pressure at landfall (hPa)       (inverse barometer, ~1 cm per hPa)
      V   = max sustained wind at landfall (m/s)            (wind set-up, scales with V²)
      C_w = 4.2e-4 s²/m                                     (calibrated so Fani 2019 ≈ 1.6 m at Puri and
                                                             Amphan 2020 ≈ 3–4 m in the Sundarbans, matching
                                                             the order of IMD's official guidance)
      shelf_factor: 1.0 steep Odisha shelf, 3.4 very shallow head-Bay shelf (sample calibration)

  along-coast profile g(s): peak at Rmw to the right of the track, decaying over 2.5·Rmw;
      left side 0.45·exp(−(s/1.5·Rmw)²)
  coastal water level  W(s) = tide + S·g(s)
  inland level        W_in = W(s) − decay × distance inland  ("reduced with distance inland")
  inundation: bathtub — cell floods if elevation < W_in AND it is 8-connected to the sea
              (directly or through rivers/lagoons carrying the surge).
  expected: central track, expected tide.  high: max over central half of the track set with
            +10 % intensity and high tide.
"""
import math
from collections import deque
from dataclasses import dataclass

from app.forecast_ingest.track import TrackPt, landfall, track_set
from app.geo import to_xy

C_WIND = 4.2e-4
AMBIENT_HPA = 1010.0
MIN_RIVER_LEVEL_M = 0.2
MODEL_NAME = "tatraksha-screening-surge"
MODEL_VERSION = "1.0.0"
SCREENING_LABEL = "Screening estimate – defer to official surge guidance"


@dataclass
class SurgeParams:
    rmw_km: float
    shelf_factor: float
    tide_expected_m: float
    tide_high_m: float
    inland_decay_m_per_km: float


def peak_surge_m(pc_hpa: float | None, vmax_kmh: float, shelf_factor: float) -> float:
    dp = max(0.0, AMBIENT_HPA - (pc_hpa if pc_hpa is not None else AMBIENT_HPA - vmax_kmh / 3.0))
    v = vmax_kmh / 3.6
    return 0.01 * dp + C_WIND * v * v * shelf_factor


def profile(s_km: float, rmw_km: float) -> float:
    right = math.exp(-(((s_km - rmw_km) / (2.5 * rmw_km)) ** 2)) if s_km >= 0 else 0.0
    left = 0.45 * math.exp(-((s_km / (1.5 * rmw_km)) ** 2))
    return max(right, left)


def coast_unit(coast: dict, lat: float, heading: tuple[float, float]) -> tuple[float, float]:
    """Unit vector along the coast (km space) pointing to the right of the storm's motion."""
    ex, ey = math.cos(math.radians(lat)), coast["b"]
    n = math.hypot(ex, ey)
    ex, ey = ex / n, ey / n
    rx, ry = heading[1], -heading[0]
    return (ex, ey) if ex * rx + ey * ry >= 0 else (-ex, -ey)


def inundation(base, lf: dict, peak_m: float, tide_m: float, p: SurgeParams) -> tuple[list[float], list[float]]:
    """Returns (depth per cell on land [m], water level at coast per cell [m])."""
    g = base.grid
    e = coast_unit(base.coast, lf["lat"], lf["heading"])
    n = g.rows * g.cols
    level = [0.0] * n
    for r in range(g.rows):
        la = g.lat(r)
        for c in range(g.cols):
            x, y = to_xy(la, g.lon(c), lf["lat"], lf["lon"])
            s = x * e[0] + y * e[1]
            i = r * g.cols + c
            level[i] = tide_m + peak_m * profile(s, p.rmw_km)
    depth = [0.0] * n
    seen = bytearray(n)
    q = deque(i for i in range(n) if base.sea[i])
    for i in q:
        seen[i] = 1
    while q:
        i = q.popleft()
        r, c = divmod(i, g.cols)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (dr or dc) and 0 <= rr < g.rows and 0 <= cc < g.cols:
                    j = rr * g.cols + cc
                    if seen[j]:
                        continue
                    w_in = level[j] - p.inland_decay_m_per_km * base.dist_inland_km[j]
                    if base.water[j]:
                        if w_in > MIN_RIVER_LEVEL_M:
                            seen[j] = 1
                            q.append(j)
                    elif base.elevation_m[j] < w_in:
                        seen[j] = 1
                        depth[j] = round(w_in - base.elevation_m[j], 2)
                        q.append(j)
    return depth, level


def run(base, pts: list[TrackPt], p: SurgeParams) -> dict:
    lf = landfall(pts, base.coast)
    peak = peak_surge_m(lf["pc"], lf["vmax"], p.shelf_factor)
    expected, level = inundation(base, lf, peak, p.tide_expected_m, p)
    high = [0.0] * len(expected)
    member_peaks = []
    for k, member in track_set(pts):
        if abs(k) > 0.5:
            continue
        mlf = landfall(member, base.coast)
        mpeak = peak_surge_m(None if mlf["pc"] is None else AMBIENT_HPA - 1.1 * (AMBIENT_HPA - mlf["pc"]),
                             mlf["vmax"] * 1.05, p.shelf_factor)
        member_peaks.append({"k": k, "landfall_lat": round(mlf["lat"], 3), "landfall_lon": round(mlf["lon"], 3),
                             "peak_surge_m": round(mpeak, 2)})
        d, _ = inundation(base, mlf, mpeak, p.tide_high_m, p)
        high = [max(a, b) for a, b in zip(high, d)]
    # coastal segments every ~10 km along the coastline for the table
    g = base.grid
    segments = []
    e = coast_unit(base.coast, lf["lat"], lf["heading"])
    for c in range(0, g.cols, 6):
        lon = g.lon(c)
        lat = base.coast["a"] + base.coast["b"] * (lon - base.coast["lon0"])
        if not (g.bbox["lat_min"] <= lat <= g.bbox["lat_max"]):
            continue
        x, y = to_xy(lat, lon, lf["lat"], lf["lon"])
        s = x * e[0] + y * e[1]
        surge = peak * profile(s, p.rmw_km)
        high_surge = max(m["peak_surge_m"] for m in member_peaks) * profile(s, p.rmw_km) if member_peaks else surge
        segments.append({"segment_id": f"CS-{c:03d}", "lat": round(lat, 4), "lon": round(lon, 4),
                         "along_coast_km": round(s, 1), "surge_expected_m": round(surge, 2),
                         "surge_high_m": round(max(high_surge, surge), 2),
                         "water_level_expected_m": round(surge + p.tide_expected_m, 2)})
    cell_km2 = (g.cell_deg * 111.2) ** 2 * math.cos(math.radians(lf["lat"]))
    return {
        "label": SCREENING_LABEL,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "landfall": {k: v for k, v in lf.items() if k != "heading"},
        "peak_surge_expected_m": round(peak, 2),
        "peak_surge_high_m": round(max([m["peak_surge_m"] for m in member_peaks] + [peak]), 2),
        "tide_m": {"expected": p.tide_expected_m, "high": p.tide_high_m},
        "track_set_members": member_peaks,
        "segments": segments,
        "inundated_km2_expected": round(sum(1 for d in expected if d > 0) * cell_km2, 1),
        "inundated_km2_high": round(sum(1 for d in high if d > 0) * cell_km2, 1),
        "depth_expected": expected,
        "depth_high": high,
        "assumptions": [
            "Peak surge = 1 cm/hPa × pressure deficit + 4.2e-4 × V² × shelf factor (sample calibration).",
            f"Shelf factor {p.shelf_factor}; radius of maximum winds {p.rmw_km} km; tide expected "
            f"{p.tide_expected_m} m / high {p.tide_high_m} m (sample values).",
            f"Water level decays {p.inland_decay_m_per_km} m per km inland; bathtub fill connected to the sea.",
            "High case: central half of the track set, +10 % pressure deficit, +5 % wind, high tide.",
        ],
    }
