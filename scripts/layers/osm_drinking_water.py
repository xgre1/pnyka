"""Public drinking-water points (count per neighbourhood), from OSM. Relevant to heat."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, write_layer, municipality_total

data = fetch("drinking_water", """(
  node["amenity"="drinking_water"]({bbox});
  node["amenity"="fountain"]["drinking_water"="yes"]({bbox});
  node["man_made"="water_tap"]["drinking_water"="yes"]({bbox});
);out;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
total = municipality_total(counts)
print("municipality total:", total)
if total < 30:
    print("SKIP: fewer than 30 features in the Municipality")
    sys.exit(0)
write_layer("osm_drinking_water", {
    "name": "Βρύσες πόσιμου νερού",
    "unit": "πλήθος",
    "note": "Δημόσιες βρύσες του OSM· η χαρτογράφηση είναι ελλιπής και δεν ξέρουμε αν λειτουργούν",
    "worse": "low",
}, {n: float(c) for n, c in counts.items()}, 0)
