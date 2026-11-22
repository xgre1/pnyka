"""Area-weighted mean permitted building coefficient (Συντελεστής Δόμησης) per neighbourhood.

Only neighbourhoods with at least 50% of their area covered by a zone that has a numeric
coefficient get a value. A coefficient of 0 (non-buildable zone) is a real value and is kept.
"""
from shapely.geometry import shape
from shapely.strtree import STRtree

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
zones = []
for f in k.fetch_layer("synt_domisis")["features"]:
    try:
        sd = float(str(f["properties"].get("sd")).replace(",", "."))
    except ValueError:
        continue
    zones.append((shape(f["geometry"]).buffer(0), sd))
print("zones with numeric sd", len(zones))
tree = STRtree([z for z, _ in zones])
out = {}
for n, poly in nbs:
    num = cov = 0.0
    for i in tree.query(poly):
        a = poly.intersection(zones[i][0]).area
        num += a * zones[i][1]
        cov += a
    if cov >= 0.5 * poly.area:
        out[n] = num / cov
k.write("city_building_coefficient", out, {
    "name": "Επιτρεπόμενος συντελεστής δόμησης",
    "unit": "μέσος ΣΔ (σταθμισμένος με την έκταση)",
    "source": k.CITY + ": Συντελεστές Δόμησης περιοχής Δήμου Αθηναίων, CC BY 3.0 GR",
    "note": "Θεσμικός ΣΔ των ζωνών, όχι πόσο είναι πράγματι χτισμένη η γειτονιά· οι ζώνες ΣΔ 0 (πάρκα, αρχαιολογικοί χώροι) μετρούν.",
    "worse": "none",
}, decimals=2)
