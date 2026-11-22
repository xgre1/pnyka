"""Street lamps (highway=street_lamp) per km2, from OSM. Skipped if < 200 in the Municipality."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, per_km2, write_layer, municipality_total

data = fetch("street_lamps", """(
  node["highway"="street_lamp"]({bbox});
);out;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
total = municipality_total(counts)
print("municipality total:", total, "neighbourhoods with any:", sum(1 for c in counts.values() if c))
# Nov 2026 run: 244 lamps, but in only 33 of 144 neighbourhoods and ~70% of them in
# Syntagma alone: a few micro-mapped spots, not coverage. Skip unless half have any.
covered = sum(1 for c in counts.values() if c)
if total < 200 or covered < len(counts) / 2:
    print("SKIP: too few lamps or too patchy coverage to publish")
    sys.exit(0)
write_layer("osm_street_lamps", {
    "name": "Φανοστάτες",
    "unit": "ανά km²",
    "note": "Φανοστάτες του OSM· η χαρτογράφηση είναι πολύ ελλιπής",
    "worse": "low",
}, per_km2(polys, counts), 1)
