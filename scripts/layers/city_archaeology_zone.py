"""Percent of each neighbourhood's area inside the Archaeology Sector (Τομέας Αρχαιολογίας, ΦΕΚ 96Δ/2004)."""
from shapely.geometry import shape

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
zones = [shape(f["geometry"]) for f in k.fetch_layer("orioarxaiologias")["features"]]
print("polygons", len(zones))
k.write("city_archaeology_zone", k.area_share(zones, nbs), {
    "name": "Τομέας Αρχαιολογίας",
    "unit": "% της έκτασης",
    "source": k.CITY + ": Τομέας Αρχαιολογίας (όριο ΦΕΚ 96Δ/2004), CC BY 3.0 GR",
    "note": "Θεσμικό όριο με αυστηρότερους όρους για εκσκαφές και δόμηση· δεν δείχνει πού υπάρχουν ευρήματα.",
    "worse": "none",
}, decimals=1)
