"""Shared Earth Engine helpers: the replay grid as EE features, chunked reduceRegions."""
import ee

CHUNK = 800


def grid_cells(lat_max: float, lon_min: float, cell_deg: float, rows: int, cols: int) -> list[dict]:
    cells = []
    for r in range(rows):
        top = lat_max - r * cell_deg
        for c in range(cols):
            left = lon_min + c * cell_deg
            cells.append({"i": r * cols + c, "rect": [left, top - cell_deg, left + cell_deg, top]})
    return cells


def reduce_cells(image: ee.Image, cells: list[dict], reducer: ee.Reducer, scale: float,
                 as_points: bool = False) -> dict[int, dict]:
    """reduceRegions over the grid in chunks (keeps each request under EE's element limits)."""
    out: dict[int, dict] = {}
    for k in range(0, len(cells), CHUNK):
        feats = []
        for cell in cells[k:k + CHUNK]:
            x0, y0, x1, y1 = cell["rect"]
            geom = ee.Geometry.Point([(x0 + x1) / 2, (y0 + y1) / 2]) if as_points else ee.Geometry.Rectangle([x0, y0, x1, y1])
            feats.append(ee.Feature(geom, {"i": cell["i"]}))
        fc = image.reduceRegions(collection=ee.FeatureCollection(feats), reducer=reducer, scale=scale)
        for f in fc.getInfo()["features"]:
            out[int(f["properties"]["i"])] = f["properties"]
    return out
