"""Exposure per village (PRD §10, §14): WorldPop population and Google Open Buildings v3 counts
within a buffer of each village point."""
import ee


def worldpop() -> ee.Image:
    return (ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq("country", "IND"))
            .filter(ee.Filter.eq("year", 2020)).mosaic())


def village_exposure(points: list[dict], radius_m: float = 1500) -> dict[str, dict]:
    feats = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p["lon"], p["lat"]]).buffer(radius_m), {"id": p["id"]})
                                  for p in points])
    pop = worldpop().reduceRegions(collection=feats, reducer=ee.Reducer.sum(), scale=100)
    buildings = ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons").filter(
        ee.Filter.gte("confidence", 0.75))

    def count(f):
        return f.set("buildings", buildings.filterBounds(f.geometry()).size())

    out = {}
    for f in pop.map(count).getInfo()["features"]:
        props = f["properties"]
        out[props["id"]] = {"population": int(round(props.get("sum") or 0)), "buildings": props.get("buildings"),
                            "source": "WorldPop 2020 100 m; Open Buildings v3 (confidence ≥ 0.75)"}
    return out
