"""Existing tree canopy as a transparent PNG for the map (shown when zoomed into an area).

Source: raw/treecover/dl/meta_chm_athens.tif (Meta/WRI canopy height, EPSG:3857, about 1.2 m pixels).
Kept: pixels with canopy height >= 3 m, inside the 144 neighbourhoods. Downsampled 3x (about 3.6 m pixels).
Writes app/public/data/canopy.png and app/public/data/canopy.json (corner coordinates for a MapLibre image source).
Run with the scratchpad venv (numpy, rasterio, pillow or a plain PNG writer below):
    python -I app/scripts/canopy_png.py
"""
import json
import math
import os
import struct
import zlib

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "raw", "treecover", "dl", "meta_chm_athens.tif")
NB = os.path.join(ROOT, "app", "public", "data", "neighbourhoods.geojson")
OUT = os.path.join(ROOT, "app", "public", "data")
FACTOR = 3
MIN_HEIGHT_M = 3
RGBA = (79, 214, 140, 150)  # quiet green, semi-transparent


def merc(lon, lat):
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180
    return x, y


def lonlat(x, y):
    lon = x / 20037508.34 * 180
    lat = math.degrees(2 * math.atan(math.exp(y / 20037508.34 * math.pi)) - math.pi / 2)
    return [round(lon, 6), round(lat, 6)]


def write_png(path, rgba):
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].tobytes() for y in range(h))
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


with rasterio.open(SRC) as r:
    w, h = r.width // FACTOR, r.height // FACTOR
    full = r.read(1)[: h * FACTOR, : w * FACTOR]
    chm = full.reshape(h, FACTOR, w, FACTOR).max(axis=(1, 3))
    tr = r.transform * r.transform.scale(r.width / w, r.height / h)
    b = r.bounds

geo = json.load(open(NB, encoding="utf-8"))
shapes = []
for f in geo["features"]:
    g = f["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        shapes.append(({"type": "Polygon", "coordinates": [[list(merc(*c)) for c in ring] for ring in poly]}, 1))
inside = rasterize(shapes, out_shape=(h, w), transform=tr, fill=0, dtype="uint8")

mask = (chm >= MIN_HEIGHT_M) & (inside == 1)
rgba = np.zeros((h, w, 4), dtype=np.uint8)
rgba[mask] = RGBA
write_png(os.path.join(OUT, "canopy.png"), rgba)
coords = [lonlat(b.left, b.top), lonlat(b.right, b.top), lonlat(b.right, b.bottom), lonlat(b.left, b.bottom)]
json.dump({"coordinates": coords, "min_height_m": MIN_HEIGHT_M, "pixel_m": round(1.194 * FACTOR, 2)}, open(os.path.join(OUT, "canopy.json"), "w"))
print(w, h, int(mask.sum()), "canopy pixels", os.path.getsize(os.path.join(OUT, "canopy.png")), "bytes")
