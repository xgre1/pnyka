"""Distance (m) from each neighbourhood's centroid to the nearest Metro / Tram / rail station."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
pts = k.points("stasy2024")
print("features", len(pts))
k.write("city_rail_distance", k.nearest_distance(pts, nbs), {
    "name": "Απόσταση από σταθμό Μετρό, Τραμ ή τρένου",
    "unit": "μέτρα",
    "source": k.CITY + ": Σταθμοί Μετρό, Τραμ, ΟΣΕ (2024), CC BY 3.0 GR",
    "note": "Ευθεία απόσταση από το κέντρο της γειτονιάς, όχι πεζή διαδρομή· χωρίς τους σταθμούς της Γραμμής 4 υπό κατασκευή.",
    "worse": "high",
}, decimals=0)
