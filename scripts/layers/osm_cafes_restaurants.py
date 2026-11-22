"""Cafes, restaurants, bars and fast food per km2, from OSM (nightlife / noise context)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, per_km2, write_layer, municipality_total

data = fetch("cafes_restaurants", """(
  nwr["amenity"~"^(cafe|restaurant|bar|pub|fast_food)$"]({bbox});
);out center;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
print("municipality total:", municipality_total(counts))
write_layer("osm_cafes_restaurants", {
    "name": "Καφέ και εστιατόρια",
    "unit": "ανά km²",
    "note": "Καφέ, εστιατόρια, μπαρ και φαστφούντ του OSM· δείχνει κίνηση, όχι καλό ή κακό",
    "worse": "none",
}, per_km2(polys, counts), 1)
