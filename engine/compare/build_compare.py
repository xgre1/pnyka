#!/usr/bin/env python3
"""Actual plantings vs the same number of trees placed in order of need.

Python standard library only, no network, deterministic.
Usage: python3 -I engine/compare/build_compare.py [--out DIR]
Writes actual_vs_need.json, actual_vs_need.csv, SUMMARY.md into DIR
(default: the folder of this script). See README.md for every definition.
"""
import csv
import hashlib
import json
import math
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

SRC = OrderedDict([
    ("plantings_points", "athenstrees/plantings_points.csv"),
    ("neighbourhoods", "neighbourhoods.geojson"),
    ("population", "raw/population/population_by_neighbourhood.csv"),
    ("treecover", "treecover/treecover_by_neighbourhood.csv"),
    ("sites", "streets/sites_with_plantings.csv"),
    ("packages", "engine/packages.csv"),
])

BARE_THRESHOLD = 2.0
GROVE_IDS = ("2216", "2218")
SCHOOL_CANOPY_LT = 5.0
SCHOOL_RADIUS_M = 150.0
YEARS = ("2024", "2025", "2026")


def p(rel):
    return os.path.join(ROOT, rel)


def read_csv(rel):
    with open(p(rel), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- geometry
def ring_contains(ring, x, y):
    """Ray casting: cast a ray to +x, count edge crossings."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y):
            xc = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xc:
                inside = not inside
        j = i
    return inside


def polygon_contains(poly, x, y):
    """poly = [outer, hole1, ...]; inside outer and outside every hole."""
    if not ring_contains(poly[0], x, y):
        return False
    for hole in poly[1:]:
        if ring_contains(hole, x, y):
            return False
    return True


def load_shapes():
    with open(p(SRC["neighbourhoods"]), encoding="utf-8") as f:
        g = json.load(f)
    shapes = []
    for ft in g["features"]:
        geom = ft["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        xs = [pt[0] for pl in polys for pt in pl[0]]
        ys = [pt[1] for pl in polys for pt in pl[0]]
        shapes.append((ft["properties"]["name"], polys, (min(xs), min(ys), max(xs), max(ys))))
    return shapes


def locate(shapes, lon, lat):
    """Return (name or None, number of matching neighbourhoods). First match in file order wins."""
    hits = []
    for name, polys, (x0, y0, x1, y1) in shapes:
        if lon < x0 or lon > x1 or lat < y0 or lat > y1:
            continue
        for pl in polys:
            if polygon_contains(pl, lon, lat):
                hits.append(name)
                break
    return (hits[0] if hits else None), len(hits)


def dist_m(lat1, lon1, lat2, lon2):
    r = 6371008.8
    a1, a2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    dp = a2 - a1
    h = math.sin(dp / 2) ** 2 + math.cos(a1) * math.cos(a2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- load
def load_all():
    shapes = load_shapes()
    names = [s[0] for s in shapes]
    pop = {r["name"]: r for r in read_csv(SRC["population"])}
    cover = {r["neighbourhood"]: float(r["ua_stl2018_pct"]) for r in read_csv(SRC["treecover"])}
    nb = OrderedDict()
    for n in names:
        nb[n] = {
            "cover": cover[n],
            "pop": float(pop[n]["pop_total"]),
            "p65": float(pop[n]["pop_65plus"]),
            "p014": float(pop[n]["pop_0_14"]),
            "bare": cover[n] < BARE_THRESHOLD,
        }
    pts = []
    multi = 0
    for r in read_csv(SRC["plantings_points"]):
        lat, lon = float(r["lat"]), float(r["lon"])
        nm, k = locate(shapes, lon, lat)
        if k > 1:
            multi += 1
        pts.append({
            "id": r["planting_id"], "date": r["planting_date"], "year": r["planting_date"][:4],
            "trees": int(r["num_trees"]), "lat": lat, "lon": lon, "nb": nm,
        })
    sites = [r for r in read_csv(SRC["sites"]) if r["site_type"] == "school"]
    pk = [r for r in read_csv(SRC["packages"]) if r["intervention_id"] == "trees_pavement"]
    pk.sort(key=lambda r: int(r["rank_within_intervention"]))
    return nb, pts, sites, pk, multi


# ---------------------------------------------------------------- allocation
def walk(order, N):
    """order: list of (name, qty_central, cost_central).
    Returns (by_nb, cost, packages_used, last_fraction)."""
    left = N
    by = {}
    cost = 0.0
    used = 0
    frac = 1.0
    for name, q, c in order:
        if left <= 0:
            break
        take = min(q, left)
        by[name] = take
        cost += c * (take / q)
        left -= take
        used += 1
        frac = take / q
    if left > 0:
        raise ValueError("packages cannot absorb N: %d trees left" % left)
    return by, cost, used, frac


def to_order(rows):
    return [(r["neighbourhood"], int(float(r["quantity_central"])), float(r["cost_central_eur"])) for r in rows]


def pk_order_composite(pk):
    return to_order(pk)


def pk_order_least_cover(pk, nb):
    return to_order(sorted(pk, key=lambda r: (nb[r["neighbourhood"]]["cover"], r["neighbourhood"])))


# ---------------------------------------------------------------- indicators
def r3(x):
    return None if x is None else round(x, 3)


def indicators(nb, by, schools=None):
    N = sum(by.values())
    full = OrderedDict((n, by.get(n, 0)) for n in nb)
    bare_trees = sum(v for n, v in full.items() if nb[n]["bare"])
    bare_pop = sum(d["pop"] for d in nb.values() if d["bare"])
    rest_pop = sum(d["pop"] for d in nb.values() if not d["bare"])
    per_b = bare_trees / bare_pop * 1000
    per_r = (N - bare_trees) / rest_pop * 1000
    recv = [n for n, v in full.items() if v > 0]
    top10 = sorted(full.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    half = sum(d["pop"] for d in nb.values()) / 2
    cum = 0.0
    lor = 0.0
    for n in sorted(nb, key=lambda k: (nb[k]["cover"], k)):
        if cum >= half:
            break
        w = min(1.0, (half - cum) / nb[n]["pop"])
        lor += full[n] * w
        cum += nb[n]["pop"] * w
    out = OrderedDict()
    out["n_trees"] = N
    out["share_bare_pct"] = r3(bare_trees / N * 100)
    out["per1000_bare"] = r3(per_b)
    out["per1000_rest"] = r3(per_r)
    out["ratio_bare_to_rest"] = r3(per_b / per_r) if per_r else None
    out["neighbourhoods_receiving"] = len(recv)
    out["residents_receiving"] = round(sum(nb[n]["pop"] for n in recv))
    out["residents_65plus_receiving"] = round(sum(nb[n]["p65"] for n in recv))
    out["residents_0_14_receiving"] = round(sum(nb[n]["p014"] for n in recv))
    out["top10_share_pct"] = r3(sum(v for _, v in top10) / N * 100)
    out["lorenz_least_treed_half_share_pct"] = r3(lor / N * 100)
    out["mean_cover_pct"] = r3(sum(v * nb[n]["cover"] for n, v in full.items()) / N)
    out["schools_low_canopy_reached"] = schools
    return out, full


def schools_reached(sites, pts):
    low = [s for s in sites if float(s["canopy_pct_150m"]) < SCHOOL_CANOPY_LT]
    n = 0
    for s in low:
        la, lo = float(s["lat"]), float(s["lon"])
        dlat = SCHOOL_RADIUS_M / 111000.0 * 1.2
        dlon = dlat / max(0.1, math.cos(math.radians(la)))
        for q in pts:
            if abs(q["lat"] - la) > dlat or abs(q["lon"] - lo) > dlon:
                continue
            if dist_m(la, lo, q["lat"], q["lon"]) <= SCHOOL_RADIUS_M:
                n += 1
                break
    return n, len(low)


# ---------------------------------------------------------------- build
def sha(rel):
    with open(p(rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def counts(points):
    by = {}
    for q in points:
        by[q["nb"]] = by.get(q["nb"], 0) + q["trees"]
    return by


def build():
    nb, pts, sites, pk, multi = load_all()
    inside = [q for q in pts if q["nb"]]
    outside = [q for q in pts if not q["nb"]]

    def yearly(y):
        return [q for q in inside if q["year"] == y]

    def share_bare(points):
        t = sum(q["trees"] for q in points)
        b = sum(q["trees"] for q in points if nb[q["nb"]]["bare"])
        return b / t * 100

    repro = OrderedDict()
    repro["trees_total_register"] = sum(q["trees"] for q in pts)
    repro["trees_inside_neighbourhoods"] = sum(q["trees"] for q in inside)
    repro["trees_outside_neighbourhoods"] = sum(q["trees"] for q in outside)
    repro["trees_dated_2001"] = sum(q["trees"] for q in pts if q["year"] == "2001")
    repro["trees_dated_2001_inside"] = sum(q["trees"] for q in inside if q["year"] == "2001")
    repro["bare_share_pct_all"] = r3(share_bare(inside))
    for y in YEARS:
        repro["bare_share_pct_" + y] = r3(share_bare(yearly(y)))
    repro["bare_share_pct_all_without_2216_2218"] = r3(share_bare([q for q in inside if q["id"] not in GROVE_IDS]))
    repro["points_in_more_than_one_polygon"] = multi

    comp = pk_order_composite(pk)
    lcf = pk_order_least_cover(pk, nb)
    scenarios = OrderedDict()
    low_total = None
    for key in YEARS + ("all",):
        pts_k = inside if key == "all" else yearly(key)
        by_a = counts(pts_k)
        N = sum(by_a.values())
        sr, low_total = schools_reached(sites, [q for q in pts_k if q["year"] != "2001"])
        ind_a, full_a = indicators(nb, by_a, sr)
        sc = OrderedDict()
        sc["n_trees"] = N
        a = OrderedDict(ind_a)
        a["by_neighbourhood"] = full_a
        sc["actual"] = a
        for side, order in (("need", comp), ("need_least_cover_first", lcf)):
            by_n, cost_n, used_n, frac_n = walk(order, N)
            ind_n, full_n = indicators(nb, by_n)
            d = OrderedDict(ind_n)
            d["cost_central_eur"] = round(cost_n, 2)
            d["packages_used"] = used_n
            d["last_package_fraction"] = round(frac_n, 4)
            d["by_neighbourhood"] = full_n
            sc[side] = d
        pg = [q for q in pts_k if q["id"] not in GROVE_IDS]
        ind_g, _ = indicators(nb, counts(pg), schools_reached(sites, [q for q in pg if q["year"] != "2001"])[0])
        sc["actual_without_groves_2216_2218"] = ind_g
        scenarios[key] = sc

    file_n = sum(1 for s in sites if float(s["canopy_pct_150m"]) < SCHOOL_CANOPY_LT
                 and float(s["new_trees_150m_since_2024"] or 0) > 0)
    repro["schools_low_canopy_reached_from_file_column"] = file_n
    repro["schools_low_canopy_total"] = low_total

    dates = sorted(q["date"] for q in pts)
    meta = OrderedDict()
    meta["title"] = "Trees actually planted vs the same number of trees placed in order of need"
    meta["register_date_range"] = [dates[0], dates[-1]]
    meta["sources"] = OrderedDict(
        (k, OrderedDict([("path", v), ("sha256", sha(v))])) for k, v in SRC.items())
    meta["reproduction_check"] = repro
    meta["capacity_trees_pavement_central_total"] = sum(c[1] for c in comp)
    meta["eligible_neighbourhoods_trees_pavement"] = len(pk)
    meta["bare_group"] = "ua_stl2018_pct < %g (%d neighbourhoods)" % (
        BARE_THRESHOLD, sum(1 for d in nb.values() if d["bare"]))
    bare_pop = sum(d["pop"] for d in nb.values() if d["bare"])
    tot_pop = sum(d["pop"] for d in nb.values())
    meta["bare_group_residents_share_pct"] = round(bare_pop / tot_pop * 100, 3)
    meta["definitions"] = OrderedDict([
        ("n_trees", "Trees assigned to a neighbourhood by point in polygon (ray casting); N is identical on both sides. Trees outside every polygon are not in N."),
        ("year_scenarios", "2024, 2025, 2026 (to the last register date). The 4 trees dated 2001 are excluded from the yearly scenarios and included in 'all'."),
        ("need", "trees_pavement packages in order of rank_within_intervention (composite priority score, PROVISIONAL); each neighbourhood gets its central quantity until N is used; the last gets the remainder."),
        ("need_least_cover_first", "Same packages ordered by ua_stl2018_pct ascending (ties by name); independent of the composite formula."),
        ("cost_central_eur", "Sum of cost_central_eur of packages.csv, pro-rated for the partial last package."),
        ("share_bare_pct", "100 x trees in the bare group / N."),
        ("per1000_bare_and_rest", "Trees per 1,000 residents (pop_total) in the bare group / in the other neighbourhoods."),
        ("ratio_bare_to_rest", "per1000_bare / per1000_rest. Below 1: the bare group gets fewer trees per resident."),
        ("neighbourhoods_receiving", "Neighbourhoods with at least one tree."),
        ("residents_receiving", "pop_total, pop_65plus, pop_0_14 summed over neighbourhoods with at least one tree."),
        ("top10_share_pct", "Share of N in the 10 neighbourhoods with the most trees."),
        ("lorenz_least_treed_half_share_pct", "Neighbourhoods ordered by ua_stl2018_pct ascending (ties by name), population cumulated to 50% (the neighbourhood crossing 50% counted pro rata); share of N they receive."),
        ("mean_cover_pct", "Tree-weighted mean of ua_stl2018_pct: the average new tree went to a neighbourhood with this cover."),
        ("schools_low_canopy_reached", "ACTUAL side only: schools with canopy_pct_150m < 5 with at least one planted tree (non-2001 rows) within 150 m, recomputed from the points by haversine; null on the need side."),
        ("actual_without_groves_2216_2218", "Actual side with planting ids 2216 and 2218 removed."),
    ])
    caveats = [
        "capacity_unverified",
        "need_is_where_the_need_is_not_a_planting_plan",
        "composite_score_provisional_pending_audit",
        "need_limited_to_neighbourhoods_with_a_trees_pavement_package",
        "population_uncertain_per_neighbourhood_25_30_pct",
        "tree_cover_is_2018_street_tree_layer",
        "trees_dated_2001_excluded_from_yearly",
        "trees_outside_neighbourhoods_excluded_from_n",
        "mass_entries_2216_2218_unverified",
        "actual_counts_trees_not_size_or_survival",
    ]
    return OrderedDict([("meta", meta), ("scenarios", scenarios), ("caveats", caveats)])


# ---------------------------------------------------------------- output
def el_int(x):
    return "{:,}".format(int(round(x))).replace(",", ".")


MONTHS = ["Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
          "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"]


def greek_paragraph(doc, key):
    sc = doc["scenarios"][key]
    a, n = sc["actual"], sc["need"]
    pop_share = doc["meta"]["bare_group_residents_share_pct"]
    if key == "all":
        d = doc["meta"]["register_date_range"][1]
        lead = "Από το 2024 έως τις %d %s %d ο Δήμος φύτεψε %s δέντρα." % (
            int(d[8:]), MONTHS[int(d[5:7]) - 1], int(d[:4]), el_int(sc["n_trees"]))
    elif key == "2026":
        lead = "Το 2026, μέχρι σήμερα, ο Δήμος φύτεψε %s δέντρα." % el_int(sc["n_trees"])
    else:
        lead = "Το %s ο Δήμος φύτεψε %s δέντρα." % (key, el_int(sc["n_trees"]))
    s2 = "Τα %s στα 100 πήγαν στις γειτονιές χωρίς πράσινο, όπου ζουν %s στους 100 κατοίκους." % (
        el_int(a["share_bare_pct"]), el_int(pop_share))
    s3 = "Με την ίδια ποσότητα δέντρων, με σειρά ανάγκης, θα πήγαιναν %s στα 100." % el_int(n["share_bare_pct"])
    return lead + " " + s2 + " " + s3


CAVEAT_EL = ("Δεν γνωρίζουμε αν τα δέντρα χωρούν εκεί, γιατί δεν υπάρχει μητρώο λάκκων δέντρων. "
             "Η σειρά ανάγκης δείχνει πού υπάρχει ανάγκη, δεν είναι σχέδιο φύτευσης.")

LABELS = OrderedDict([
    ("n_trees", "Trees (N)"),
    ("share_bare_pct", "Share to the 62 bare neighbourhoods, %"),
    ("per1000_bare", "Trees per 1,000 residents, bare group"),
    ("per1000_rest", "Trees per 1,000 residents, other neighbourhoods"),
    ("ratio_bare_to_rest", "Ratio bare / other"),
    ("neighbourhoods_receiving", "Neighbourhoods receiving at least 1 tree"),
    ("residents_receiving", "Residents in those neighbourhoods"),
    ("residents_65plus_receiving", "Residents 65+ in those neighbourhoods"),
    ("residents_0_14_receiving", "Residents 0-14 in those neighbourhoods"),
    ("top10_share_pct", "Share of trees in the top 10 neighbourhoods, %"),
    ("lorenz_least_treed_half_share_pct", "Share to the least-treed half of the population, %"),
    ("mean_cover_pct", "Mean tree cover of the average new tree, %"),
    ("schools_low_canopy_reached", "Schools with canopy < 5% with a new tree within 150 m (actual only)"),
    ("cost_central_eur", "Cost at central price, EUR"),
])


def fmt(v):
    if v is None:
        return "n/a"
    if isinstance(v, int):
        return "{:,}".format(v)
    return "{:,.2f}".format(v) if abs(v) < 100 else "{:,.0f}".format(v)


def summary_md(doc):
    L = []
    L.append("# Actual plantings vs the same number of trees in order of need\n")
    L.append("Generated by `build_compare.py` from computed numbers only. Need-side figures that use the composite score are PROVISIONAL until the separate audit of the formula finishes; the `least cover first` column does not depend on it.\n")
    L.append("Whether the trees would physically fit where the need is cannot be known: there is no tree-pit register (flag capacity_unverified). The need side shows where the need is, it is not a planting plan.\n")
    L.append("Register dates: %s to %s. The 4 trees dated 2001 are in the total (`all`) but not in the yearly figures. Trees outside every neighbourhood polygon are not counted in N.\n" % tuple(doc["meta"]["register_date_range"]))
    for key, title in (("2025", "N = 2025"), ("all", "N = all years")):
        sc = doc["scenarios"][key]
        L.append("## %s (%s trees)\n" % (title, fmt(sc["n_trees"])))
        L.append("| Indicator | Actual | Need (composite, provisional) | Need (least cover first) |")
        L.append("|---|---:|---:|---:|")
        for k, lab in LABELS.items():
            vs = [sc[s].get(k) for s in ("actual", "need", "need_least_cover_first")]
            L.append("| %s | %s |" % (lab, " | ".join(fmt(v) for v in vs)))
        g = sc["actual_without_groves_2216_2218"]
        L.append("")
        L.append("Actual without planting ids 2216 and 2218: %s trees, %s%% to the bare group, ratio %s.\n" % (
            fmt(g["n_trees"]), fmt(g["share_bare_pct"]), fmt(g["ratio_bare_to_rest"])))
    L.append("## Sentences in Greek\n")
    for key in ("2025", "all"):
        L.append(greek_paragraph(doc, key) + "\n")
    L.append(CAVEAT_EL + "\n")
    L.append("The Greek sentences use the composite order (provisional) and whole numbers per 100.\n")
    return "\n".join(L)


def write_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    doc = build()
    with open(os.path.join(out_dir, "actual_vs_need.json"), "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    with open(os.path.join(out_dir, "actual_vs_need.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["scenario", "side", "indicator", "value"])
        for key, sc in doc["scenarios"].items():
            for side in ("actual", "need", "need_least_cover_first", "actual_without_groves_2216_2218"):
                for k, v in sc[side].items():
                    if k == "by_neighbourhood" or v is None:
                        continue
                    w.writerow([key, side, k, v])
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8", newline="") as f:
        f.write(summary_md(doc))
    return doc


if __name__ == "__main__":
    out = HERE
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    d = write_all(out)
    print(json.dumps(d["meta"]["reproduction_check"], ensure_ascii=False, indent=1))
