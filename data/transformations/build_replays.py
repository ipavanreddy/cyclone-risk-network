"""Build the committed, deterministic replay datasets in data/replays/.

Run:  cd services/api && uv run python ../../data/transformations/build_replays.py

Stdlib only. Everything written here is SAMPLE data, labelled as such:
- Cyclone tracks are approximate reconstructions from publicly reported IMD facts (landfall place/time,
  intensity, official surge guidance). They are NOT the official IMD best track.
- Bulletins are reconstructed in IMD style for training/replay; NOT official IMD products.
- Terrain is a synthetic surrogate (coast-distance ramp + river channels + deterministic noise).
  Real mode replaces it with Earth Engine DEM / JRC water sampled onto the same grid
  (see geospatial/earth-engine/).
- Village names are real places; coordinates are approximate; population and vulnerability are synthetic.
- Shelters, substations and hospitals are sample points placed near real towns.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "replays"
IST = timezone(timedelta(hours=5, minutes=30))
DATASET_VERSION = "replay-sample-v1"
GENERATED_REF = "2026-09-30T00:00:00+05:30"
KM_PER_DEG = 111.2


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = (lat2 - lat1) * KM_PER_DEG
    dlon = (lon2 - lon1) * KM_PER_DEG * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dlat, dlon)


def noise(i: int, j: int, seed: float) -> float:
    """Deterministic pseudo-noise in [0, 1)."""
    v = math.sin(i * 12.9898 + j * 78.233 + seed) * 43758.5453
    return v - math.floor(v)


def seg_dist_km(lat: float, lon: float, a: tuple[float, float], b: tuple[float, float]) -> float:
    coslat = math.cos(math.radians(lat))
    ax, ay = (a[1] - lon) * coslat * KM_PER_DEG, (a[0] - lat) * KM_PER_DEG
    bx, by = (b[1] - lon) * coslat * KM_PER_DEG, (b[0] - lat) * KM_PER_DEG
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def polyline_dist_km(lat: float, lon: float, line: list[tuple[float, float]]) -> float:
    return min(seg_dist_km(lat, lon, line[k], line[k + 1]) for k in range(len(line) - 1))


def category(v: float) -> str:
    for threshold, name in [(222, "SuCS"), (166, "ESCS"), (118, "VSCS"), (89, "SCS"), (62, "CS"), (50, "DD")]:
        if v >= threshold:
            return name
    return "D"


CATEGORY_NAMES = {
    "SuCS": "Super Cyclonic Storm",
    "ESCS": "Extremely Severe Cyclonic Storm",
    "VSCS": "Very Severe Cyclonic Storm",
    "SCS": "Severe Cyclonic Storm",
    "CS": "Cyclonic Storm",
    "DD": "Deep Depression",
    "D": "Depression",
}

# ---------------------------------------------------------------------------------------------
# Replay configurations
# ---------------------------------------------------------------------------------------------
FANI = {
    "replay_id": "fani-2019",
    "code": "FANI-2019",
    "cyclone_name": "Fani",
    "state": "OD",
    "state_name": "Odisha",
    "district": "Puri",
    "landfall_time": "2019-05-03T08:30:00+05:30",
    "landfall_area": "near Puri, Odisha",
    "bulletin_region": "Odisha coast",
    "bay_region": "west-central Bay of Bengal",
    "official_surge_m": "about 1.5 m above astronomical tide",
    "surge_districts": "Puri, Khurda, Ganjam and Jagatsinghpur districts",
    "steps": [72, 48, 24, 6],
    # (hours relative to landfall, lat, lon, max sustained wind km/h, central pressure hPa)
    "truth": [
        (-84, 12.9, 85.5, 165, 962),
        (-72, 13.6, 85.3, 180, 956),
        (-60, 14.3, 85.0, 185, 950),
        (-48, 15.2, 84.8, 195, 944),
        (-36, 16.2, 84.8, 205, 937),
        (-24, 17.3, 84.9, 205, 934),
        (-12, 18.5, 85.2, 195, 937),
        (-6, 19.1, 85.5, 185, 940),
        (0, 19.80, 85.83, 175, 944),
        (6, 20.6, 86.1, 140, 962),
        (12, 21.5, 86.7, 110, 975),
        (24, 22.9, 87.8, 75, 990),
    ],
    # Forecast bias per hour of lead time (deg lat, deg lon): early bulletins placed landfall
    # slightly south-west along the coast (sample error, deterministic).
    "bias_per_h": (-0.0020, -0.0030),
    "landfall_time_bias_h_per_h": 0.06,
    "rmw_km": 25,
    "shelf_factor": 1.0,
    "tide_m": {"expected": 0.6, "high": 1.0},
    "surge_inland_decay_m_per_km": 0.25,
    "rain_r0_mm_h": 12.0,
    "antecedent_wetness": 0.1,
    "bbox": {"lat_min": 19.55, "lat_max": 20.25, "lon_min": 85.30, "lon_max": 86.40},
    "cell_deg": 0.0125,
    # coast: lat = a + b * (lon - lon0); sea on the south side
    "coast": {"a": 19.795, "b": 0.29, "lon0": 85.83},
    "terrain": {"base_m": 1.5, "k": 1.1, "p": 0.75, "noise_m": 0.8, "embankment_m": 0.0},
    "channels": [
        {"name": "Kushabhadra", "width_km": 0.8, "line": [(19.83, 86.00), (19.95, 85.98), (20.10, 85.90), (20.25, 85.86)]},
        {"name": "Devi", "width_km": 1.0, "line": [(19.92, 86.33), (20.05, 86.25), (20.25, 86.12)]},
        {"name": "Bhargavi", "width_km": 0.6, "line": [(19.78, 85.55), (19.90, 85.70), (20.10, 85.78), (20.25, 85.80)]},
        {"name": "Chilika outlet", "width_km": 1.4, "line": [(19.66, 85.42), (19.69, 85.48)]},
    ],
    "lagoons": [{"name": "Chilika", "lat": 19.74, "lon": 85.33, "rlat": 0.14, "rlon": 0.09}],
    "hub": {"id": "HUB-PURI-PIPILI", "name": "District relief depot, Pipili (sample)", "lat": 20.113, "lon": 85.831},
    # (name, lat, lon, block, population, vulnerability, coastal_fishing)
    "villages": [
        ("Puri coastal wards", 19.806, 85.826, "Puri Sadar", 42000, 0.55, True),
        ("Penthakata", 19.802, 85.843, "Puri Sadar", 9800, 0.82, True),
        ("Baliapanda", 19.795, 85.805, "Puri Sadar", 7600, 0.62, True),
        ("Chakratirtha", 19.812, 85.858, "Puri Sadar", 5200, 0.58, True),
        ("Sipasurubili", 19.826, 85.872, "Puri Sadar", 4100, 0.66, True),
        ("Talabania", 19.834, 85.890, "Puri Sadar", 3500, 0.61, False),
        ("Balighai", 19.844, 85.912, "Puri Sadar", 2900, 0.70, True),
        ("Beleswar", 19.852, 85.943, "Gop", 3300, 0.68, True),
        ("Ramachandi", 19.862, 86.002, "Gop", 2400, 0.72, True),
        ("Chandrabhaga", 19.880, 86.110, "Gop", 3100, 0.74, True),
        ("Konark", 19.887, 86.094, "Gop", 16800, 0.48, False),
        ("Gop", 19.996, 86.035, "Gop", 14500, 0.45, False),
        ("Kuanrpur", 19.935, 86.150, "Kakatpur", 3800, 0.63, False),
        ("Kakatpur", 20.000, 86.190, "Kakatpur", 11200, 0.52, False),
        ("Astaranga", 19.990, 86.270, "Astaranga", 8900, 0.71, True),
        ("Nuagarh", 19.955, 86.235, "Astaranga", 4200, 0.69, True),
        ("Chandanpur", 19.930, 85.842, "Puri Sadar", 6400, 0.50, False),
        ("Sakhigopal", 19.972, 85.822, "Satyabadi", 12400, 0.44, False),
        ("Nimapara", 20.058, 86.000, "Nimapara", 19800, 0.40, False),
        ("Pipili", 20.113, 85.831, "Pipili", 21500, 0.38, False),
        ("Delang", 20.060, 85.720, "Delang", 9100, 0.47, False),
        ("Kanas", 20.020, 85.600, "Kanas", 7300, 0.53, False),
        ("Brahmagiri", 19.795, 85.680, "Brahmagiri", 13600, 0.51, False),
        ("Baliharachandi", 19.742, 85.605, "Brahmagiri", 3000, 0.73, True),
        ("Satapada", 19.700, 85.442, "Krushnaprasad", 6100, 0.76, True),
        ("Arakhakuda", 19.712, 85.470, "Krushnaprasad", 2800, 0.80, True),
        ("Alanda", 19.760, 85.520, "Brahmagiri", 3400, 0.67, False),
        ("Balukhand", 19.848, 85.965, "Gop", 2100, 0.64, False),
        ("Nuanai", 19.905, 85.905, "Puri Sadar", 5600, 0.57, False),
        ("Samang", 19.960, 85.950, "Gop", 4800, 0.55, False),
    ],
    "highways": [
        ("NH-316", ["Pipili", "Sakhigopal", "Chandanpur", "Puri coastal wards"]),
        ("Marine Drive (Puri–Konark)", ["Puri coastal wards", "Chakratirtha", "Sipasurubili", "Talabania", "Balighai",
                                         "Beleswar", "Balukhand", "Ramachandi", "Konark", "Chandrabhaga"]),
        ("Konark–Astaranga road", ["Konark", "Kuanrpur", "Nuagarh", "Astaranga"]),
        ("Konark–Pipili road", ["Konark", "Samang", "Gop", "Nimapara", "Pipili"]),
        ("Nimapara–Kakatpur road", ["Nimapara", "Kakatpur", "Astaranga"]),
        ("Puri–Satapada road", ["Puri coastal wards", "Baliapanda", "Brahmagiri", "Alanda", "Baliharachandi", "Satapada",
                                 "Arakhakuda"]),
        ("Brahmagiri–Delang road", ["Brahmagiri", "Kanas", "Delang", "Pipili"]),
        ("Chandanpur–Gop road", ["Chandanpur", "Nuanai", "Samang"]),
        ("Penthakata lane", ["Puri coastal wards", "Penthakata", "Chakratirtha"]),
    ],
    "shelters_near": ["Penthakata", "Baliapanda", "Sipasurubili", "Balighai", "Beleswar", "Ramachandi", "Konark",
                      "Chandrabhaga", "Kuanrpur", "Astaranga", "Kakatpur", "Gop", "Chandanpur", "Brahmagiri",
                      "Baliharachandi", "Satapada", "Nuanai", "Sakhigopal", "Nimapara", "Samang"],
    "substations": [("Puri 132/33 kV", "Puri coastal wards"), ("Konark 33/11 kV", "Konark"), ("Gop 33/11 kV", "Gop"),
                    ("Nimapara 132/33 kV", "Nimapara"), ("Pipili 220/132 kV", "Pipili"),
                    ("Brahmagiri 33/11 kV", "Brahmagiri"), ("Kakatpur 33/11 kV", "Kakatpur"),
                    ("Satapada 33/11 kV", "Satapada"), ("Astaranga 33/11 kV", "Astaranga"),
                    ("Sakhigopal 33/11 kV", "Sakhigopal")],
    "hospitals": [("District Headquarters Hospital, Puri", "Puri coastal wards"), ("CHC Gop", "Gop"),
                  ("CHC Nimapara", "Nimapara"), ("CHC Brahmagiri", "Brahmagiri"), ("CHC Kakatpur", "Kakatpur"),
                  ("CHC Astaranga", "Astaranga"), ("CHC Sakhigopal", "Sakhigopal"), ("CHC Pipili", "Pipili"),
                  ("PHC Satapada", "Satapada")],
    "observed_flood_note": "Sample 'observed' flood points for replay validation; real mode uses Sentinel-1 SAR "
                           "change detection in Earth Engine.",
}

AMPHAN = {
    "replay_id": "amphan-2020",
    "code": "AMPHAN-2020",
    "cyclone_name": "Amphan",
    "state": "WB",
    "state_name": "West Bengal",
    "district": "South 24 Parganas",
    "landfall_time": "2020-05-20T17:30:00+05:30",
    "landfall_area": "across the Sundarbans, between Digha (West Bengal) and Hatiya (Bangladesh)",
    "bulletin_region": "West Bengal – Bangladesh coasts",
    "bay_region": "central Bay of Bengal",
    "official_surge_m": "about 4-5 m above astronomical tide",
    "surge_districts": "South and North 24 Parganas districts",
    "steps": [72, 48, 24, 6],
    "truth": [
        (-84, 12.2, 86.4, 120, 976),
        (-72, 12.9, 86.3, 150, 968),
        (-60, 13.8, 86.3, 240, 925),
        (-48, 15.2, 86.5, 230, 930),
        (-36, 16.6, 86.8, 220, 940),
        (-24, 18.2, 87.2, 200, 950),
        (-12, 20.0, 87.7, 180, 960),
        (-6, 20.9, 88.0, 170, 965),
        (0, 21.62, 88.30, 160, 968),
        (6, 22.6, 88.5, 120, 980),
        (12, 23.6, 89.0, 80, 990),
        (24, 25.0, 89.6, 50, 996),
    ],
    "bias_per_h": (-0.0010, 0.0035),
    "landfall_time_bias_h_per_h": -0.04,
    "rmw_km": 30,
    "shelf_factor": 3.4,
    "tide_m": {"expected": 1.0, "high": 1.4},
    "surge_inland_decay_m_per_km": 0.08,
    "rain_r0_mm_h": 14.0,
    "antecedent_wetness": 0.3,
    "bbox": {"lat_min": 21.50, "lat_max": 22.45, "lon_min": 87.95, "lon_max": 89.00},
    "cell_deg": 0.0125,
    "coast": {"a": 21.56, "b": 0.0, "lon0": 88.3},
    "terrain": {"base_m": 0.8, "k": 0.18, "p": 0.85, "noise_m": 0.5, "embankment_m": 2.2},
    "channels": [
        {"name": "Hooghly", "width_km": 3.0, "line": [(21.50, 88.02), (21.85, 88.05), (22.05, 88.10), (22.19, 88.16), (22.30, 88.10), (22.45, 88.12)]},
        {"name": "Muriganga", "width_km": 1.6, "line": [(21.50, 88.15), (21.85, 88.15), (21.97, 88.14)]},
        {"name": "Saptamukhi", "width_km": 1.4, "line": [(21.50, 88.30), (21.90, 88.33), (22.05, 88.35)]},
        {"name": "Thakuran", "width_km": 1.4, "line": [(21.50, 88.45), (21.90, 88.47), (22.05, 88.50)]},
        {"name": "Matla", "width_km": 1.8, "line": [(21.50, 88.62), (21.95, 88.63), (22.31, 88.68), (22.40, 88.66)]},
        {"name": "Bidya–Gosaba", "width_km": 1.4, "line": [(21.50, 88.82), (22.00, 88.80), (22.20, 88.78)]},
        {"name": "Raimangal", "width_km": 1.6, "line": [(21.50, 88.96), (22.20, 88.95)]},
    ],
    "lagoons": [],
    "hub": {"id": "HUB-S24P-BARUIPUR", "name": "District relief depot, Baruipur (sample)", "lat": 22.360, "lon": 88.430},
    "villages": [
        ("Gangasagar", 21.650, 88.080, "Sagar", 9800, 0.78, True),
        ("Rudranagar", 21.750, 88.100, "Sagar", 7200, 0.74, False),
        ("Ghoramara", 21.910, 88.125, "Sagar", 3100, 0.88, True),
        ("Kakdwip", 21.870, 88.190, "Kakdwip", 22400, 0.52, False),
        ("Namkhana", 21.770, 88.230, "Namkhana", 11800, 0.66, True),
        ("Frasergunj", 21.600, 88.245, "Namkhana", 4200, 0.83, True),
        ("Bakkhali", 21.575, 88.265, "Namkhana", 3600, 0.80, True),
        ("Mousuni", 21.660, 88.200, "Namkhana", 5300, 0.86, True),
        ("Patharpratima", 21.790, 88.360, "Patharpratima", 14200, 0.72, False),
        ("G-Plot", 21.620, 88.390, "Patharpratima", 4800, 0.87, True),
        ("Raidighi", 21.970, 88.430, "Mathurapur II", 12600, 0.63, False),
        ("Kultali", 22.050, 88.560, "Kultali", 10400, 0.75, False),
        ("Mathurapur", 22.120, 88.370, "Mathurapur I", 15900, 0.54, False),
        ("Diamond Harbour", 22.190, 88.190, "Diamond Harbour I", 24800, 0.42, False),
        ("Kulpi", 22.080, 88.240, "Kulpi", 13300, 0.58, False),
        ("Jaynagar", 22.170, 88.420, "Jaynagar I", 18700, 0.49, False),
        ("Canning", 22.310, 88.670, "Canning I", 26400, 0.51, False),
        ("Basanti", 22.190, 88.670, "Basanti", 14600, 0.70, False),
        ("Gosaba", 22.160, 88.800, "Gosaba", 12100, 0.79, True),
        ("Satjelia", 22.100, 88.870, "Gosaba", 6900, 0.85, True),
        ("Pakhiralaya", 22.120, 88.830, "Gosaba", 5400, 0.84, True),
        ("Jharkhali", 22.020, 88.690, "Basanti", 7800, 0.77, True),
        ("Maipith", 21.940, 88.590, "Kultali", 5100, 0.81, True),
        ("Baruipur", 22.360, 88.430, "Baruipur", 30500, 0.36, False),
    ],
    "highways": [
        ("Diamond Harbour Road (NH-12)", ["Baruipur", "Jaynagar", "Mathurapur", "Diamond Harbour", "Kulpi", "Kakdwip", "Namkhana", "Frasergunj", "Bakkhali"]),
        ("Mathurapur–Raidighi road", ["Mathurapur", "Raidighi", "Patharpratima", "G-Plot"]),
        ("Sagar island road", ["Kakdwip", "Rudranagar", "Gangasagar"]),
        ("Baruipur–Canning road", ["Baruipur", "Canning", "Basanti", "Gosaba", "Pakhiralaya", "Satjelia"]),
        ("Jaynagar–Kultali road", ["Jaynagar", "Kultali", "Maipith"]),
        ("Canning–Jharkhali road", ["Canning", "Jharkhali"]),
        ("Namkhana–Mousuni ferry road", ["Namkhana", "Mousuni"]),
        ("Kakdwip–Ghoramara jetty", ["Kakdwip", "Ghoramara"]),
    ],
    "shelters_near": ["Gangasagar", "Rudranagar", "Kakdwip", "Namkhana", "Frasergunj", "Mousuni", "Patharpratima",
                      "G-Plot", "Raidighi", "Kultali", "Mathurapur", "Diamond Harbour", "Canning", "Basanti", "Gosaba",
                      "Pakhiralaya", "Jharkhali", "Maipith"],
    "substations": [("Kakdwip 132/33 kV", "Kakdwip"), ("Namkhana 33/11 kV", "Namkhana"),
                    ("Patharpratima 33/11 kV", "Patharpratima"), ("Diamond Harbour 132/33 kV", "Diamond Harbour"),
                    ("Canning 132/33 kV", "Canning"), ("Gosaba 33/11 kV", "Gosaba"), ("Baruipur 220/132 kV", "Baruipur"),
                    ("Raidighi 33/11 kV", "Raidighi"), ("Sagar 33/11 kV", "Rudranagar")],
    "hospitals": [("Diamond Harbour District Hospital", "Diamond Harbour"), ("Kakdwip Sub-divisional Hospital", "Kakdwip"),
                  ("Canning Sub-divisional Hospital", "Canning"), ("Sagar Rural Hospital", "Rudranagar"),
                  ("Patharpratima Rural Hospital", "Patharpratima"), ("Gosaba Rural Hospital", "Gosaba"),
                  ("Namkhana BPHC", "Namkhana"), ("Basanti Rural Hospital", "Basanti")],
    "observed_flood_note": "Sample 'observed' flood points for replay validation; real mode uses Sentinel-1 SAR "
                           "change detection in Earth Engine.",
}

# West Bengal adapter demo: the state file uses its own field names; data/adapters/west_bengal.json maps them.
WB_FIELD_MAP = {"village_code": "mouza_code", "name": "mouza_name", "block": "cd_block", "population": "pop_sample",
                "vulnerability_index": "svi_sample", "lat": "latitude", "lon": "longitude",
                "coastal_fishing": "fisher_hamlet"}

# ---------------------------------------------------------------------------------------------


def parse_t(s: str) -> datetime:
    return datetime.fromisoformat(s)


def coast_lat(cfg: dict, lon: float) -> float:
    c = cfg["coast"]
    return c["a"] + c["b"] * (lon - c["lon0"])


def dist_inland_km(cfg: dict, lat: float, lon: float) -> float:
    """Signed perpendicular distance to the straight coastline (positive = inland/north)."""
    b = cfg["coast"]["b"]
    dlat_km = (lat - coast_lat(cfg, lon)) * KM_PER_DEG
    return dlat_km / math.sqrt(1 + (b * KM_PER_DEG / (KM_PER_DEG * math.cos(math.radians(lat)))) ** 2)


def build_grid(cfg: dict) -> dict:
    bb, d = cfg["bbox"], cfg["cell_deg"]
    rows = round((bb["lat_max"] - bb["lat_min"]) / d)
    cols = round((bb["lon_max"] - bb["lon_min"]) / d)
    t = cfg["terrain"]
    elevation, water, sea, dinland, dchan = [], [], [], [], []
    for r in range(rows):  # row 0 = north
        lat = bb["lat_max"] - (r + 0.5) * d
        for c in range(cols):
            lon = bb["lon_min"] + (c + 0.5) * d
            di = dist_inland_km(cfg, lat, lon)
            dc = min(polyline_dist_km(lat, lon, ch["line"]) - ch["width_km"] / 2 for ch in cfg["channels"])
            in_lagoon = any(((lat - lg["lat"]) / lg["rlat"]) ** 2 + ((lon - lg["lon"]) / lg["rlon"]) ** 2 <= 1
                            for lg in cfg["lagoons"])
            is_sea = di <= 0
            is_water = is_sea or dc <= 0.35 or in_lagoon
            if is_sea:
                e = -2.0 - 0.3 * abs(di)
            elif is_water:
                e = -1.0
            else:
                e = t["base_m"] + t["k"] * di ** t["p"] + (noise(r, c, 1.7) - 0.5) * t["noise_m"]
                # river valleys are lower; embankments raise the immediate banks (WB)
                if dc < 3.0:
                    e -= (3.0 - dc) / 3.0 * min(2.5, 0.35 * e)
                    if t["embankment_m"] and dc < 1.4:
                        e += t["embankment_m"]
                e = max(e, 0.3)
            elevation.append(round(e, 2))
            water.append(1 if is_water else 0)
            sea.append(1 if is_sea else 0)
            dinland.append(round(max(di, 0.0), 2))
            dchan.append(round(max(dc, 0.0), 2))
    return {
        "metadata": meta(cfg, "Synthetic terrain surrogate (coast-distance ramp + river channels + noise). "
                              "Real mode: Copernicus GLO-30 DEM + JRC Global Surface Water via Earth Engine.",
                         is_synthetic=True),
        "grid": {"lat_max": bb["lat_max"], "lon_min": bb["lon_min"], "cell_deg": d, "rows": rows, "cols": cols},
        "coast": cfg["coast"],
        "elevation_m": elevation,
        "water": water,
        "sea": sea,
        "dist_inland_km": dinland,
        "dist_channel_km": dchan,
    }


def meta(cfg: dict, source: str, is_synthetic: bool = False) -> dict:
    return {
        "source": source,
        "reference_timestamp": GENERATED_REF,
        "dataset_version": DATASET_VERSION,
        "geographic_scope": f"{cfg['district']}, {cfg['state_name']} (replay bbox)",
        "is_sample": True,
        "is_synthetic": is_synthetic,
    }


def nudge_inland(cfg: dict, lat: float, lon: float, min_km: float = 0.8) -> float:
    while dist_inland_km(cfg, lat, lon) < min_km:
        lat += 0.002
    return round(lat, 4)


def build_places(cfg: dict) -> tuple[list[dict], dict[str, tuple[float, float]]]:
    code = cfg["code"].split("-")[0][:4]
    villages, pos = [], {}
    for k, (name, lat, lon, block, pop, vul, fishing) in enumerate(cfg["villages"], start=1):
        lat = nudge_inland(cfg, lat, lon)
        pos[name] = (lat, lon)
        villages.append({
            "village_code": f"SAMPLE-{cfg['state']}-{code}-{k:03d}",
            "name": name, "block": block, "district": cfg["district"], "state": cfg["state"],
            "population": pop, "vulnerability_index": vul, "coastal_fishing": fishing,
            "lat": lat, "lon": lon,
        })
    return villages, pos


def build_assets(cfg: dict, pos: dict) -> list[dict]:
    st = cfg["state"]
    assets = []
    for k, near in enumerate(cfg["shelters_near"], start=1):
        lat, lon = pos[near]
        # place shelter ~0.6-1.4 km further inland (deterministic)
        lat2 = nudge_inland(cfg, lat + 0.004 + 0.006 * noise(k, 3, 2.2), lon + 0.006 * (noise(k, 5, 1.1) - 0.5))
        assets.append({"asset_id": f"SH-{st}-{k:03d}", "type": "shelter",
                       "name": f"Multipurpose Cyclone Shelter, {near} (sample)",
                       "capacity": int(800 + 1200 * noise(k, 7, 0.4)) // 50 * 50, "criticality": "high",
                       "near": near, "lat": lat2, "lon": round(lon + 0.006 * (noise(k, 5, 1.1) - 0.5), 4)})
    for k, (name, near) in enumerate(cfg["substations"], start=1):
        lat, lon = pos[near]
        assets.append({"asset_id": f"SS-{st}-{k:03d}", "type": "substation", "name": f"{name} substation (sample)",
                       "capacity": None, "criticality": "high" if "132" in name or "220" in name else "medium",
                       "near": near, "lat": nudge_inland(cfg, lat - 0.003, lon + 0.004), "lon": round(lon + 0.004, 4)})
    for k, (name, near) in enumerate(cfg["hospitals"], start=1):
        lat, lon = pos[near]
        assets.append({"asset_id": f"HS-{st}-{k:03d}", "type": "hospital", "name": f"{name} (sample location)",
                       "capacity": 30 + int(170 * noise(k, 9, 0.8)), "criticality": "high", "near": near,
                       "lat": nudge_inland(cfg, lat + 0.002, lon - 0.003), "lon": round(lon - 0.003, 4)})
    return assets


def build_roads(cfg: dict, villages: list[dict], assets: list[dict], pos: dict) -> dict:
    nodes: dict[str, dict] = {}
    for v in villages:
        nodes[v["village_code"]] = {"id": v["village_code"], "kind": "village", "lat": v["lat"], "lon": v["lon"]}
    name_to_id = {v["name"]: v["village_code"] for v in villages}
    hub = cfg["hub"]
    nodes[hub["id"]] = {"id": hub["id"], "kind": "hub", "lat": hub["lat"], "lon": hub["lon"]}
    edges = []

    def add_edge(a: str, b: str, road: str, kind: str) -> None:
        na, nb = nodes[a], nodes[b]
        edges.append({"edge_id": f"E{len(edges) + 1:04d}", "from": a, "to": b, "road": road, "kind": kind,
                      "length_km": round(km(na["lat"], na["lon"], nb["lat"], nb["lon"]) * 1.2, 2)})

    for road, seq in cfg["highways"]:
        for a, b in zip(seq, seq[1:]):
            add_edge(name_to_id[a], name_to_id[b], road, "arterial")
    # hub connects to the nearest village
    nearest = min(villages, key=lambda v: km(v["lat"], v["lon"], hub["lat"], hub["lon"]))
    add_edge(hub["id"], nearest["village_code"], "Depot access road", "local")
    # every asset connects to the village it sits beside
    for a in assets:
        nodes[a["asset_id"]] = {"id": a["asset_id"], "kind": a["type"], "lat": a["lat"], "lon": a["lon"]}
        add_edge(name_to_id[a["near"]], a["asset_id"], f"Access road to {a['asset_id']}", "local")
    # ensure every village on at least one road
    linked = {e["from"] for e in edges} | {e["to"] for e in edges}
    for v in villages:
        if v["village_code"] not in linked:
            other = min((w for w in villages if w is not v and w["village_code"] in linked),
                        key=lambda w: km(v["lat"], v["lon"], w["lat"], w["lon"]))
            add_edge(v["village_code"], other["village_code"], f"Village road {v['name']}", "local")
    return {"metadata": meta(cfg, "Simplified sample road network between real place names (straight segments). "
                                  "Real mode: OpenStreetMap highways."),
            "nodes": list(nodes.values()), "edges": edges}


def truth_at(cfg: dict, h: float) -> tuple[float, float, float, float]:
    pts = cfg["truth"]
    for a, b in zip(pts, pts[1:]):
        if a[0] <= h <= b[0]:
            f = (h - a[0]) / (b[0] - a[0])
            return tuple(a[k] + f * (b[k] - a[k]) for k in range(1, 5))  # type: ignore[return-value]
    last = pts[-1]
    return last[1], last[2], last[3], last[4]


def forecast_track(cfg: dict, step: int) -> list[dict]:
    """Forecast rows of the bulletin issued at T-step (hours before actual landfall)."""
    lf = parse_t(cfg["landfall_time"])
    issue_h = -step
    rows = []
    for lead in [0, 6, 12, 18, 24, 36, 48, 60, 72, 84]:
        h = issue_h + lead
        if h > 18:
            break
        lat, lon, v, p = truth_at(cfg, h)
        blat, blon = cfg["bias_per_h"]
        lat += blat * lead
        lon += blon * lead
        v = v + (5 if lead >= 24 else 0) * (1 if step >= 48 else 0)  # early bulletins slightly over-forecast
        v = int(round(v / 5.0) * 5)
        rows.append({"time": (lf + timedelta(hours=h)).isoformat(), "lead_h": lead, "lat": round(lat, 1),
                     "lon": round(lon, 1), "max_wind_kmh": v, "central_pressure_hpa": int(round(p)),
                     "category": category(v)})
    return rows


def direction_word(dlat: float, dlon: float) -> str:
    ang = (math.degrees(math.atan2(dlon, dlat)) + 360) % 360
    names = ["north", "north-northeast", "northeast", "east-northeast", "east", "east-southeast", "southeast",
             "south-southeast", "south", "south-southwest", "southwest", "west-southwest", "west",
             "west-northwest", "northwest", "north-northwest"]
    return names[int((ang + 11.25) // 22.5) % 16]


def bulletin_text(cfg: dict, step: int, no: int, rows: list[dict]) -> tuple[str, str, str]:
    lf = parse_t(cfg["landfall_time"])
    issued = lf - timedelta(hours=step)
    fl_time = lf + timedelta(hours=round(cfg["landfall_time_bias_h_per_h"] * step))
    now = rows[0]
    nxt = rows[2] if len(rows) > 2 else rows[-1]
    motion = direction_word(nxt["lat"] - now["lat"], nxt["lon"] - now["lon"])
    cat = CATEGORY_NAMES[now["category"]]
    part_of_day = "forenoon" if fl_time.hour < 12 else ("afternoon" if fl_time.hour < 17 else "evening")
    landfall_str = f"{part_of_day} of {fl_time.strftime('%d %B %Y')}"
    peak = max(r["max_wind_kmh"] for r in rows if parse_t(r["time"]) <= fl_time + timedelta(hours=1))
    lf_row = min(rows, key=lambda r: abs((parse_t(r["time"]) - fl_time).total_seconds()))
    lf_v = lf_row["max_wind_kmh"]
    lines = [
        "INDIA METEOROLOGICAL DEPARTMENT – REPLAY SAMPLE",
        "*** Reconstructed for training/replay from publicly reported facts. NOT an official IMD product. ***",
        "TROPICAL CYCLONE ADVISORY BULLETIN",
        f"Bulletin No.: {cfg['code']}/{no:02d}",
        f"Issued at: {issued.strftime('%H%M')} IST, {issued.strftime('%d %B %Y')}",
        f"Sub: {cat} '{cfg['cyclone_name'].upper()}' over {cfg['bay_region']} – {cfg['bulletin_region']}",
        "",
        f"The {cat} '{cfg['cyclone_name'].upper()}' lay centred at {issued.strftime('%H%M')} hours IST of "
        f"{issued.strftime('%d %B %Y')} near latitude {now['lat']:.1f}°N and longitude {now['lon']:.1f}°E. "
        f"Estimated central pressure {now['central_pressure_hpa']} hPa. It is very likely to move {motion}wards, "
        f"intensify up to {peak} km/h and cross the {cfg['bulletin_region']} {cfg['landfall_area']} during the "
        f"{landfall_str} with maximum sustained wind speed of {lf_v - 10}-{lf_v} km/h gusting to {lf_v + 20} km/h.",
        "",
        "Forecast track and intensity:",
        "Date/Time (IST) | Position (Lat °N / Long °E) | Max sustained surface wind (km/h) | Central pressure (hPa) | Category",
    ]
    for r in rows:
        t = parse_t(r["time"])
        v = r["max_wind_kmh"]
        lines.append(f"{t.strftime('%d.%m.%y/%H%M')} | {r['lat']:.1f}/{r['lon']:.1f} | {v - 10}-{v} gusting to "
                     f"{v + 20} | {r['central_pressure_hpa']} | {r['category']}")
    lines += [
        "",
        f"Storm surge: Storm surge of {cfg['official_surge_m']} is likely to inundate low lying areas of "
        f"{cfg['surge_districts']} at the time of landfall.",
        "Sea condition: Phenomenal to very high. Fishermen are advised not to venture into the sea.",
        "Next bulletin: in 3 hours.",
    ]
    return "\n".join(lines), issued.isoformat(), fl_time.isoformat()


def build_scenario(cfg: dict) -> dict:
    steps = []
    for n, step in enumerate(cfg["steps"], start=1):
        rows = forecast_track(cfg, step)
        text, issued, fl_time = bulletin_text(cfg, step, 10 + n * 4, rows)
        steps.append({
            "step": f"T{step}", "hours_before_landfall": step, "bulletin_no": f"{cfg['code']}/{10 + n * 4:02d}",
            "issued_at": issued, "bulletin_text": text,
            "truth_parse": {"cyclone_name": cfg["cyclone_name"], "issued_at": issued, "track": rows,
                            "expected_landfall": {"area": cfg["landfall_area"], "time": fl_time},
                            "official_surge_text": cfg["official_surge_m"]},
        })
    return {
        "metadata": meta(cfg, "Approximate reconstruction from publicly reported IMD/RSMC New Delhi facts "
                              "(landfall place/time, intensity, surge guidance). Sample, not the official best track."),
        "replay_id": cfg["replay_id"], "code": cfg["code"], "cyclone_name": cfg["cyclone_name"],
        "state": cfg["state"], "district": cfg["district"], "landfall_time": cfg["landfall_time"],
        "landfall_area": cfg["landfall_area"],
        "model_params": {
            "rmw_km": cfg["rmw_km"], "shelf_factor": cfg["shelf_factor"], "tide_m": cfg["tide_m"],
            "surge_inland_decay_m_per_km": cfg["surge_inland_decay_m_per_km"], "rain_r0_mm_h": cfg["rain_r0_mm_h"],
            "antecedent_wetness": cfg["antecedent_wetness"],
            "_note": "Tide levels, shelf factor and rainfall scale are sample calibration values (documented in "
                     "geospatial/earth-engine/README.md).",
        },
        "hub": cfg["hub"],
        "truth_track": [{"hours_from_landfall": h, "lat": la, "lon": lo, "max_wind_kmh": v, "central_pressure_hpa": p}
                        for h, la, lo, v, p in cfg["truth"]],
        "steps": steps,
    }


def build_observed(cfg: dict, villages: list[dict]) -> dict:
    """Sample 'observed' flooded villages (deterministic) for the validation panel."""
    obs = []
    for k, v in enumerate(villages):
        d = dist_inland_km(cfg, v["lat"], v["lon"])
        dc = min(polyline_dist_km(v["lat"], v["lon"], ch["line"]) for ch in cfg["channels"])
        score = math.exp(-d / (3 if cfg["state"] == "OD" else 25)) + 0.6 * math.exp(-dc / 2.5) + 0.2 * noise(k, 1, 4.0)
        obs.append({"village_code": v["village_code"], "observed_flooded": score > 0.75})
    return {"metadata": meta(cfg, cfg["observed_flood_note"], is_synthetic=True), "villages": obs}


def to_state_format(cfg: dict, villages: list[dict]) -> list[dict]:
    if cfg["state"] != "WB":
        return villages
    return [{WB_FIELD_MAP.get(k, k): val for k, val in v.items()} for v in villages]


def main() -> None:
    for cfg in (FANI, AMPHAN):
        out = OUT / cfg["replay_id"]
        out.mkdir(parents=True, exist_ok=True)
        villages, pos = build_places(cfg)
        assets = build_assets(cfg, pos)
        files = {
            "scenario.json": build_scenario(cfg),
            "base_grid.json": build_grid(cfg),
            "villages.json": {"metadata": meta(cfg, "Real place names, approximate coordinates; population and "
                                                    "vulnerability are synthetic sample values.", True),
                              "villages": to_state_format(cfg, villages)},
            "assets.json": {"metadata": meta(cfg, "Sample shelters/substations/hospitals placed near real towns. "
                                                  "Real mode: state shelter lists + OpenStreetMap."),
                            "assets": assets},
            "roads.json": build_roads(cfg, villages, assets, pos),
            "observed_flood.json": build_observed(cfg, villages),
        }
        for name, obj in files.items():
            (out / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
                                    if name == "base_grid.json" else json.dumps(obj, ensure_ascii=False, indent=1))
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
