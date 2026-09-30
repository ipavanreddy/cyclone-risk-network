"""Render the hazard map as a PNG (stdlib only) — the image Gemini receives for multimodal reasoning,
also served to the dashboard so officers see exactly what the model saw."""
import struct
import zlib

SCALE = 4  # pixels per grid cell

SEA = (170, 200, 230)
LAND = (236, 232, 220)
BANDS = {"Very High": (140, 0, 30), "High": (230, 60, 30), "Moderate": (245, 170, 40), "Low": (60, 150, 80)}


def _png(width: int, height: int, rows: list[bytearray]) -> bytes:
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def _mix(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def cell_color(i: int, layers: dict, layer: str):
    if layers["water"][i]:
        return SEA
    col = LAND
    if layer in ("composite", "flood"):
        p = layers["flood_likelihood"][i]
        if p >= 0.35:
            col = _mix(col, (80, 160, 90), min(1.0, (p - 0.35) / 0.5) * 0.8)
    if layer in ("composite", "wind"):
        w = layers["wind_max"][i]
        if layer == "wind" and w >= 62:
            col = _mix(col, (150, 60, 170), min(1.0, (w - 62) / 140))
    if layer in ("composite", "surge"):
        d = layers["surge_expected"][i]
        dh = layers["surge_high"][i]
        if d > 0:
            col = _mix((90, 140, 255), (10, 30, 150), min(1.0, d / 2.0))
        elif dh > 0:
            col = _mix(col, (120, 170, 255), 0.6)
    return col


def hazard_png(result: dict, layer: str = "composite") -> bytes:
    g = result["grid"]
    rows_n, cols_n, d = g["rows"], g["cols"], g["cell_deg"]
    layers = result["layers"]
    w, h = cols_n * SCALE, rows_n * SCALE
    img = [bytearray(w * 3) for _ in range(h)]
    for r in range(rows_n):
        for c in range(cols_n):
            col = cell_color(r * cols_n + c, layers, layer)
            for y in range(r * SCALE, (r + 1) * SCALE):
                row = img[y]
                for x in range(c * SCALE, (c + 1) * SCALE):
                    row[x * 3:x * 3 + 3] = bytes(col)

    def px(lat, lon):
        return int((lon - g["lon_min"]) / d * SCALE), int((g["lat_max"] - lat) / d * SCALE)

    def dot(x, y, col, rad):
        for yy in range(y - rad, y + rad + 1):
            for xx in range(x - rad, x + rad + 1):
                if 0 <= xx < w and 0 <= yy < h and (xx - x) ** 2 + (yy - y) ** 2 <= rad * rad:
                    img[yy][xx * 3:xx * 3 + 3] = bytes(col)

    # forecast track (black dots along interpolated segments)
    pts = result["track"]["points"]
    for a, b in zip(pts, pts[1:]):
        for k in range(40):
            f = k / 40
            dot(*px(a["lat"] + f * (b["lat"] - a["lat"]), a["lon"] + f * (b["lon"] - a["lon"])), (20, 20, 20), 1)
    for a in result["assets"]:
        if a["type"] == "shelter":
            col = (0, 0, 0) if a.get("cut_off") else (255, 255, 255)
            dot(*px(a["lat"], a["lon"]), col, 3)
    for v in result["villages"]:
        dot(*px(v["lat"], v["lon"]), BANDS[v["risk_band"]], 5)
    lf = result["scenario"]["forecast_landfall"]
    dot(*px(lf["lat"], lf["lon"]), (255, 0, 200), 6)
    return _png(w, h, img)


LEGEND = ("Hazard map legend: light blue = sea, rivers and lagoons; blue shades = screening storm-surge inundation (expected; "
          "darker = deeper, pale blue = high case only); green shading = rainfall flood likelihood ≥ 0.35; "
          "coloured circles = villages by Village Risk band (dark red Very High, red High, amber Moderate, "
          "green Low); white squares = safe shelters, black = cut-off shelters; black dotted line = forecast "
          "track; magenta = forecast landfall point. North is up.")
