"""Screening storm-surge inundation in Earth Engine (PRD §11) — the same transparent bathtub model the
API runs on the replay grid, here at DEM resolution:

  W_in(x) = coastal water level − decay × distance inland (km)
  flooded  = DEM < W_in  AND connected to the sea through flooded pixels or permanent water
  depth    = W_in − DEM

The coastal water level comes from app/surge/model.py (1 cm/hPa × Δp + 4.2e-4 × V² × shelf + tide).
Label: "Screening estimate – defer to official surge guidance".
"""
import ee

from tatraksha_ee.layers import dem, permanent_water

PALETTE = ["c6dbef", "6baed6", "2171b5", "08306b"]


def inundation_image(bbox: dict, water_level_m: float, decay_m_per_km: float, max_inland_km: float = 40) -> ee.Image:
    region = ee.Geometry.Rectangle([bbox["lon_min"], bbox["lat_min"], bbox["lon_max"], bbox["lat_max"]])
    elev = dem().unmask(0).clip(region)
    water = permanent_water().clip(region)
    sea = elev.lte(0).And(water)
    # distance from the sea in km (fastDistanceTransform returns squared pixel distance)
    dist_km = sea.fastDistanceTransform(512).sqrt().multiply(ee.Image.pixelArea().sqrt()).divide(1000)
    level = ee.Image.constant(water_level_m).subtract(dist_km.multiply(decay_m_per_km))
    candidate = elev.lt(level).Or(water)
    # connectivity: cumulative cost from the sea over candidate pixels only
    cost = ee.Image.constant(1).updateMask(candidate)
    reach = cost.cumulativeCost(source=sea.selfMask(), maxDistance=max_inland_km * 1000)
    connected = reach.mask().And(water.Not())
    depth = level.subtract(elev).updateMask(connected).updateMask(level.subtract(elev).gt(0))
    return depth.rename("surge_depth_m").set({"label": "Screening estimate – defer to official surge guidance",
                                             "water_level_m": water_level_m, "decay_m_per_km": decay_m_per_km})


def inundation_tile_url(bbox: dict, water_level_m: float, decay_m_per_km: float) -> dict:
    img = inundation_image(bbox, water_level_m, decay_m_per_km)
    map_id = img.getMapId({"min": 0, "max": 3, "palette": PALETTE})
    return {"url_format": map_id["tile_fetcher"].url_format,
            "label": "Earth Engine screening surge inundation – defer to official surge guidance",
            "attribution": "Google Earth Engine; Copernicus GLO-30 DEM; JRC Global Surface Water"}
