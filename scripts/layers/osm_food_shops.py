"""Supermarkets, groceries and bakeries per 1,000 residents, from OSM (food-access proxy)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, element_points, count_points, per_1000, write_layer, municipality_total

data = fetch("food_shops", """(
  nwr["shop"~"^(supermarket|convenience|grocery|greengrocer|bakery)$"]({bbox});
);out center;""")
polys, pop = neighbourhoods()
counts = count_points(polys, element_points(data))
print("municipality total:", municipality_total(counts))
write_layer("osm_food_shops", {
    "name": "Καταστήματα τροφίμων",
    "unit": "ανά 1.000 κατοίκους",
    "note": "Σούπερ μάρκετ, μίνι μάρκετ, μανάβικα και φούρνοι του OSM· η κάλυψη των μικρών καταστημάτων είναι ελλιπής",
    "worse": "low",
}, per_1000(polys, counts, pop), 2)
