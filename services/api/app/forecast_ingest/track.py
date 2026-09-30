"""Track uncertainty (track set + cone) and a parametric wind field (PRD §9).

Transparent, deterministic:
- Cone radius by lead time uses typical IMD track-forecast errors (approx. 24 h ≈ 77 km, 48 h ≈ 117 km,
  72 h ≈ 159 km; sample values of the order reported in IMD annual verification reports).
- Track set: members shifted perpendicular to the track by k × cone radius, k ∈ [-1, 1].
- Wind: modified Rankine vortex, V = Vmax·r/Rmw inside Rmw, Vmax·(Rmw/r)^0.6 outside.
"""
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.geo import KM_PER_DEG, km, offset, to_xy

ERROR_TABLE_KM = [(0, 0), (12, 50), (24, 77), (36, 95), (48, 117), (60, 140), (72, 159), (96, 220), (120, 280)]
TRACK_SET_K = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
GALE_KMH = 62


@dataclass
class TrackPt:
    time: datetime
    lat: float
    lon: float
    vmax: float
    pc: float | None
    lead_h: float


def cone_radius_km(lead_h: float) -> float:
    for (h0, r0), (h1, r1) in zip(ERROR_TABLE_KM, ERROR_TABLE_KM[1:]):
        if h0 <= lead_h <= h1:
            return r0 + (r1 - r0) * (lead_h - h0) / (h1 - h0)
    return ERROR_TABLE_KM[-1][1]


def from_parse(track: list[dict], issued_at: str) -> list[TrackPt]:
    t0 = datetime.fromisoformat(issued_at)
    pts = []
    for p in track:
        t = datetime.fromisoformat(p["time"])
        pts.append(TrackPt(t, p["lat"], p["lon"], p["max_wind_kmh"], p.get("central_pressure_hpa"),
                           max(0.0, (t - t0).total_seconds() / 3600)))
    return sorted(pts, key=lambda p: p.time)


def interpolate(pts: list[TrackPt], step_h: float = 1.0) -> list[TrackPt]:
    out = []
    for a, b in zip(pts, pts[1:]):
        span = (b.time - a.time).total_seconds() / 3600
        n = max(1, int(span / step_h))
        for i in range(n):
            f = i / n
            pc = None if a.pc is None or b.pc is None else a.pc + f * (b.pc - a.pc)
            out.append(TrackPt(a.time + timedelta(hours=f * span), a.lat + f * (b.lat - a.lat),
                               a.lon + f * (b.lon - a.lon), a.vmax + f * (b.vmax - a.vmax), pc,
                               a.lead_h + f * (b.lead_h - a.lead_h)))
    out.append(pts[-1])
    return out


def heading(pts: list[TrackPt], i: int) -> tuple[float, float]:
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    x, y = to_xy(b.lat, b.lon, a.lat, a.lon)
    n = math.hypot(x, y) or 1.0
    return x / n, y / n


def shifted(pts: list[TrackPt], k: float) -> list[TrackPt]:
    """Member track shifted k × cone radius to the right (k>0) of the direction of motion."""
    out = []
    for i, p in enumerate(pts):
        hx, hy = heading(pts, i)
        r = k * cone_radius_km(p.lead_h)
        lat, lon = offset(p.lat, p.lon, hy * r, -hx * r)  # right normal = (hy, -hx)
        out.append(TrackPt(p.time, lat, lon, p.vmax, p.pc, p.lead_h))
    return out


def track_set(pts: list[TrackPt]) -> list[tuple[float, list[TrackPt]]]:
    return [(k, shifted(pts, k)) for k in TRACK_SET_K]


def cone_polygon(pts: list[TrackPt]) -> list[list[float]]:
    """[[lat, lon], ...] closed polygon: right edge forward, left edge back, with rounded end caps."""
    right = shifted(pts, 1.0)
    left = shifted(pts, -1.0)
    ring = [[p.lat, p.lon] for p in right] + [[p.lat, p.lon] for p in reversed(left)]
    ring.append(ring[0])
    return [[round(a, 4), round(b, 4)] for a, b in ring]


def coast_signed_km(coast: dict, lat: float, lon: float) -> float:
    b = coast["b"]
    dlat_km = (lat - (coast["a"] + b * (lon - coast["lon0"]))) * KM_PER_DEG
    return dlat_km / math.sqrt(1 + (b / math.cos(math.radians(lat))) ** 2)


def landfall(pts: list[TrackPt], coast: dict) -> dict:
    """First crossing of the coastline (sea -> land). Falls back to the closest approach."""
    fine = interpolate(pts, 0.25)
    for i, (a, b) in enumerate(zip(fine, fine[1:])):
        da, db = coast_signed_km(coast, a.lat, a.lon), coast_signed_km(coast, b.lat, b.lon)
        if da <= 0 < db:
            f = -da / (db - da)
            hx, hy = heading(fine, i)
            pc = a.pc if a.pc is not None else None
            return {"time": (a.time + (b.time - a.time) * f).isoformat(), "lat": a.lat + f * (b.lat - a.lat),
                    "lon": a.lon + f * (b.lon - a.lon), "vmax": a.vmax + f * (b.vmax - a.vmax),
                    "pc": pc, "heading": (hx, hy), "crossed": True}
    best = min(range(len(fine)), key=lambda i: abs(coast_signed_km(coast, fine[i].lat, fine[i].lon)))
    p = fine[best]
    return {"time": p.time.isoformat(), "lat": p.lat, "lon": p.lon, "vmax": p.vmax, "pc": p.pc,
            "heading": heading(fine, best), "crossed": False}


def wind_at(vmax: float, r_km: float, rmw_km: float) -> float:
    if r_km < rmw_km:
        return vmax * max(r_km, 1.0) / rmw_km
    return vmax * (rmw_km / r_km) ** 0.6


def wind_field(pts: list[TrackPt], grid, rmw_km: float, landfall_time: datetime) -> tuple[list[float], list[float | None]]:
    """Per cell: max sustained wind (km/h) and gale arrival (hours before landfall; None if never gale)."""
    hourly = interpolate(pts, 1.0)
    bb = grid.bbox
    clat, clon = (bb["lat_min"] + bb["lat_max"]) / 2, (bb["lon_min"] + bb["lon_max"]) / 2
    hourly = [p for p in hourly if km(p.lat, p.lon, clat, clon) < 600]
    n = grid.rows * grid.cols
    vmax = [0.0] * n
    arrival: list[float | None] = [None] * n
    lats = [grid.lat(r) for r in range(grid.rows)]
    lons = [grid.lon(c) for c in range(grid.cols)]
    for p in hourly:
        coslat = math.cos(math.radians(p.lat))
        hrs_before = (landfall_time - p.time).total_seconds() / 3600
        for r, la in enumerate(lats):
            dy = (la - p.lat) * KM_PER_DEG
            base = r * grid.cols
            for c, lo in enumerate(lons):
                d = math.hypot(dy, (lo - p.lon) * KM_PER_DEG * coslat)
                v = wind_at(p.vmax, d, rmw_km)
                i = base + c
                vmax[i] = max(vmax[i], v)
                if v >= GALE_KMH and arrival[i] is None:
                    arrival[i] = hrs_before
    return [round(v, 1) for v in vmax], [None if a is None else round(a, 1) for a in arrival]
