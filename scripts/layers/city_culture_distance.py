"""Distance (m) from each neighbourhood's centroid to the nearest municipal cultural venue."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
pts = k.points("politismos24_f")
print("features", len(pts))
k.write("city_culture_distance", k.nearest_distance(pts, nbs), {
    "name": "Απόσταση από δημοτικό χώρο πολιτισμού",
    "unit": "μέτρα",
    "source": k.CITY + ": Χώροι πολιτισμού Δήμου Αθηναίων (2024: μουσεία, βιβλιοθήκες, θέατρα, πολιτιστικά κέντρα), CC BY 3.0 GR",
    "note": "Ευθεία απόσταση από το κέντρο της γειτονιάς· μόνο οι 25 χώροι του Δήμου, όχι ιδιωτικοί ή κρατικοί.",
    "worse": "high",
}, decimals=0)
