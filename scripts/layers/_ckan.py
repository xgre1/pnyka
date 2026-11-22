"""Shared helpers for the City of Athens CKAN layers (and Inside Airbnb).

Everything is computed in EPSG:2100 (GGRS87 / Greek Grid, metres), the native CRS of
the City GeoServer layers. Neighbourhood polygons (WGS84) are projected with pyproj.

Downloads are cached in CKAN_CACHE; the GeoJSON resource URLs follow DATA.md.
Run:  <venv>/bin/python -I scripts/layers/<id>.py
"""
import csv
import json
import os
import subprocess

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.strtree import STRtree

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CACHE = os.environ.get(
    "CKAN_CACHE",
    "/tmp/pnyka-cache/"
    "2e591172-7062-49fa-a3ae-a59bf97042e7/scratchpad/ckan",
)
WFS = ("http://gis.cityofathens.gr/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature"
       "&typename=geonode%3A{layer}&outputFormat=json&srs=EPSG%3A2100&srsName=EPSG%3A2100")
CITY = "Δήμος Αθηναίων, opendata.cityofathens.gr"

_to2100 = Transformer.from_crs(4326, 2100, always_xy=True)
_to4326 = Transformer.from_crs(2100, 4326, always_xy=True)


def to2100(geom):
    return transform(lambda x, y, z=None: _to2100.transform(x, y), geom)


def to4326(geom):
    return transform(lambda x, y, z=None: _to4326.transform(x, y), geom)


def neighbourhoods():
    """[(name, polygon in EPSG:2100)] for the 144 neighbourhoods."""
    with open(os.path.join(REPO, "neighbourhoods.geojson")) as f:
        g = json.load(f)
    return [(ft["properties"]["name"], to2100(shape(ft["geometry"]))) for ft in g["features"]]


def population():
    with open(os.path.join(REPO, "raw", "population", "population_by_neighbourhood.csv")) as f:
        return {r["name"]: float(r["pop_total"]) for r in csv.DictReader(f)}


def fetch_layer(layer):
    """GeoJSON FeatureCollection (EPSG:2100) of a City GeoServer layer, cached."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, layer + ".geojson")
    for attempt in range(4):
        if os.path.exists(path) and os.path.getsize(path) > 100:
            try:
                with open(path) as f:
                    return json.load(f)
            except ValueError:
                os.remove(path)  # truncated download
        subprocess.run(["curl", "-s", "-m", "60", "-o", path, WFS.format(layer=layer)])
    raise RuntimeError("download failed: " + layer)


def points(layer, keep=None):
    """[(Point in EPSG:2100, properties)]; MultiPoint features use their first point."""
    out = []
    for ft in fetch_layer(layer)["features"]:
        if keep and not keep(ft["properties"]):
            continue
        geom = ft.get("geometry")
        if not geom:
            continue
        s = shape(geom)
        p = s.geoms[0] if s.geom_type == "MultiPoint" else s
        out.append((Point(p.x, p.y), ft["properties"]))
    return out


def assign(pts, nbs):
    """Count points per neighbourhood (smallest containing polygon). Returns (counts, outside)."""
    polys = [p for _, p in nbs]
    tree = STRtree(polys)
    counts = {n: 0.0 for n, _ in nbs}
    outside = 0
    for pt, weight in pts:
        hits = [i for i in tree.query(pt) if polys[i].covers(pt)]
        if not hits:
            outside += 1
            continue
        i = min(hits, key=lambda k: polys[k].area)
        counts[nbs[i][0]] += weight
    return counts, outside


def rep_point(poly):
    c = poly.centroid
    return c if poly.contains(c) else poly.representative_point()


def write(lid, values, meta, decimals=2):
    """values: {name: float}; meta: name, unit, source, note, worse."""
    d = os.path.join(REPO, "raw", "layers")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, lid + ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "value"])
        for n, v in values.items():
            w.writerow([n, round(v, decimals)])
    m = {"id": lid, "name": meta["name"], "unit": meta["unit"], "kind": "rec",
         "source": meta["source"], "note": meta.get("note", ""), "worse": meta["worse"]}
    with open(os.path.join(d, lid + ".json"), "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    vs = list(values.values())
    print(f"{lid}: rows={len(vs)} min={min(vs):.2f} max={max(vs):.2f} nonzero={sum(1 for v in vs if v)}")


MIN_AREA_KM2 = 0.04  # ΣΥΝΤΑΓΜΑ (0.017 km2) and ΒΟΥΛΗ (0.032): one point would read as 30-60 per km2


def per_km2(counts, nbs):
    area = {n: p.area / 1e6 for n, p in nbs}
    return {n: counts[n] / area[n] for n in counts if area[n] >= MIN_AREA_KM2}


MIN_POP = 200  # below this a per-resident rate is noise (ΣΥΝΤΑΓΜΑ 70, ΒΟΥΛΗ 117 residents)


def per_1000(counts, pop):
    return {n: 1000.0 * c / pop[n] for n, c in counts.items() if pop.get(n, 0) >= MIN_POP}


def nearest_distance(pts, nbs):
    """Metres from each neighbourhood's centroid (or an inside point) to the nearest point."""
    geoms = [p for p, _ in pts]
    tree = STRtree(geoms)
    out = {}
    for n, poly in nbs:
        rp = rep_point(poly)
        i = tree.nearest(rp)
        out[n] = rp.distance(geoms[i])
    return out


def area_share(zone_polys, nbs):
    """Percent of each neighbourhood's area covered by the union of zone_polys."""
    from shapely.ops import unary_union
    u = unary_union([z.buffer(0) for z in zone_polys])
    return {n: 100.0 * p.intersection(u).area / p.area for n, p in nbs}
