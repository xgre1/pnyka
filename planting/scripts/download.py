"""Download the OSM inputs for the planting candidates (cached in the scratchpad).

Run: <venv>/bin/python -I planting/scripts/download.py
Inputs land in $OSM_CACHE (default: the scratchpad osm/ folder used by scripts/layers/_osm.py).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts", "layers"))
import _osm  # noqa: E402

# Buildings are split into tiles so each Overpass call stays under the curl timeout.
LAT = [37.94, 37.965, 37.99, 38.015, 38.04]
LON = [23.68, 23.72, 23.76, 23.80]

STREETS_Q = ('way["highway"~"^(primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|'
             'residential|unclassified|living_street|pedestrian|trunk|trunk_link)$"]({bbox}); out geom;')
SCHOOLS_Q = 'nwr["amenity"~"^(school|kindergarten)$"]({bbox}); out geom;'


def main():
    d = _osm.fetch("planting_streets", STREETS_Q)
    print("streets", len(d["elements"]))
    d = _osm.fetch("planting_schools", SCHOOLS_Q)
    print("schools", len(d["elements"]))
    for i in range(len(LAT) - 1):
        for j in range(len(LON) - 1):
            bb = f"{LAT[i]},{LON[j]},{LAT[i + 1]},{LON[j + 1]}"
            d = _osm.fetch(f"planting_buildings_{i}{j}",
                           f'(way["building"]({bb}); relation["building"]({bb}););out geom;')
            print("buildings tile", i, j, len(d["elements"]), flush=True)


if __name__ == "__main__":
    main()
