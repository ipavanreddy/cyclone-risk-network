"""Base hazard layers (PRD §10) sampled onto the replay grid.

- Elevation: Copernicus GLO-30 DEM (COPERNICUS/DEM/GLO30), mean per cell.
- Permanent water: JRC Global Surface Water v1.4 occurrence > 50 %, cell counted as water if > 50 % covered.
- Rainfall: GPM IMERG V07 half-hourly precipitation (mm/h) summed × 0.5 h over the window.
"""
import ee

from tatraksha_ee.common import grid_cells, reduce_cells


def dem() -> ee.Image:
    return ee.ImageCollection("COPERNICUS/DEM/GLO30").select("DEM").mosaic().rename("elevation")


def permanent_water() -> ee.Image:
    occ = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
    return occ.gt(50).unmask(0).rename("water")


def gpm_accumulation(start_iso: str, end_iso: str) -> ee.Image:
    col = ee.ImageCollection("NASA/GPM_L3/IMERG_V07").filterDate(start_iso, end_iso).select("precipitation")
    return col.sum().multiply(0.5).rename("rain_mm")


def sample_base_layers(lat_max: float, lon_min: float, cell_deg: float, rows: int, cols: int) -> dict:
    cells = grid_cells(lat_max, lon_min, cell_deg, rows, cols)
    stack = dem().unmask(0).addBands(permanent_water())
    res = reduce_cells(stack, cells, ee.Reducer.mean(), scale=90)
    n = rows * cols
    elevation = [round(float(res.get(i, {}).get("elevation") or 0.0), 2) for i in range(n)]
    water = [1 if float(res.get(i, {}).get("water") or 0.0) > 0.5 else 0 for i in range(n)]
    return {"elevation_m": elevation, "water": water,
            "source": "COPERNICUS/DEM/GLO30; JRC/GSW1_4/GlobalSurfaceWater"}


def sample_gpm(lat_max: float, lon_min: float, cell_deg: float, rows: int, cols: int, start_iso: str,
               end_iso: str) -> list[float]:
    cells = grid_cells(lat_max, lon_min, cell_deg, rows, cols)
    res = reduce_cells(gpm_accumulation(start_iso, end_iso), cells, ee.Reducer.first(), scale=11132, as_points=True)
    return [round(float(res.get(i, {}).get("first") or 0.0), 1) for i in range(rows * cols)]
