"""Distance (m) from each neighbourhood's centroid to the nearest ΚΕΠ (citizen service centre)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
pts = k.points("kep")
print("features", len(pts))
k.write("city_kep_distance", k.nearest_distance(pts, nbs), {
    "name": "Απόσταση από ΚΕΠ",
    "unit": "μέτρα",
    "source": k.CITY + ": ΚΕΠ - Κέντρα Εξυπηρέτησης Πολιτών, CC BY 3.0 GR",
    "note": "Ευθεία απόσταση από το κέντρο της γειτονιάς προς τα 8 ΚΕΠ του Δήμου· δεν λαμβάνει υπόψη ωράρια ή ψηφιακή εξυπηρέτηση.",
    "worse": "high",
}, decimals=0)
