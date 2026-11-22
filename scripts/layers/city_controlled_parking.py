"""Percent of each neighbourhood's area inside a controlled-parking zone (Ζώνες Ελεγχόμενης Στάθμευσης)."""
from shapely.geometry import shape

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
zones = [shape(f["geometry"]) for f in k.fetch_layer("zones_stathmeusis")["features"]]
print("zones", len(zones))
k.write("city_controlled_parking", k.area_share(zones, nbs), {
    "name": "Ελεγχόμενη στάθμευση",
    "unit": "% της έκτασης",
    "source": k.CITY + ": Ζώνες Ελεγχόμενης Στάθμευσης, CC BY 3.0 GR",
    "note": "Δείχνει πού ισχύει το σύστημα, όχι πόσες θέσεις υπάρχουν ή αν επαρκούν.",
    "worse": "none",
}, decimals=1)
