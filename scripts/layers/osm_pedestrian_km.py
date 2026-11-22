"""Pedestrian streets (highway=pedestrian, living_street), km per km2, from OSM.

Only linear ways; pedestrian squares mapped as areas (area=yes) are left out so
their outline is not counted as street length.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, way_lines, length_km, write_layer

data = fetch("pedestrian", """(
  way["highway"~"^(pedestrian|living_street)$"]["area"!="yes"]({bbox});
);out geom;""")
polys, pop = neighbourhoods()
km = length_km(polys, way_lines(data))
print("municipality total km:", round(sum(km.values()), 1), "ways in bbox:", len(data["elements"]))
dens = {n: km[n] / (p.area / 1e6) for n, p in polys}
write_layer("osm_pedestrian_km", {
    "name": "Πεζόδρομοι",
    "unit": "χλμ ανά km²",
    "note": "Πεζόδρομοι και δρόμοι ήπιας κυκλοφορίας του OSM· οι πλατείες ως επιφάνειες δεν μετρώνται",
    "worse": "low",
}, dens, 2)
