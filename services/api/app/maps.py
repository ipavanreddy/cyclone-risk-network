"""Google Maps Platform server-side adapter (MAPS_API_KEY): Geocoding + Routes.

Used for shelter reachability context: normal-conditions drive time from a village to its assigned shelter
(Routes API) and the Google-formatted address of the village location (reverse Geocoding). Flood/surge road
cut-offs still come from our own road-network model; Google Routes does not know about forecast flooding,
so its drive time is labelled "pre-storm / normal conditions". Demo mode returns None.
"""
from functools import lru_cache

import httpx

from app import integrations
from app.config import settings

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


def geocode(address: str) -> dict:
    """Forward geocode (raises on failure). Used by the status probe and /api/geocode."""
    r = httpx.get(GEOCODE_URL, params={"address": address, "region": "in", "key": settings.maps_api_key}, timeout=15)
    r.raise_for_status()
    body = r.json()
    if body.get("status") not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Geocoding {body.get('status')}: {body.get('error_message', '')}")
    res = body.get("results") or []
    if not res:
        return {"query": address, "found": False}
    top = res[0]
    loc = top["geometry"]["location"]
    return {"query": address, "found": True, "formatted_address": top["formatted_address"], "lat": loc["lat"],
            "lon": loc["lng"], "place_id": top.get("place_id"), "source": "Google Geocoding API"}


@lru_cache(maxsize=512)
def reverse_geocode(lat: float, lon: float) -> str | None:
    if not integrations.maps_enabled():
        return None
    try:
        r = httpx.get(GEOCODE_URL, params={"latlng": f"{lat},{lon}", "key": settings.maps_api_key,
                                           "result_type": "locality|sublocality|administrative_area_level_3|"
                                                          "administrative_area_level_2"}, timeout=15)
        r.raise_for_status()
        body = r.json()
        if body.get("status") not in ("OK", "ZERO_RESULTS"):
            raise RuntimeError(f"Geocoding {body.get('status')}: {body.get('error_message', '')}")
        integrations.clear_error("maps_routes")
        res = body.get("results") or []
        return res[0]["formatted_address"] if res else None
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("maps_routes", exc)
        return None


@lru_cache(maxsize=1024)
def drive_route(o_lat: float, o_lon: float, d_lat: float, d_lon: float) -> dict | None:
    """Google Routes API drive distance/time (normal traffic conditions). None in demo mode or on failure."""
    if not integrations.maps_enabled():
        return None
    try:
        r = httpx.post(ROUTES_URL, headers={"X-Goog-Api-Key": settings.maps_api_key,
                                            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters"},
                       json={"origin": {"location": {"latLng": {"latitude": o_lat, "longitude": o_lon}}},
                             "destination": {"location": {"latLng": {"latitude": d_lat, "longitude": d_lon}}},
                             "travelMode": "DRIVE"}, timeout=15)
        r.raise_for_status()
        routes = r.json().get("routes") or []
        integrations.clear_error("maps_routes")
        if not routes:
            return {"found": False, "source": "Google Routes API"}
        rt = routes[0]
        return {"found": True, "distance_km": round(rt["distanceMeters"] / 1000, 1),
                "duration_min": round(int(rt["duration"].rstrip("s")) / 60), "source": "Google Routes API",
                "conditions": "normal (pre-storm) road conditions; forecast flood cut-offs are from the TatRaksha "
                              "road-network model"}
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("maps_routes", exc)
        return None
