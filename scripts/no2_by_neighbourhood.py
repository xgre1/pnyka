"""NO2 annual mean 2024 (EEA interpolated, 1 km, EPSG:3035) sampled per Athens neighbourhood.
Mean of the 1 km cells whose 100 m sub-samples fall inside the polygon (area-weighted)."""
import json, sys, csv
import numpy as np, rasterio
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.prepared import prep
tif, geo, out = sys.argv[1], sys.argv[2], sys.argv[3]
g = json.load(open(geo, encoding="utf-8"))
tr = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
with rasterio.open(tif) as r:
    arr = r.read(1); nod = r.nodata; T = r.transform
    rows = []
    for f in g["features"]:
        poly = shape(f["geometry"]); pp = prep(poly)
        minx, miny, maxx, maxy = poly.bounds
        vals = []
        for x in np.arange(minx, maxx, 0.0012):
            for y in np.arange(miny, maxy, 0.0009):
                if pp.contains(Point(x, y)):
                    X, Y = tr.transform(x, y)
                    c, rr = ~T * (X, Y)
                    v = arr[int(rr), int(c)]
                    if nod is None or v != nod:
                        vals.append(float(v))
        if not vals:
            c = poly.representative_point(); X, Y = tr.transform(c.x, c.y); cc, rr = ~T * (X, Y); vals = [float(arr[int(rr), int(cc)])]
        rows.append({"name": f["properties"]["name"], "no2_2024_ugm3": round(sum(vals) / len(vals), 2), "n_samples": len(vals)})
w = csv.DictWriter(open(out, "w", encoding="utf-8", newline=""), fieldnames=list(rows[0]))
w.writeheader(); w.writerows(rows)
v = [x["no2_2024_ugm3"] for x in rows]
print(len(rows), min(v), max(v), round(sum(v)/len(v), 1))
