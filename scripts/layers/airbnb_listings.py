"""Inside Airbnb Athens: entire-home listings per 1,000 residents.

Input: listings.csv.gz of the snapshot below (anonymous download, CC BY 4.0), cached in
CKAN_CACHE/airbnb/. Listing coordinates are lon/lat (WGS84), projected to EPSG:2100.
"""
import csv
import gzip
import os
import subprocess

from shapely.geometry import Point

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ckan as k  # noqa: E402

SNAPSHOT = "2026-09-22"
URL = f"https://data.insideairbnb.com/greece/attica/athens/{SNAPSHOT}/data/listings.csv.gz"
path = os.path.join(k.CACHE, "airbnb", "listings.csv.gz")
if not os.path.exists(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(["curl", "-s", "-m", "180", "-o", path, URL], check=True)

rows = list(csv.DictReader(gzip.open(path, "rt", encoding="utf-8")))
entire = [r for r in rows if r["room_type"] == "Entire home/apt"]
active = sum(1 for r in entire if r["number_of_reviews_ltm"] not in ("", "0"))
print("listings", len(rows), "entire", len(entire), "entire with review in last 12 months", active)

nbs = k.neighbourhoods()
pts = [(Point(*k._to2100.transform(float(r["longitude"]), float(r["latitude"]))), 1) for r in entire]
counts, outside = k.assign(pts, nbs)
print("outside polygons", outside)
k.write("airbnb_listings", k.per_1000(counts, k.population()), {
    "name": "Πίεση στέγασης από βραχυχρόνια μίσθωση",
    "unit": "ολόκληρα σπίτια Airbnb ανά 1.000 κατοίκους",
    "source": f"Inside Airbnb, Athens, στιγμιότυπο {SNAPSHOT}, CC BY 4.0",
    "note": "Μετρά όλες τις καταχωρίσεις ολόκληρου σπιτιού, και ανενεργές· οι θέσεις έχουν σκόπιμη μετατόπιση έως ~150 m.",
    "worse": "high",
}, decimals=1)
