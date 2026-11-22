"""Municipal sports facilities (open sports centres + closed courts + pools) per 1,000 residents."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

nbs = k.neighbourhoods()
pts = []
for layer in ("anoixta_gipeda24", "kleista_gipeda", "kolimbitiria"):
    p = k.points(layer)
    print(layer, len(p))
    pts += [(pt, 1) for pt, _ in p]
counts, outside = k.assign(pts, nbs)
print("features", len(pts), "outside", outside)
k.write("city_sports", k.per_1000(counts, k.population()), {
    "name": "Δημοτικοί αθλητικοί χώροι",
    "unit": "ανά 1.000 κατοίκους",
    "source": k.CITY + ": Ανοιχτά Αθλητικά Κέντρα (2024), Κλειστά Γήπεδα, Κολυμβητήρια, CC BY 3.0 GR",
    "note": "Μόνο οι χώροι του Δήμου (ΟΠΑΝΔΑ), όχι ιδιωτικά γυμναστήρια ή σχολικές αυλές· μετράει πλήθος, όχι μέγεθος.",
    "worse": "low",
}, decimals=3)
