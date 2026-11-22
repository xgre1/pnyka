"""Municipal EV charging points (sum of 'theseis' per site) per km2."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
allp = k.points("Protergia_charge_place")
pts = [(pt, float(pr.get("theseis") or 1)) for pt, pr in allp]
counts, outside = k.assign(pts, nbs)
print("sites", len(allp), "spots", sum(w for _, w in pts), "outside", outside)
k.write("city_ev_chargers", k.per_km2(counts, nbs), {
    "name": "Θέσεις φόρτισης ηλεκτρικών οχημάτων",
    "unit": "θέσεις ανά km²",
    "source": k.CITY + ": Θέσεις φόρτισης ηλεκτρικών αυτοκινήτων (δίκτυο Δήμου), CC BY 3.0 GR",
    "note": "Μόνο οι 19 θέσεις του δημοτικού δικτύου· οι ιδιωτικοί φορτιστές δεν περιλαμβάνονται.",
    "worse": "low",
}, decimals=2)
