"""Candidate planting spots in the Municipality of Athens: streets, pedestrian streets, school yards.

CANDIDATES for a site visit, not a planting plan. Every assumption is a named parameter below.

Inputs
  OSM (planting/scripts/download.py, cached in the scratchpad): highways, amenity=school|kindergarten.
  Buildings: City of Athens solar-map footprints (raw/treecover/dl/cityg_c40solarmap.json.gz, 66,661
    footprints). Used instead of OSM buildings: Overpass timed out on every mirror for buildings, and the
    City layer is the official footprint set already used by capacity/ and roofs/.
  Canopy: Meta canopy height model raw/treecover/dl/meta_chm_athens.tif (pixel >= 3 m = canopy).
  Neighbourhoods: app/public/data/neighbourhoods.geojson (144 polygons, id + name).

Run: <venv>/bin/python -I planting/scripts/candidates.py
"""
import csv
import gzip
import json
import math
import os
import re
import sys

import numpy as np
import rasterio
import shapely
from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts", "layers"))
import _osm  # noqa: E402

REPO = _osm.REPO
OUT = os.path.join(REPO, "planting")

# ---------------------------------------------------------------- parameters
# Streets
STREET_CLASSES = {"primary", "secondary", "tertiary", "residential", "unclassified"}
MIN_WAY_LENGTH_M = 20.0          # drop OSM ways shorter than this (inside the Municipality)
CHUNK_M = 100.0                  # ways are cut into pieces of about this length
SAMPLE_SPACING_M = 20.0          # one perpendicular ray pair every 20 m
RAY_CAP_M = 30.0                 # ray length; no facade within 30 m = "open" side (park, square, plot)
MIN_VALID_SHARE = 0.5            # a side is measured only if >= half of its rays hit a facade cleanly
LANE_M = 3.0                     # per travel lane
PARKING_PARALLEL_M = 2.0         # per parking row, parallel
PARKING_ANGLED_M = 4.5           # per parking row, diagonal / perpendicular
CLASS_DEFAULT_CARRIAGEWAY_M = {  # used when there is no width and no lanes tag
    "primary": 12.0, "secondary": 9.0, "tertiary": 7.0, "residential": 6.0, "unclassified": 6.0,
    "living_street": 4.0, "pedestrian": 0.0,
}
# Parking rows assumed when OSM has no parking tag. The class defaults above already include them;
# when only `lanes` is tagged they are added on top. Only residential/unclassified: on the bigger
# classes we do not know, so we assume none (conservative for the parking-lane option).
UNTAGGED_PARKING_ROWS = {"residential": 1, "unclassified": 1}
LANES_FLOOR_TO_CLASS_DEFAULT = True  # lanes x 3 m never below the class default when parking is untagged
SENSITIVITY_SIDEWALK_M = (2.3, 2.8, 3.3, 3.8)  # printed only: sidewalk trees at other thresholds
MIN_SIDEWALK_FOR_TREE_M = 2.80   # ΥΑ ΥΠΕΝ/ΔΜΕΑΑΠ/124964/1561/2022 (ΦΕΚ 6213/Β/7-12-2022) and the 2009 text
SPACING_M = 8.0                  # street trees, one per 8 m per side
PARKING_TREE_SPACING_M = 8.0     # trees in the parking lane, one per 8 m on the parking side
PARKING_SPACES_PER_TREE = 1.0    # about one on-street space lost per tree
JUNCTION_CLEAR_M = 5.0           # no tree within 5 m of each way end (junction corners)
USABLE_LENGTH_SHARE = 1.0        # driveways, kiosks, bus stops, metro exits: NOT known, not applied
CANOPY_H_MIN_M = 3.0             # CHM pixel >= 3 m counts as tree canopy
CANOPY_OVERHANG_M = 2.0          # canopy over the last 2 m of carriageway counts for that side
SKIP_IF_CANOPY_SHARE = 0.5       # a side already >= 50 % shaded gets no new trees
# Pedestrian streets (highway=pedestrian lines, living_street) and pedestrian areas
PED_SPACING_M = 10.0
PED_MIN_WIDTH_M = 5.0            # 3.5 m clear for emergency vehicles + about 1.5 m for the tree zone
PED_TWO_ROWS_WIDTH_M = 8.0
PED_AREA_TREE_SHARE = 0.15       # squares (highway=pedestrian, area=yes): target canopy share
# School yards
YARD_TREE_SHARE = 0.15           # target canopy share of the yard
CROWN_M2 = 35.0                  # engine/params.csv trees_pavement crown_area_at_20y_m2, central
SCHOOL_MATCH_BUFFER_M = 15.0     # a sites.csv school point within 15 m of an OSM school polygon matches
NESTED_SHARE = 0.8               # a school polygon >= 80 % inside a bigger one is dropped (duplicate)
# App file
SIMPLIFY_M = 1.0

SCRATCH = os.path.dirname(_osm.CACHE)

# ---------------------------------------------------------------- helpers
R3857 = 6378137.0


def to_ll(x, y):
    return x / _osm.KX, y / _osm.KY


def geom_metric(g):
    return shapely.transform(g, lambda c: np.column_stack([c[:, 0] * _osm.KX, c[:, 1] * _osm.KY]))


def geom_ll(g, digits=None):
    g = shapely.transform(g, lambda c: np.column_stack([c[:, 0] / _osm.KX, c[:, 1] / _osm.KY]))
    if digits is not None:
        g = shapely.set_precision(g, 10 ** -digits)
    return g


class Canopy:
    def __init__(self, path):
        with rasterio.open(path) as src:
            self.a = src.read(1)
            self.left, self.top = src.bounds.left, src.bounds.top
            self.res = src.res[0]

    def is_canopy(self, x, y):
        """x, y local metres (arrays) -> bool array (False outside the raster)."""
        lon, lat = to_ll(np.asarray(x), np.asarray(y))
        X = R3857 * np.radians(lon)
        Y = R3857 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
        col = ((X - self.left) / self.res).astype(int)
        row = ((self.top - Y) / self.res).astype(int)
        ok = (row >= 0) & (row < self.a.shape[0]) & (col >= 0) & (col < self.a.shape[1])
        out = np.zeros(np.shape(x), bool)
        out[ok] = self.a[row[ok], col[ok]] >= CANOPY_H_MIN_M
        return out

    def share_in(self, poly, step=2.0):
        if poly.is_empty or poly.area < 1:
            return 0.0
        x0, y0, x1, y1 = poly.bounds
        xs, ys = np.meshgrid(np.arange(x0 + step / 2, x1, step), np.arange(y0 + step / 2, y1, step))
        xs, ys = xs.ravel(), ys.ravel()
        inside = shapely.contains_xy(poly, xs, ys)
        if inside.sum() == 0:
            return 0.0
        return float(self.is_canopy(xs[inside], ys[inside]).mean())


def num(v):
    if v is None:
        return None
    m = re.match(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*(m)?\s*$", str(v))
    return float(m.group(1).replace(",", ".")) if m else None


def parking_rows(tags):
    """(left_m, right_m, tagged) parking widths from parking:* / parking:lane:* tags."""
    w = {"left": 0.0, "right": 0.0}
    tagged = False
    for side in ("left", "right"):
        for key in (f"parking:{side}", "parking:both", f"parking:lane:{side}", "parking:lane:both"):
            v = tags.get(key)
            if v is None:
                continue
            tagged = True
            if v in ("no", "no_parking", "no_stopping", "separate", "fire_lane"):
                w[side] = 0.0
            else:
                orient = (tags.get(f"parking:{side}:orientation") or tags.get("parking:both:orientation") or v)
                w[side] = PARKING_ANGLED_M if orient in ("diagonal", "perpendicular") else PARKING_PARALLEL_M
            break
        r = tags.get(f"parking:{side}:restriction") or tags.get("parking:both:restriction")
        if r in ("no_stopping", "no_parking"):
            w[side] = 0.0
            tagged = True
    if tags.get("parking:lane") in ("no", "no_parking", "no_stopping"):
        tagged = True
    return w["left"], w["right"], tagged


def carriageway(tags, hw):
    """Returns (half_left_m, half_right_m, parking_left_m, parking_right_m, untagged_rows, source)."""
    pl, pr, ptag = parking_rows(tags)
    width = num(tags.get("width"))
    lanes = num(tags.get("lanes"))
    untagged = 0 if ptag else UNTAGGED_PARKING_ROWS.get(hw, 0)
    if width and 2.0 <= width <= 40.0:
        return width / 2, width / 2, pl, pr, untagged, "width"
    if lanes:
        if ptag:
            travel = lanes * LANE_M
            return travel / 2 + pl, travel / 2 + pr, pl, pr, 0, "lanes"
        # parking untagged: lanes alone miss the parked cars (Acharnon: lanes=2 but parking both
        # sides), so the class default is a floor
        cw = lanes * LANE_M + untagged * PARKING_PARALLEL_M
        if LANES_FLOOR_TO_CLASS_DEFAULT:
            cw = max(cw, CLASS_DEFAULT_CARRIAGEWAY_M.get(hw, 0.0))
        return cw / 2, cw / 2, pl, pr, untagged, "lanes"
    cw = CLASS_DEFAULT_CARRIAGEWAY_M.get(hw, 6.0)
    if ptag:  # tagged parking replaces the default row
        cw = cw - UNTAGGED_PARKING_ROWS.get(hw, 0) * PARKING_PARALLEL_M
        return cw / 2 + pl, cw / 2 + pr, pl, pr, 0, "default"
    return cw / 2, cw / 2, pl, pr, untagged, "default"


def chunks(line, size):
    n = max(1, int(round(line.length / size)))
    if n == 1:
        return [line]
    out = []
    for i in range(n):
        out.append(shapely.ops.substring(line, line.length * i / n, line.length * (i + 1) / n))
    return out


# ---------------------------------------------------------------- loading
def load_neighbourhoods():
    with open(os.path.join(REPO, "app/public/data/neighbourhoods.geojson")) as f:
        gj = json.load(f)
    ids, names, polys = [], [], []
    for ft in gj["features"]:
        g = shape(ft["geometry"])
        g = g if g.is_valid else g.buffer(0)
        ids.append(ft["properties"]["id"])
        names.append(ft["properties"]["name"])
        polys.append(geom_metric(g))
    return ids, names, polys


def load_buildings():
    with gzip.open(os.path.join(REPO, "raw/treecover/dl/cityg_c40solarmap.json.gz"), "rt", encoding="utf8") as f:
        feats = json.load(f)["features"]
    g = shapely.make_valid(np.array([shape(f["geometry"]) for f in feats], dtype=object))
    g = np.array([geom_metric(x) for x in g], dtype=object)
    return g[~shapely.is_empty(g)]


class NbIndex:
    def __init__(self, polys):
        self.polys = polys
        self.tree = shapely.STRtree(polys)

    def find(self, pt):
        idx = self.tree.query(pt, predicate="intersects")
        return int(idx[0]) if len(idx) else None


# ---------------------------------------------------------------- ray measurement
def measure(lines, way_ids, bld_tree, bld, road_tree, road_way_ids, canopy, half_l, half_r):
    """For each line: per side (left, right) median facade distance, valid share, canopy share.

    half_l / half_r: per line half carriageway on each side (canopy is sampled from half - overhang
    to the facade). Returns dict of arrays.
    """
    P, N, owner, side = [], [], [], []
    for i, ln in enumerate(lines):
        L = ln.length
        k = max(1, int(L // SAMPLE_SPACING_M))
        for j in range(k):
            d = (j + 0.5) * L / k
            a = ln.interpolate(max(0.0, d - 1.0))
            b = ln.interpolate(min(L, d + 1.0))
            tx, ty = b.x - a.x, b.y - a.y
            n = math.hypot(tx, ty) or 1.0
            p = ln.interpolate(d)
            for s, sgn in ((0, 1.0), (1, -1.0)):  # 0 = left of way direction, 1 = right
                P.append((p.x, p.y))
                N.append((-ty / n * sgn, tx / n * sgn))
                owner.append(i)
                side.append(s)
    P = np.array(P)
    N = np.array(N)
    owner = np.array(owner)
    side = np.array(side)
    ends = P + N * RAY_CAP_M
    rays = shapely.linestrings(np.stack([P, ends], axis=1))
    pts = shapely.points(P)
    nr = len(rays)
    # facade distance
    dist = np.full(nr, np.inf)
    ri, bi = bld_tree.query(rays, predicate="intersects")
    if len(ri):
        inter = shapely.intersection(rays[ri], bld[bi])
        dd = shapely.distance(pts[ri], inter)
        np.minimum.at(dist, ri, dd)
    # another road crossing the ray before the facade (dual carriageway, parallel road, square)
    rd = np.full(nr, np.inf)
    ri, wi = road_tree.query(rays, predicate="intersects")
    if len(ri):
        keep = road_way_ids[wi] != way_ids[owner[ri]]
        ri, wi = ri[keep], wi[keep]
        dd = shapely.distance(pts[ri], shapely.intersection(rays[ri], road_tree.geometries[wi]))
        dd = np.where(dd < 0.5, np.inf, dd)  # touching at the sample point = junction node, ignore
        np.minimum.at(rd, ri, dd)
    inside = dist < 1.0          # sample point inside a footprint (arcade, mapped-over street)
    hit = np.isfinite(dist) & ~inside & (dist < rd)
    road_first = np.isfinite(rd) & (rd < dist)
    # canopy along each ray, 1 m steps, from (half carriageway - overhang) to the facade (or cap)
    half = np.where(side == 0, half_l[owner], half_r[owner])
    stop = np.where(hit, dist, np.minimum(rd, RAY_CAP_M))
    offs = np.arange(0.5, RAY_CAP_M, 1.0)
    X = P[:, :1] + N[:, :1] * offs
    Y = P[:, 1:] + N[:, 1:] * offs
    use = (offs[None, :] >= np.maximum(0, half - CANOPY_OVERHANG_M)[:, None]) & (offs[None, :] <= stop[:, None])
    can = canopy.is_canopy(X, Y) & use
    nl = len(lines)
    res = {}
    grp = owner * 2 + side
    ng = nl * 2
    n = np.maximum(np.bincount(grp, minlength=ng), 1)
    valid = np.bincount(grp, weights=hit, minlength=ng) / n
    openshare = np.bincount(grp, weights=~np.isfinite(dist) & ~road_first, minlength=ng) / n
    roadshare = np.bincount(grp, weights=road_first, minlength=ng) / n
    u = np.bincount(grp, weights=use.sum(1), minlength=ng)
    cshare = np.bincount(grp, weights=can.sum(1), minlength=ng) / np.maximum(u, 1)
    med = np.full(ng, np.nan)
    hg, hd = grp[hit], dist[hit]
    order = np.lexsort((hd, hg))
    hg, hd = hg[order], hd[order]
    starts = np.searchsorted(hg, np.arange(ng), side="left")
    stops = np.searchsorted(hg, np.arange(ng), side="right")
    for gi in np.nonzero(stops > starts)[0]:
        med[gi] = float(np.median(hd[starts[gi]:stops[gi]]))
    for s, tag in ((0, "l"), (1, "r")):
        res["facade_" + tag] = med[s::2]
        res["valid_" + tag] = valid[s::2]
        res["open_" + tag] = openshare[s::2]
        res["road_" + tag] = roadshare[s::2]
        res["canopy_" + tag] = cshare[s::2]
    return res


# ---------------------------------------------------------------- main
def main():
    print("loading", flush=True)
    nb_ids, nb_names, nb_polys = load_neighbourhoods()
    nbx = NbIndex(nb_polys)
    city = unary_union(nb_polys)
    bld = load_buildings()
    bld_tree = shapely.STRtree(bld)
    canopy = Canopy(os.path.join(REPO, "raw/treecover/dl/meta_chm_athens.tif"))
    with open(os.path.join(_osm.CACHE, "planting_streets.json")) as f:
        ways = json.load(f)["elements"]
    print(f"buildings {len(bld)}, OSM highway ways {len(ways)}", flush=True)

    # all road lines (for the parallel-road check), clipped nothing
    road_geoms, road_ids = [], []
    for w in ways:
        g = w.get("geometry") or []
        if len(g) >= 2 and w["tags"].get("area") != "yes":
            road_geoms.append(geom_metric(LineString([(p["lon"], p["lat"]) for p in g])))
            road_ids.append(w["id"])
    road_tree = shapely.STRtree(road_geoms)
    road_ids = np.array(road_ids)

    # ---- pieces for streets and pedestrian lines
    pieces = []  # dict per chunk
    ped_areas = []
    for w in ways:
        t = w["tags"]
        hw = t["highway"]
        g = w.get("geometry") or []
        if len(g) < 2:
            continue
        if hw == "pedestrian" and t.get("area") == "yes":
            if len(g) >= 4:
                ped_areas.append((w, geom_metric(Polygon([(p["lon"], p["lat"]) for p in g]).buffer(0))))
            continue
        kind = "street" if hw in STREET_CLASSES else ("pedestrian" if hw in ("pedestrian", "living_street") else None)
        if kind is None:
            continue
        if t.get("tunnel") not in (None, "no") or t.get("bridge") not in (None, "no") or t.get("covered") == "yes":
            continue
        ln = geom_metric(LineString([(p["lon"], p["lat"]) for p in g])).intersection(city)
        parts = [ln] if ln.geom_type == "LineString" else [x for x in getattr(ln, "geoms", []) if x.geom_type == "LineString"]
        wl = sum(p.length for p in parts)
        if wl < MIN_WAY_LENGTH_M:
            continue
        hl, hr, pl, pr, untagged, src = carriageway(t, hw) if kind == "street" else (0, 0, 0, 0, 0, "-")
        if kind == "pedestrian" and hw == "living_street":
            # living streets keep a narrow carriageway; trees go in one row along it
            hl = hr = 0.0
        eff = max(0.0, wl - 2 * JUNCTION_CLEAR_M) / wl * USABLE_LENGTH_SHARE
        for part in parts:
            for c in chunks(part, CHUNK_M):
                if c.length < 1:
                    continue
                pieces.append(dict(way=w["id"], kind=kind, hw=hw, name=t.get("name", ""), line=c,
                                   hl=hl, hr=hr, pl=pl, pr=pr, untagged=untagged, cw_src=src,
                                   eff_len=c.length * eff, width_tag=num(t.get("width"))))
    print(f"pieces {len(pieces)}, pedestrian areas {len(ped_areas)}", flush=True)

    m = measure([p["line"] for p in pieces], np.array([p["way"] for p in pieces]), bld_tree, bld,
                road_tree, road_ids, canopy, np.array([p["hl"] for p in pieces]),
                np.array([p["hr"] for p in pieces]))

    streets, peds = [], []
    for i, p in enumerate(pieces):
        mid = p["line"].interpolate(0.5, normalized=True)
        k = nbx.find(mid)
        if k is None:
            continue
        fl, fr = m["facade_l"][i], m["facade_r"][i]
        okl = m["valid_l"][i] >= MIN_VALID_SHARE
        okr = m["valid_r"][i] >= MIN_VALID_SHARE
        cl, cr = m["canopy_l"][i], m["canopy_r"][i]
        rec = dict(name=p["name"], highway=p["hw"], nb_id=nb_ids[k], nb_name=nb_names[k],
                   length_m=round(p["line"].length, 1), line=p["line"])
        if p["kind"] == "street":
            swl = fl - p["hl"] if okl else None
            swr = fr - p["hr"] if okr else None
            corridor = fl + fr if (okl and okr) else None
            trees = 0
            sides = 0
            side_ok = []
            for sw, cs in ((swl, cl), (swr, cr)):
                plant = sw is not None and sw >= MIN_SIDEWALK_FOR_TREE_M and cs < SKIP_IF_CANOPY_SHARE
                side_ok.append(plant)
                if plant:
                    sides += 1
                    trees += int(math.floor(p["eff_len"] / SPACING_M * (1 - cs)))
            # parking-lane option: sides that are measured, NOT plantable on the sidewalk, have parking
            tp = 0
            n_park_sides = 0
            cand = []
            for s, (sw, cs, pw) in enumerate(((swl, cl, p["pl"]), (swr, cr, p["pr"]))):
                if sw is not None and sw >= 0 and not side_ok[s] and cs < SKIP_IF_CANOPY_SHARE:
                    cand.append((s, cs, pw))
            tagged_sides = [c for c in cand if c[2] > 0]
            if tagged_sides:
                use = tagged_sides
            elif p["untagged"] > 0 and cand:
                use = cand[:p["untagged"]]  # one assumed row: count one side only
            else:
                use = []
            for s, cs, _ in use:
                n_park_sides += 1
                tp += int(math.floor(p["eff_len"] / PARKING_TREE_SPACING_M * (1 - cs)))
            meas = [c for c, ok in ((cl, okl), (cr, okr)) if ok]
            rec.update(corridor_m=None if corridor is None else round(corridor, 1),
                       carriageway_m=round(p["hl"] + p["hr"], 1), carriageway_src=p["cw_src"],
                       sidewalk_left_m=None if swl is None else round(swl, 1),
                       sidewalk_right_m=None if swr is None else round(swr, 1),
                       sidewalk_m=None if not [x for x in (swl, swr) if x is not None] else
                       round(float(np.mean([x for x in (swl, swr) if x is not None])), 1),
                       side_status="/".join(
                           "ok" if ok else ("road" if m["road_" + t][i] > m["open_" + t][i] else "open")
                           for ok, t in ((okl, "l"), (okr, "r"))),
                       sides=sides, trees=trees, trees_parking=tp, parking_sides=n_park_sides,
                       parking_spaces_lost=int(round(tp * PARKING_SPACES_PER_TREE)),
                       canopy_now_pct=round(100 * float(np.mean(meas)) if meas else 100 * (cl + cr) / 2, 1),
                       _sides=[(swl, cl), (swr, cr)], _eff=p["eff_len"])
            streets.append(rec)
        else:
            if p["width_tag"]:
                width = p["width_tag"]
            else:
                width = (fl if okl else RAY_CAP_M) + (fr if okr else RAY_CAP_M)
            rows = 0 if width < PED_MIN_WIDTH_M else (2 if width >= PED_TWO_ROWS_WIDTH_M else 1)
            cs = (cl + cr) / 2
            trees = 0 if cs >= SKIP_IF_CANOPY_SHARE else int(math.floor(p["eff_len"] / PED_SPACING_M * rows * (1 - cs)))
            rec.update(width_m=round(width, 1), width_src="osm" if p["width_tag"] else "facades",
                       rows=rows, trees=trees, canopy_now_pct=round(100 * cs, 1))
            peds.append(rec)

    # pedestrian areas (squares)
    for w, poly in ped_areas:
        if poly.is_empty:
            continue
        poly = poly.intersection(city)
        if poly.area < 50:
            continue
        k = nbx.find(poly.representative_point())
        if k is None:
            continue
        free = poly.difference(unary_union(bld[bld_tree.query(poly, predicate="intersects")]))
        cs = canopy.share_in(free)
        trees = int(math.floor(free.area * max(0.0, PED_AREA_TREE_SHARE - cs) / CROWN_M2))
        peds.append(dict(name=w["tags"].get("name", ""), highway="pedestrian_area", nb_id=nb_ids[k],
                         nb_name=nb_names[k], length_m=None, area_m2=round(free.area), width_m=None,
                         width_src="-", rows=None, trees=trees, canopy_now_pct=round(100 * cs, 1), line=free))
    # drop pedestrian lines inside a pedestrian area (counted by the area)
    areas = [r["line"] for r in peds if r["highway"] == "pedestrian_area"]
    if areas:
        at = shapely.STRtree(areas)
        peds = [r for r in peds if r["highway"] == "pedestrian_area" or
                not len(at.query(r["line"].interpolate(0.5, normalized=True), predicate="within"))]

    yards, n_sch_matched, n_nur_matched = school_yards(nbx, nb_ids, nb_names, city, bld, bld_tree, canopy)

    write_outputs(streets, peds, yards, nb_ids, nb_names)
    validation(streets, peds)
    tot_s = sum(r["trees"] for r in streets)
    tot_p = sum(r["trees_parking"] for r in streets)
    tot_ped = sum(r["trees"] for r in peds)
    tot_y = sum(r["trees"] for r in yards)
    stat = {}
    for r in streets:
        stat[r["side_status"]] = stat.get(r["side_status"], 0) + r["length_m"]
    print("street km by side status (left/right):",
          {k: round(v / 1000, 1) for k, v in sorted(stat.items(), key=lambda x: -x[1])})
    print("carriageway source km:", {s: round(sum(r["length_m"] for r in streets if r["carriageway_src"] == s) / 1000, 1)
                                     for s in ("width", "lanes", "default")})
    print(f"TOTAL streets(sidewalk) {tot_s}  streets(parking lane) {tot_p} (spaces lost {sum(r['parking_spaces_lost'] for r in streets)})"
          f"  pedestrian {tot_ped}  yards {tot_y}")
    print(f"plantable street km {sum(r['length_m'] for r in streets if r['sides'] > 0) / 1000:.1f} of {sum(r['length_m'] for r in streets) / 1000:.1f}")
    print(f"schools matched {n_sch_matched}/397, nurseries matched {n_nur_matched}/72")
    for thr in SENSITIVITY_SIDEWALK_M:
        t = sum(int(math.floor(r["_eff"] / SPACING_M * (1 - cs))) for r in streets for sw, cs in r["_sides"]
                if sw is not None and sw >= thr and cs < SKIP_IF_CANOPY_SHARE)
        print(f"sensitivity: sidewalk threshold {thr} m -> {t} sidewalk trees")


def school_yards(nbx, nb_ids, nb_names, city, bld, bld_tree, canopy):
    with open(os.path.join(_osm.CACHE, "planting_schools.json")) as f:
        els = json.load(f)["elements"]
    polys = []
    for el in els:
        g = None
        if el["type"] == "way":
            c = el.get("geometry") or []
            if len(c) >= 4 and (c[0]["lon"], c[0]["lat"]) == (c[-1]["lon"], c[-1]["lat"]):
                g = Polygon([(p["lon"], p["lat"]) for p in c]).buffer(0)
        elif el["type"] == "relation":
            data = {"elements": [el]}
            pp = _osm.area_polygons(data)  # already metric
            if pp:
                polys.append((el, pp[0]))
            continue
        if g is not None:
            polys.append((el, geom_metric(g)))
    polys = [(el, g.intersection(city)) for el, g in polys]
    polys = [(el, g) for el, g in polys if g.area > 20]
    polys.sort(key=lambda x: -x[1].area)
    kept = []
    for el, g in polys:
        if any(g.intersection(k).area >= NESTED_SHARE * g.area for _, k in kept):
            continue
        kept.append((el, g))
    # our schools
    sites = []
    with open(os.path.join(REPO, "streets/sites.csv")) as f:
        for row_i, r in enumerate(csv.DictReader(f)):
            if r["site_type"] in ("school", "nursery"):
                x, y = _osm.proj(float(r["lon"]), float(r["lat"]))
                sites.append((row_i, r["site_type"], r["name"], shapely.Point(x, y)))
    st = shapely.STRtree([s[3] for s in sites])
    out = []
    matched = set()
    for el, g in kept:
        idx = st.query(g.buffer(SCHOOL_MATCH_BUFFER_M), predicate="intersects")
        m = [sites[i] for i in idx]
        matched.update(s[0] for s in m)
        bi = bld_tree.query(g, predicate="intersects")
        yard = g.difference(unary_union(bld[bi])) if len(bi) else g
        cs = canopy.share_in(yard)
        trees = int(math.floor(yard.area * max(0.0, YARD_TREE_SHARE - cs) / CROWN_M2))
        k = nbx.find(g.representative_point())
        if k is None or trees < 1:
            continue
        out.append(dict(name=el["tags"].get("name", ""), amenity=el["tags"].get("amenity"),
                        nb_id=nb_ids[k], nb_name=nb_names[k], area_m2=round(g.area), yard_m2=round(yard.area),
                        canopy_now_pct=round(100 * cs, 1), trees=trees,
                        matched_school_id=";".join(f"sites.csv:{s[0]}" for s in m if s[1] == "school") or None,
                        matched_nursery_id=";".join(f"sites.csv:{s[0]}" for s in m if s[1] == "nursery") or None,
                        matched_names=";".join(s[2] for s in m) or None, line=yard))
    n_s = len({s[0] for s in sites if s[1] == "school" and s[0] in matched})
    n_n = len({s[0] for s in sites if s[1] == "nursery" and s[0] in matched})
    print(f"school polygons: {len(polys)} (after nested-dedupe {len(kept)}), with >=1 tree {len(out)}")
    return out, n_s, n_n


def feature(r, digits=None, simplify=None, props=None):
    g = r["line"]
    if simplify:
        g = g.simplify(simplify)
    g = geom_ll(g, digits)
    p = {k: v for k, v in r.items() if k != "line" and not k.startswith("_")} if props is None else {k: r.get(k) for k in props}
    return {"type": "Feature", "geometry": mapping(g), "properties": p}


def dump(path, feats, digits=None):
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, REPO)}: {len(feats)} features, {os.path.getsize(path) / 1e6:.2f} MB")


def write_outputs(streets, peds, yards, nb_ids, nb_names):
    os.makedirs(OUT, exist_ok=True)
    # full street table (all measured pieces) goes to the scratchpad for checking
    dump(os.path.join(SCRATCH, "planting_streets_all.geojson"), [feature(r, 6) for r in streets])
    cs = [r for r in streets if r["trees"] > 0 or r["trees_parking"] > 0]
    dump(os.path.join(OUT, "candidates_streets.geojson"), [feature(r, 6) for r in cs])
    cp = [r for r in peds if r["trees"] > 0]
    dump(os.path.join(OUT, "candidates_pedestrian.geojson"), [feature(r, 6) for r in cp])
    dump(os.path.join(OUT, "candidates_schoolyards.geojson"), [feature(r, 6) for r in yards])
    app = []
    for r in cs:
        f = feature(r, 5, SIMPLIFY_M, ["name", "nb_id", "trees", "trees_parking", "sidewalk_m"])
        f["properties"]["type"] = "street"
        app.append(f)
    for r in cp:
        f = feature(r, 5, SIMPLIFY_M, ["name", "nb_id", "trees"])
        f["properties"]["type"] = "pedestrian"
        app.append(f)
    for r in yards:
        f = feature(r, 5, SIMPLIFY_M, ["name", "nb_id", "trees", "yard_m2"])
        f["properties"]["type"] = "yard"
        app.append(f)
    dump(os.path.join(OUT, "app_candidates.geojson"), app, 5)
    agg = {i: dict(trees_streets=0, trees_streets_parking=0, trees_pedestrian=0, trees_yards=0,
                   street_km_plantable=0.0) for i in nb_ids}
    for r in streets:
        a = agg[r["nb_id"]]
        a["trees_streets"] += r["trees"]
        a["trees_streets_parking"] += r["trees_parking"]
        if r["sides"] > 0:
            a["street_km_plantable"] += r["length_m"] / 1000
    for r in peds:
        agg[r["nb_id"]]["trees_pedestrian"] += r["trees"]
    for r in yards:
        agg[r["nb_id"]]["trees_yards"] += r["trees"]
    with open(os.path.join(OUT, "candidates_by_neighbourhood.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "trees_streets", "trees_streets_parking", "trees_pedestrian", "trees_yards",
                    "trees_total", "street_km_plantable"])
        for i, n in sorted(zip(nb_ids, nb_names)):
            a = agg[i]
            tot = a["trees_streets"] + a["trees_pedestrian"] + a["trees_yards"]
            w.writerow([i, n, a["trees_streets"], a["trees_streets_parking"], a["trees_pedestrian"],
                        a["trees_yards"], tot, round(a["street_km_plantable"], 2)])
    have = sum(1 for i in nb_ids if agg[i]["trees_streets"] + agg[i]["trees_pedestrian"] + agg[i]["trees_yards"] > 0)
    have_p = sum(1 for i in nb_ids if sum(v for k, v in agg[i].items() if k.startswith("trees")) > 0)
    print(f"neighbourhoods with any candidate: {have}/144 (incl. parking-lane option {have_p}/144)")


# Validation: (label, OSM name, optional lon/lat bbox to pick the right street)
VALIDATION = [
    ("Πανεπιστημίου", "Πανεπιστημίου", None),
    ("Πατησίων (28ης Οκτωβρίου)", "Πατησίων", None),
    ("Αχαρνών", "Αχαρνών", None),
    ("Ακαδημίας", "Ακαδημίας", None),
    ("Φωκίωνος Νέγρη", "Φωκίωνος Νέγρη", None),
    ("Σκουφά", "Σκουφά", None),
    ("Αδριανού (Πλάκα)", "Αδριανού", None),
    ("Κυψέλης", "Κυψέλης", None),
    ("Ιουλιανού", "Ιουλιανού", None),
    ("Μιχαήλ Βόδα", "Μιχαήλ Βόδα", None),
]


def validation(streets, peds):
    rows = []
    for label, nm, bb in VALIDATION:
        sel = []
        for r in streets + peds:
            if r["name"] != nm:
                continue
            if bb:
                c = geom_ll(r["line"].centroid)
                if not (bb[0] <= c.x <= bb[2] and bb[1] <= c.y <= bb[3]):
                    continue
            sel.append(r)
        if not sel:
            rows.append([label, "not in OSM as a street of these classes"])
            continue
        L = sum(r["length_m"] or 0 for r in sel)

        def wmed(key):
            v = [(r[key], r["length_m"]) for r in sel if r.get(key) is not None]
            if not v:
                return None
            v.sort()
            tot = sum(w for _, w in v)
            acc = 0
            for x, w in v:
                acc += w
                if acc >= tot / 2:
                    return x
        hws = sorted({r["highway"] for r in sel})
        st = [r for r in sel if "sides" in r]
        plant_km = sum(r["length_m"] for r in st if r["sides"] > 0) / 1000
        rows.append([label, f"{'/'.join(hws)}", f"{L / 1000:.2f} km", f"corridor {wmed('corridor_m')}",
                     f"carriageway {wmed('carriageway_m')}", f"sidewalk L {wmed('sidewalk_left_m')} R {wmed('sidewalk_right_m')}",
                     f"ped width {wmed('width_m')}", f"plantable km {plant_km:.2f}",
                     f"trees {sum(r['trees'] for r in sel)}", f"parking-lane trees {sum(r.get('trees_parking', 0) for r in sel)}",
                     f"canopy {sum(r['canopy_now_pct'] * (r['length_m'] or 0) for r in sel) / max(L, 1):.1f}% (length-weighted mean)"])
    with open(os.path.join(SCRATCH, "planting_validation.txt"), "w") as f:
        for r in rows:
            line = " | ".join(str(x) for x in r)
            print(line)
            f.write(line + "\n")


if __name__ == "__main__":
    main()
