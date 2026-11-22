"""Pharmacies per 1,000 residents, from OSM."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, per_1000, write_layer, municipality_total

data = fetch("pharmacies", """(
  nwr["amenity"="pharmacy"]({bbox});
  nwr["healthcare"="pharmacy"]({bbox});
);out center;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
print("municipality total:", municipality_total(counts))
write_layer("osm_pharmacies", {
    "name": "Φαρμακεία",
    "unit": "ανά 1.000 κατοίκους",
    "note": "Φαρμακεία όπως είναι χαρτογραφημένα στο OSM· μερικά μπορεί να λείπουν",
    "worse": "low",
}, per_1000(polys, counts, pop), 2)
