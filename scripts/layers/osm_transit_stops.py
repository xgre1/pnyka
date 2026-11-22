"""Bus, trolley and tram stops plus metro entrances per km2, from OSM."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, per_km2, write_layer, municipality_total

data = fetch("transit_stops", """(
  node["highway"="bus_stop"]({bbox});
  node["public_transport"="platform"]["bus"="yes"]({bbox});
  node["public_transport"="platform"]["trolleybus"="yes"]({bbox});
  node["railway"="tram_stop"]({bbox});
  node["railway"="subway_entrance"]({bbox});
);out;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
print("municipality total:", municipality_total(counts))
write_layer("osm_transit_stops", {
    "name": "Στάσεις συγκοινωνίας",
    "unit": "ανά km²",
    "note": "Στάσεις λεωφορείου, τρόλεϊ, τραμ και είσοδοι μετρό· δεν μετρά τη συχνότητα των δρομολογίων",
    "worse": "low",
}, per_km2(polys, counts), 1)
