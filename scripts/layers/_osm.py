"""Shared helpers for the OSM layers: Overpass download (cached), neighbourhood
polygons in a local metric projection, point-in-polygon, line clipping, output.

Run any layer script with the shapely venv:  python -I scripts/layers/<id>.py
"""
import csv
import json
import math
import os
import sys
import time
import subprocess
import urllib.parse

from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CACHE = os.environ.get(
    "OSM_CACHE",
    "/tmp/pnyka-cache/"
    "2e591172-7062-49fa-a3ae-a59bf97042e7/scratchpad/osm",
)
BBOX = "37.94,23.68,38.04,23.80"
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
SOURCE = "OpenStreetMap, Νοέμβριος 2026, ODbL"

LAT0 = 37.98
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110540.0


def proj(x, y, z=None):
    """lon/lat degrees -> local metres (error well under 1% over the Municipality)."""
    return (x * KX, y * KY)


def fetch(key, body):
    """body is Overpass QL without the [out:json] header; write {bbox} for the bbox."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, key + ".json")
    if os.path.exists(path) and os.path.getsize(path) > 100:
        with open(path) as f:
            return json.load(f)
    q = "[out:json][timeout:180];" + body.replace("{bbox}", BBOX)
    last = None
    for attempt in range(16):
        ep = ENDPOINTS[attempt % len(ENDPOINTS)]
        url = ep + "?data=" + urllib.parse.quote(q)
        # curl, not urllib: the venv's OpenSSL fails the TLS handshake with overpass-api.de
        r = subprocess.run(["curl", "-s", "-m", "100", "-A", "tr2-apps4athens-hackathon/1.0", url],
                           capture_output=True)
        try:
            data = json.loads(r.stdout)
            if "elements" not in data:
                raise ValueError("no elements")
            with open(path, "wb") as f:
                f.write(r.stdout)
            return data
        except Exception:  # 429/502/504 HTML pages, timeouts
            last = f"curl exit {r.returncode}, {r.stdout[:80]!r}"
            print(f"  {key}: {ep} failed ({last}); retry {attempt + 1}", file=sys.stderr, flush=True)
            time.sleep(min(5 * (attempt + 1), 30))
    raise RuntimeError(f"Overpass failed for {key}: {last}")


def neighbourhoods():
    """Returns ([(name, metric polygon)], {name: pop_total})."""
    with open(os.path.join(REPO, "neighbourhoods.geojson")) as f:
        gj = json.load(f)
    out = []
    for ft in gj["features"]:
        g = shape(ft["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        out.append((ft["properties"]["name"], transform(proj, g)))
    pop = {}
    with open(os.path.join(REPO, "raw/population/population_by_neighbourhood.csv")) as f:
        for row in csv.DictReader(f):
            try:
                pop[row["name"]] = float(row["pop_total"])
            except (ValueError, KeyError, TypeError):
                pass
    return out, pop


def element_points(data):
    """Metric points: nodes as is, ways/relations by their centre (use `out center`)."""
    pts = []
    for el in data["elements"]:
        if el["type"] == "node":
            pts.append((el["lon"], el["lat"]))
        elif "center" in el:
            pts.append((el["center"]["lon"], el["center"]["lat"]))
    return [Point(proj(*p)) for p in dict.fromkeys(pts)]


def count_points(polys, pts):
    """{name: count}; each point counted once (first polygon that contains it)."""
    tree = STRtree([p for _, p in polys])
    counts = {n: 0 for n, _ in polys}
    for pt in pts:
        for i in tree.query(pt, predicate="intersects"):
            counts[polys[i][0]] += 1
            break
    return counts


def way_lines(data):
    lines = []
    for el in data["elements"]:
        if el["type"] == "way" and len(el.get("geometry") or []) >= 2:
            lines.append(LineString([proj(p["lon"], p["lat"]) for p in el["geometry"]]))
    return lines


def length_km(polys, lines):
    """{name: km of lines inside}."""
    tree = STRtree(lines)
    out = {}
    for n, poly in polys:
        idx = tree.query(poly, predicate="intersects")
        out[n] = sum(lines[i].intersection(poly).length for i in idx) / 1000.0
    return out


def area_polygons(data):
    """Metric polygons from closed ways and multipolygon relations (`out geom`)."""
    polys = []
    for el in data["elements"]:
        if el["type"] == "way":
            g = el.get("geometry") or []
            if len(g) >= 4 and (g[0]["lon"], g[0]["lat"]) == (g[-1]["lon"], g[-1]["lat"]):
                polys.append(Polygon([proj(p["lon"], p["lat"]) for p in g]).buffer(0))
        elif el["type"] == "relation":
            outers, inners = [], []
            for m in el.get("members", []):
                g = m.get("geometry") or []
                if m.get("type") == "way" and len(g) >= 4 and (g[0]["lon"], g[0]["lat"]) == (g[-1]["lon"], g[-1]["lat"]):
                    p = Polygon([proj(q["lon"], q["lat"]) for q in g]).buffer(0)
                    (inners if m.get("role") == "inner" else outers).append(p)
            if outers:
                g = unary_union(outers)
                if inners:
                    g = g.difference(unary_union(inners))
                polys.append(g)
    return polys


def write_layer(id_, meta, values, digits=2):
    os.makedirs(os.path.join(REPO, "raw/layers"), exist_ok=True)
    with open(os.path.join(REPO, "raw/layers", id_ + ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for n in sorted(values):
            w.writerow([n, round(values[n], digits)])
    full = {"id": id_, "name": meta["name"], "unit": meta["unit"], "kind": "rec",
            "source": meta.get("source", SOURCE), "note": meta.get("note", ""),
            "worse": meta["worse"]}
    with open(os.path.join(REPO, "raw/layers", id_ + ".json"), "w") as f:
        json.dump(full, f, ensure_ascii=False, indent=1)
        f.write("\n")
    vs = list(values.values())
    print(f"{id_}: wrote {len(vs)} rows, min {min(vs):.3f}, max {max(vs):.3f}")


def per_km2(polys, counts):
    return {n: counts[n] / (p.area / 1e6) for n, p in polys if p.area > 0}


def per_1000(polys, counts, pop):
    """Leaves out neighbourhoods without a population figure or with < 50 residents."""
    return {n: counts[n] / pop[n] * 1000 for n, _ in polys if pop.get(n, 0) >= 50}


def municipality_total(counts):
    return sum(counts.values())
