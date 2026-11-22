"""Cycleways and bike lanes, km per km2, from OSM.

highway=cycleway, and roads tagged cycleway / cycleway:left|right|both = lane|track|
shared_lane|share_busway. A road with a lane on both sides counts once (its length).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _osm import fetch, neighbourhoods, way_lines, length_km, write_layer

BIKE = "^(lane|track|shared_lane|share_busway|opposite_lane|opposite_track)$"
data = fetch("bike", f"""(
  way["highway"="cycleway"]({{bbox}});
  way["highway"="path"]["bicycle"="designated"]({{bbox}});
  way["cycleway"~"{BIKE}"]({{bbox}});
  way["cycleway:left"~"{BIKE}"]({{bbox}});
  way["cycleway:right"~"{BIKE}"]({{bbox}});
  way["cycleway:both"~"{BIKE}"]({{bbox}});
);out geom;""")
polys, pop = neighbourhoods()
km = length_km(polys, way_lines(data))
print("municipality total km:", round(sum(km.values()), 1), "ways in bbox:", len(data["elements"]))
dens = {n: km[n] / (p.area / 1e6) for n, p in polys}
write_layer("osm_bike_km", {
    "name": "Ποδηλατόδρομοι",
    "unit": "χλμ ανά km²",
    "note": "Ποδηλατόδρομοι και λωρίδες όπως είναι χαρτογραφημένοι στο OSM· η κάλυψη μπορεί να είναι ελλιπής",
    "worse": "low",
}, dens, 2)
