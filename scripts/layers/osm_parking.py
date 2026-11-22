"""Car parking area (amenity=parking polygons) as % of neighbourhood area, from OSM.

Underground and multi-storey parkings are left out (parking=underground|multi-storey):
they do not take ground surface. Overlapping polygons are merged before measuring.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.ops import unary_union
from _osm import fetch, neighbourhoods, area_polygons, write_layer

data = fetch("parking", """(
  way["amenity"="parking"]({bbox});
  relation["amenity"="parking"]({bbox});
);out geom;""")
els = [e for e in data["elements"]
       if (e.get("tags") or {}).get("parking") not in ("underground", "multi-storey")]
parks = unary_union(area_polygons({"elements": els}))
polys, pop = neighbourhoods()
pct = {}
total_m2 = 0.0
for n, p in polys:
    a = parks.intersection(p).area
    total_m2 += a
    pct[n] = a / p.area * 100
print("polygons in bbox:", len(els), "surface parking inside neighbourhoods (ha):", round(total_m2 / 1e4, 1))
write_layer("osm_parking", {
    "name": "Επιφάνεια χώρων στάθμευσης",
    "unit": "%",
    "note": "Υπαίθριοι χώροι στάθμευσης του OSM· η στάθμευση στο δρόμο δεν περιλαμβάνεται",
    "worse": "high",
}, pct, 2)
