"""Active municipal fountains (Υδατοπίδακες, status ΕΝΕΡΓΟ) per km2."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
allp = k.points("pidakes")
pts = [(pt, 1) for pt, pr in allp if pr.get("status") == "ΕΝΕΡΓΟ"]
counts, outside = k.assign(pts, nbs)
print("features", len(allp), "active", len(pts), "outside", outside)
k.write("city_fountains", k.per_km2(counts, nbs), {
    "name": "Ενεργά σιντριβάνια",
    "unit": "ανά km²",
    "source": k.CITY + ": Υδατοπίδακες, CC BY 3.0 GR",
    "note": "Διακοσμητικοί πίδακες σε πλατείες, όχι βρύσες πόσιμου νερού· 11 ανενεργοί δεν μετρήθηκαν.",
    "worse": "none",
}, decimals=2)
