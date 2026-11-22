"""Benches per km2, from OSM. Relevant to the elderly and to shade."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, per_km2, write_layer, municipality_total

data = fetch("benches", """(
  node["amenity"="bench"]({bbox});
  way["amenity"="bench"]({bbox});
);out center;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
total = municipality_total(counts)
print("municipality total:", total)
if total < 30:
    print("SKIP: fewer than 30 features in the Municipality")
    sys.exit(0)
write_layer("osm_benches", {
    "name": "Παγκάκια",
    "unit": "ανά km²",
    "note": "Παγκάκια του OSM· η χαρτογράφηση είναι πολύ άνιση, άρα δείχνει κυρίως πού έχει χαρτογραφηθεί",
    "worse": "low",
}, per_km2(polys, counts), 1)
