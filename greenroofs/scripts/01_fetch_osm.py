"""Fetch from OSM (Overpass) the candidate City of Athens buildings and amenities.

Run:  <venv>/bin/python -I greenroofs/scripts/01_fetch_osm.py
Cache: scripts/layers/_osm.py CACHE (env OSM_CACHE). Output: two cached Overpass JSON files.
The fetch is deliberately broad; 02_build.py decides what counts as City evidence.
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "layers"))
import _osm  # noqa: E402

# ---- parameters
# broad net on operator / owner tags (case-insensitive); strict filter in 02_build.py
NET_RE = "Αθην|Αθήν|ΑΘΗΝ|Athen|Δήμ|Δημ|ΔΗΜ|Munic|City"
TAGS = ["operator", "owner", "operator:el", "operator:en", "owner:el", "owner:en"]
AMENITY = "townhall|library|marketplace|community_centre|social_facility|theatre|arts_centre"

op_parts = "".join(f'nwr["{t}"~"{NET_RE}",i]({{bbox}});' for t in TAGS)
Q_OPERATOR = f"({op_parts});out tags geom center;"
Q_AMENITY = (f'(nwr["amenity"~"^({AMENITY})$"]({{bbox}});'
             'nwr["leisure"="sports_centre"]({bbox});'
             ');out tags geom center;')
# City evidence in the name (Δημοτική Βιβλιοθήκη, Δημαρχείο, ... Δήμου Αθηναίων)
Q_NAME = ('nwr["name"~"^Δημοτικ|^Δημαρχείο|Δήμου Αθηναίων"]({bbox});out tags geom center;')

if __name__ == "__main__":
    a = _osm.fetch("greenroofs_city_operator", Q_OPERATOR)
    b = _osm.fetch("greenroofs_city_amenities", Q_AMENITY)
    c = _osm.fetch("greenroofs_city_names", Q_NAME)
    print("operator/owner net:", len(a["elements"]))
    print("amenity/leisure net:", len(b["elements"]))
    print("name net:", len(c["elements"]))
