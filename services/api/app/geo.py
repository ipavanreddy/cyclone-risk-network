"""Small geodesy helpers (equirectangular km approximation; fine at district scale)."""
import math

KM_PER_DEG = 111.2


def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = (lat2 - lat1) * KM_PER_DEG
    dlon = (lon2 - lon1) * KM_PER_DEG * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dlat, dlon)


def to_xy(lat: float, lon: float, lat0: float, lon0: float) -> tuple[float, float]:
    """km east, km north of (lat0, lon0)."""
    return (lon - lon0) * KM_PER_DEG * math.cos(math.radians(lat0)), (lat - lat0) * KM_PER_DEG


def offset(lat: float, lon: float, east_km: float, north_km: float) -> tuple[float, float]:
    return lat + north_km / KM_PER_DEG, lon + east_km / (KM_PER_DEG * math.cos(math.radians(lat)))


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))
