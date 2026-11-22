"""Build the app's data files from the engine export and the repo's data.

Run from the repo root:
    python3 app/scripts/build_data.py            # public build, no Athens Trees points
    python3 app/scripts/build_data.py --with-plantings

Writes app/public/data/{neighbourhoods.geojson, app.json, sites.json[, plantings.json]}.
Every number shown by the app comes from engine/packages.json; nothing is computed here
except rounding and the two Athens roof measurements that the engine keeps in params.csv.
"""
import math
import csv
import json
import os
import sys

ROOT = os.getcwd()
OUT = os.path.join(ROOT, "app", "public", "data")
WITH_PLANTINGS = "--with-plantings" in sys.argv
TABS = {"trees_pavement": "streets", "roof_cool_or_green_municipal": "buildings"}


def p(*a):
    return os.path.join(ROOT, *a)


def rows(path):
    with open(p(path), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def r(v, d=1):
    return None if v is None else round(v, d)


os.makedirs(OUT, exist_ok=True)
eng = json.load(open(p("engine", "packages.json"), encoding="utf-8"))
labels = {x["code"]: {"label": x["label_el"], "long": x["long_el"]} for x in rows("engine/labels_el.csv")}
names = {x["name"]: x["display"] for x in rows("app/scripts/names_el.csv")}
pop = {x["name"]: x for x in rows("raw/population/population_by_neighbourhood.csv")}

extra_roof = []
for x in rows("engine/params.csv"):
    if x["intervention_id"] != "roof_cool_or_green_municipal" or x["status"] != "measured_athens":
        continue
    if x["parameter"] == "classroom_air_temp_reduction_summer_degc":
        extra_roof.append(["classroom_air_temp_summer", num(x["high"]), num(x["low"]), num(x["high"]), "degC", "measured_athens", "cool_roofs_kaisariani"])
    if x["parameter"] == "roof_surface_temp_reduction_degc":
        extra_roof.append(["roof_surface_temp", num(x["high"]), None, num(x["high"]), "degC", "measured_athens", "cool_roofs_kaisariani"])
labels.setdefault("classroom_air_temp_summer", {"label": "Έως τόσους βαθμούς δροσερότερη η τάξη το καλοκαίρι", "long": "Μέτρηση σε σχολείο της Καισαριανής χωρίς κλιματισμό."})
labels.setdefault("roof_surface_temp", {"label": "Έως τόσους βαθμούς δροσερότερη η επιφάνεια της στέγης", "long": "Ίδια μέτρηση."})
labels.setdefault("cool_roofs_kaisariani", {"label": "Ευρωπαϊκό έργο Cool Roofs, σχολείο στην Καισαριανή", "long": ""})

geo = json.load(open(p("neighbourhoods.geojson"), encoding="utf-8"))
ids = {f["properties"]["name"]: i for i, f in enumerate(geo["features"])}
missing_names = [n for n in ids if n not in names]

packages = {"streets": {}, "buildings": {}}
used = set()
for pk in eng["packages"]:
    tab = TABS.get(pk["intervention"])
    if not tab or pk["neighbourhood"] not in ids:
        continue
    imp = [[i["metric_code"], i["value_up_to"], i["low"], i["high"], i["unit"], i["status"], i["source_code"]] for i in pk["impacts"]]
    if tab == "buildings":
        have = {i[0] for i in imp}
        imp = [i for i in extra_roof if i[0] not in have] + imp
    q, c = pk["quantity"], pk["cost_eur"]
    packages[tab][ids[pk["neighbourhood"]]] = {
        "rank": pk["rank_within_intervention"],
        "q": [r(q["low"], 0), r(q["central"], 0), r(q["high"], 0)],
        "c": [r(c["low"], 0), r(c["central"], 0), r(c["high"], 0)] if c and c.get("central") is not None else None,
        "sites": pk.get("sites_n"),
        # Full intervention for the 0-100% slider: capacity (trees to reach the canopy target, or all roof m2)
        "cap": r(pk.get("capacity"), 0),
        "time": [pk["time_to_effect_years"]["low"], pk["time_to_effect_years"]["high"]] if pk.get("time_to_effect_years") else None,
        "why": [[w["indicator_code"], r(w["value"], 2), w["percentile"], w["unit"]] for w in pk.get("why_here", []) if w.get("value") is not None],
        "imp": imp,
        "gaps": pk.get("data_gaps", []),
    }
    used.update(x[0] for x in imp)
    used.update(x[5] for x in imp)
    used.update(x[6] for x in imp)
    used.update(w["indicator_code"] for w in pk.get("why_here", []))
    used.update(pk.get("data_gaps", []))
used.update(TABS)

# Roofs: municipal buildings that are NOT schools (Λέσχες Φιλίας, clinics, nurseries, services), the ones that can have
# air conditioning and work in summer. Schools are left out: mostly no AC and closed in summer (findings 1445, 1500).
# Quantity = their roof footprint (capacity/), price from engine/params.csv (assumption 13.5 / 20 / 25 EUR/m2).
capn = {x["name"]: x for x in rows("capacity/capacity_by_neighbourhood.csv")}
ROOF_PRICE = (13.5, 20.0, 25.0)
old_b = packages["buildings"]
packages["buildings"] = {}
for n, i in ids.items():
    m2 = num(capn.get(n, {}).get("municipal_other_roof_area_m2")) or 0
    if m2 < 1:
        continue
    base = old_b.get(i, {})
    packages["buildings"][i] = {
        "rank": base.get("rank", 999), "q": [round(m2)] * 3, "c": [round(m2 * ROOF_PRICE[0]), round(m2 * ROOF_PRICE[1]), round(m2 * ROOF_PRICE[2])],
        "sites": num(capn[n].get("municipal_other_buildings_n")), "cap": round(m2), "time": [0, 1],
        "why": base.get("why", []), "imp": [x for x in base.get("imp", []) if x[0] == "building_cooling_load"], "gaps": base.get("gaps", []),
    }
for r_, (i, pk) in enumerate(sorted(packages["buildings"].items(), key=lambda kv: kv[1]["rank"]), start=1):
    pk["rank"] = r_
# Energy chain for the screen (each number cited; the result is an upper bound "έως").
ENERGY = {
    "cooling_kwh_per_m2": 33.0,      # office, CRES presentation, method unknown
    "cooling_cut": 0.40,             # cool roof, Kaisariani school, computed cooling need
    "heating_increase": 0.10,        # same measurement: heating need +10% in winter
    "eur_per_kwh": 0.2342,           # Eurostat nrg_pc_205, Greece, non-household 20-499 MWh, 2026 S1, all taxes
    "co2_kg_per_kwh": 0.269,         # Greek grid 2024, second-hand
    "price_eur_m2": ROOF_PRICE[1],
}


# European capitals by urban tree cover (EEA table, finding 1819). Athens' added canopy is placed on top of the EEA 11%.
CAPITALS = [[x["City name:text"], int(x["Urban tree cover:number"])] for x in rows("raw/compare/eea_green_infrastructure_cities.csv") if "average" not in x["City name:text"]]

# Where greening fits, per neighbourhood. Tree spots from planting/ (streets, pedestrian streets, school yards) when present,
# else the engine's trees-to-10% as a stand-in. Green roofs only on City buildings: greenroofs/ when present,
# else 60% of the school + municipal roof footprint from capacity/.
def _csv(path):
    full = os.path.join(ROOT, path) if "ROOT" in globals() else path
    return rows(path) if os.path.exists(full) else []
_spots = {str(x["id"]): x for x in _csv("planting/candidates_by_neighbourhood.csv")}
_groof = {str(x["id"]): x for x in _csv("greenroofs/city_roofs_by_neighbourhood.csv")}
GREEN_ROOF_EUR_M2 = (45.0, 110.0, 320.0)
# Per-unit impact, Mediterranean reference (research/cost/sources.csv BCN-2014: Baró et al. 2014, Barcelona i-Tree Eco:
# 19,036 t CO2/yr and 305.6 t pollutants/yr; divided by about 1.42 million trees, tree count from memory, to be checked).
# Green roof rain: Athens about 400 mm/yr x about 50% retained by an extensive green roof (assumption, to be checked).
IMPACT = {"co2_kg_per_tree_yr": 13.4, "pollutants_kg_per_tree_yr": 0.215, "roof_rain_m3_per_m2_yr": 0.2}  # research/cost/roofs_pavements/defaults.csv green_roof_cost_installed
for n, i in ids.items():
    pk = packages["streets"].get(i)
    if not pk:
        continue
    sp = _spots.get(str(i))
    if sp:
        pk["spots"] = int(num(sp.get("trees_total")) or 0)
        pk["spots_parking"] = int(num(sp.get("trees_streets_parking")) or 0)
        pk["spots_src"] = "planting"
    else:
        pk["spots"] = int(pk.get("cap") or pk["q"][1] or 0)
        pk["spots_parking"] = 0
        pk["spots_src"] = "engine"
    gr = _groof.get(str(i))
    c = capn.get(n, {})
    if gr:
        pk["groof"] = round(num(gr.get("usable_m2_total")) or 0)
    else:
        pk["groof"] = round(0.6 * ((num(c.get("schools_roof_area_m2")) or 0) + (num(c.get("municipal_other_roof_area_m2")) or 0)))
    # Facades of City buildings: perimeter of a square footprint x 8 m height x 30% usable wall (no windows), per building.
    fac = num((gr or {}).get("facade_m2_total"))
    if fac is None:
        fac = 0.0
        for nb_n, a in ((num(c.get("schools_buildings_n")) or 0, num(c.get("schools_roof_area_m2")) or 0),
                        (num(c.get("municipal_other_buildings_n")) or 0, num(c.get("municipal_other_roof_area_m2")) or 0)):
            if nb_n > 0 and a > 0:
                fac += nb_n * 4 * math.sqrt(a / nb_n) * 8 * 0.3
    pk["facade"] = round(fac / 10) * 10

# Tree spots as points, per neighbourhood, so the map can "plant" them one by one.
def _metres(a, b):
    return math.hypot((b[0] - a[0]) * 111320 * math.cos(math.radians(37.98)), (b[1] - a[1]) * 110540)

def _along(coords, n):
    segs = [(a, b, _metres(a, b)) for a, b in zip(coords, coords[1:])]
    L = sum(s[2] for s in segs)
    if n <= 0 or L <= 0:
        return []
    out, step, t, acc = [], L / n, L / n / 2, 0.0
    for a, b, d in segs:
        while t <= acc + d and len(out) < n:
            f = (t - acc) / d if d else 0
            out.append([round(a[0] + (b[0] - a[0]) * f, 5), round(a[1] + (b[1] - a[1]) * f, 5)])
            t += step
        acc += d
    return out

def _inside(x, y, ring):
    ins = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1:
            ins = not ins
    return ins

def _grid(ring, n):
    xs = [p_[0] for p_ in ring]; ys = [p_[1] for p_ in ring]
    for step_m in (12, 9, 7, 5, 4, 3):
        dx = step_m / (111320 * math.cos(math.radians(37.98))); dy = step_m / 110540
        pts = []
        y = min(ys) + dy / 2
        while y < max(ys):
            x = min(xs) + dx / 2
            while x < max(xs):
                if _inside(x, y, ring):
                    pts.append([round(x, 5), round(y, 5)])
                x += dx
            y += dy
        if len(pts) >= n:
            return pts[:n]
    return pts[:n]

def _lines(g):
    t = g["type"]
    return [g["coordinates"]] if t == "LineString" else g["coordinates"] if t == "MultiLineString" else []

SPOTS = {}
_cand = p("planting", "app_candidates.geojson")
if os.path.exists(_cand):
    cg = json.load(open(_cand, encoding="utf-8"))
    order = {"pedestrian": 0, "yard": 1, "street": 2}
    feats_c = sorted(cg["features"], key=lambda f: order.get(f["properties"].get("type"), 3))
    for f in feats_c:
        pr = f["properties"]
        nb_name = pr.get("neighbourhood_name") or pr.get("neighbourhood")
        i = pr.get("nb_id", pr.get("neighbourhood_id"))
        if i is None:
            i = ids.get(nb_name)
        if i is None:
            continue
        k = int(num(pr.get("trees")) or 0)
        g = f["geometry"]
        if g["type"] in ("Polygon", "MultiPolygon"):
            ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
            pts = _grid(ring, k)
        elif g["type"] == "Point":
            pts = [[round(g["coordinates"][0], 5), round(g["coordinates"][1], 5)]] * min(k, 1)
        else:
            ls = _lines(g)
            tot = sum(sum(_metres(a, b) for a, b in zip(l, l[1:])) for l in ls) or 1
            pts = [q for l in ls for q in _along(l, round(k * sum(_metres(a, b) for a, b in zip(l, l[1:])) / tot))]
        SPOTS.setdefault(str(i), []).extend(pts)
else:
    # Stand-in until planting/ exists: OSM streets of the neighbourhood, least shaded first, one tree every 8 m.
    sg = json.load(open(p("streets", "streets.geojson"), encoding="utf-8"))
    by_nb = {}
    for f in sg["features"]:
        by_nb.setdefault(f["properties"].get("neighbourhood"), []).append(f)
    for n, i in ids.items():
        pk = packages["streets"].get(i)
        if not pk or not pk.get("spots"):
            continue
        want, pts = pk["spots"], []
        for f in sorted(by_nb.get(n, []), key=lambda f: f["properties"].get("canopy_pct_12m") or 0):
            for l in _lines(f["geometry"]):
                Lm = sum(_metres(a, b) for a, b in zip(l, l[1:]))
                pts.extend(_along(l, min(int(Lm // 8), want - len(pts))))
                if len(pts) >= want:
                    break
            if len(pts) >= want:
                break
        SPOTS[str(i)] = pts
        if pts and len(pts) < want:
            pk["spots"] = len(pts)  # never promise more trees than the map can show
json.dump(SPOTS, open(os.path.join(OUT, "spots.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# City roofs (greenroofs/), filled in order inside each neighbourhood as the slider passes the trees.
ROOFS = []
_rf = p("greenroofs", "app_city_roofs.geojson")
if os.path.exists(_rf):
    rg = json.load(open(_rf, encoding="utf-8"))
    cum = {}
    for f in sorted(rg["features"], key=lambda f: -(num(f["properties"].get("usable_m2")) or 0)):
        pr = f["properties"]
        i = ids.get(pr.get("neighbourhood_name") or pr.get("neighbourhood"))
        if i is None:
            i = pr.get("neighbourhood_id")
        if i is None or pr.get("already_green") in (True, "True", "true", 1):
            continue
        m2 = num(pr.get("usable_m2")) or 0
        cum[str(i)] = cum.get(str(i), 0) + m2
        f2 = {"type": "Feature", "geometry": f["geometry"], "properties": {"nb": str(i), "m2": round(m2), "cum": round(cum[str(i)]), "name": pr.get("name", "")}}
        ROOFS.append(f2)
if ROOFS:
    # Roofs and facades follow the drawn City buildings, so the bar never promises a roof the map cannot show.
    per_roof, per_fac = {}, {}
    for f2 in ROOFS:
        nb_ = f2["properties"]["nb"]
        per_roof[nb_] = per_roof.get(nb_, 0) + f2["properties"]["m2"]
        ring = f2["geometry"]["coordinates"][0] if f2["geometry"]["type"] == "Polygon" else f2["geometry"]["coordinates"][0][0]
        per_fac[nb_] = per_fac.get(nb_, 0) + sum(_metres(a, b) for a, b in zip(ring, ring[1:])) * 8 * 0.3
    for i_, pk in packages["streets"].items():
        pk["groof"] = round(per_roof.get(str(i_), 0))
        pk["facade"] = round(per_fac.get(str(i_), 0) / 10) * 10
json.dump({"type": "FeatureCollection", "features": ROOFS}, open(os.path.join(OUT, "roofs.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

feats = []
for f in geo["features"]:
    n = f["properties"]["name"]
    i = ids[n]
    g = f["geometry"]

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]

    props = {"id": i, "name": names.get(n, n), "dk": f["properties"].get("municipal_district_id")}
    for tab in packages:
        pk = packages[tab].get(i)
        props["rank_" + tab] = pk["rank"] if pk else -1
    feats.append({"type": "Feature", "id": i, "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}, "properties": props})

nbs = {i: {"name": names.get(n, n), "raw": n, "dk": geo["features"][i]["properties"].get("municipal_district_id"),
           "pop": r(num(pop.get(n, {}).get("pop_total")), -1),
           "pop65": r(num(pop.get(n, {}).get("pop_65plus")), -1),
           "pop014": r(num(pop.get(n, {}).get("pop_0_14")), -1),
           "area_km2": r(num(pop.get(n, {}).get("area_km2")), 3),
           "tree_pct": r(num(pop.get(n, {}).get("ua_stl2018_pct")), 1)} for n, i in ids.items()}

sites = [[x["site_type"], x["name"], round(num(x["lat"]), 5), round(num(x["lon"]), 5), r(num(x["canopy_pct_150m"]), 1)]
         for x in rows("streets/sites_with_plantings.csv")]

# Planted vs the same number of trees in order of need: engine/compare/actual_vs_need.json (engine export).
compare = None
cmp_path = p("engine", "compare", "actual_vs_need.json")
if os.path.exists(cmp_path):
    cj = json.load(open(cmp_path, encoding="utf-8"))
    KEEP = ["n_trees", "share_bare_pct", "per1000_bare", "per1000_rest", "top10_share_pct", "mean_cover_pct",
            "neighbourhoods_receiving", "residents_receiving", "cost_central_eur", "schools_low_canopy_reached"]
    compare = {}
    for yr, sc in cj["scenarios"].items():
        compare[yr] = {"n": sc["n_trees"]}
        for side in ("actual", "need"):
            v = sc[side]
            compare[yr][side] = {k: v.get(k) for k in KEEP}
            compare[yr][side]["by"] = {str(ids[n]): t for n, t in v["by_neighbourhood"].items() if n in ids and t}

# Map layers: one value per neighbourhood, each with its source and kind (recorded / calculated).
# A neighbourhood without a value stays empty (never imputed). Sensor-based layers cover only areas with a City sensor.
nbcsv = {x["name"]: x for x in rows("neighbourhoods.csv")}
no2 = {x["name"]: num(x["no2_2024_ugm3"]) for x in rows("raw/air/no2_eea_2024_by_neighbourhood.csv")}
def layer(lid, name, unit, kind, source, getter, digits=1, note="", worse="high"):
    vals = {}
    for n, i in ids.items():
        v = getter(n)
        if v is not None:
            vals[str(i)] = round(v, digits)
    return {"id": lid, "name": name, "unit": unit, "kind": kind, "source": source, "note": note, "worse": worse,
            "update": UPDATE.get(lid) or next((u for k, u in UPDATE.items() if k.endswith("*") and lid.startswith(k[:-1])), ""), "values": vals}

# How often each SOURCE refreshes (the demo itself is a static snapshot of it).
UPDATE = {
    "heat_night": "live", "hours_35": "live", "pm25": "live", "sensor_gap": "live",
    "ndvi_2025": "Κάθε 5 μέρες (Sentinel-2)", "albedo_2025": "Κάθε 5 μέρες (Sentinel-2)",
    "tree_cover": "Ανά 3 χρόνια (Copernicus)", "imperviousness": "Ανά 3 χρόνια (Copernicus)",
    "no2": "Κάθε χρόνο (ΕΟΠ)", "density": "Κάθε 10 χρόνια (απογραφή)", "airbnb_listings": "Κάθε 3 μήνες (Inside Airbnb)",
    "osm_*": "Συνεχώς (OpenStreetMap)", "city_*": "Όποτε ενημερώνει ο Δήμος", "lst_summer_day": "Μία μελέτη, 2016-2020",
    "elevation": "Σταθερό", "tree_height": "Μία λήψη, 2018-2020", "zoned_green": "Όποτε ενημερώνει ο Δήμος", "pocket_parks": "Όποτε ενημερώνει ο Δήμος",
}
def popv(field):
    return lambda n: num(pop.get(n, {}).get(field))
def nbv(field):
    return lambda n: num(nbcsv.get(n, {}).get(field))
def density(n):
    a, pp = num(pop.get(n, {}).get("area_km2")), num(pop.get(n, {}).get("pop_total"))
    return pp / a if a and pp is not None else None
layers = [
    layer("tree_cover", "Κάλυψη δέντρων", "%", "rec", "Copernicus Urban Atlas Street Tree Layer 2018", popv("ua_stl2018_pct"), worse="low"),
    layer("heat_night", "Ζέστη τη νύχτα", "°C", "rec", "Αισθητήρες Δήμου Αθηναίων, καλοκαίρι 2026", nbv("heat_night"), note="Μόνο όπου υπάρχει αισθητήρας"),
    layer("hours_35", "Ώρες πάνω από 35°", "ώρες", "rec", "Αισθητήρες Δήμου Αθηναίων, καλοκαίρι 2026", nbv("hours_above_35"), 0, note="Μόνο όπου υπάρχει αισθητήρας"),
    layer("pm25", "Σωματίδια PM2.5", "µg/m³", "rec", "Αισθητήρες Δήμου Αθηναίων, 2026", nbv("pm2_5"), note="Μόνο όπου υπάρχει αισθητήρας. Οι αισθητήρες χαμηλού κόστους συμφωνούν με τους επίσημους σταθμούς μόνο στο PM2.5"),
    layer("no2", "Διοξείδιο του αζώτου (NO2)", "µg/m³", "calc", "Ευρωπαϊκός Οργανισμός Περιβάλλοντος, χάρτης NO2 2024 (προσωρινός), πλέγμα 1 χλμ, CC BY 4.0",
          lambda n: no2.get(n), note="Χάρτης 1 χλμ από σταθμούς και μοντέλο. Δείχνει τη γενική εικόνα, όχι κάθε δρόμο"),
    layer("density", "Πυκνότητα κατοίκων", "/km²", "calc", "Απογραφή 2021 (Eurostat), κατανομή ανά γειτονιά", density, 0),
    # Where the City has no sensor: residents living there, so the map shows where a new sensor would cover most people.
    layer("sensor_gap", "Χωρίς αισθητήρα", "κάτοικοι", "calc", "Δίκτυο αισθητήρων Δήμου (CKAN env-all-stations) και απογραφή 2021",
          lambda n: num(pop.get(n, {}).get("pop_total")) if nbcsv.get(n, {}).get("has_sensor") != "True" else None, -2,
          note="Γειτονιές χωρίς κανέναν αισθητήρα του Δήμου. Το χρώμα δείχνει πόσοι κάτοικοι ζουν εκεί"),
]

# Extra layers: every raw/layers/<id>.csv (name,value) with its raw/layers/<id>.json metadata.
import glob
# Layers that do not help decide where to plant stay in raw/layers/ but leave the app (team, 21/11 evening).
HIDDEN = {"osm_pharmacies", "osm_cafes_restaurants", "city_kep_distance", "osm_food_shops", "osm_parking",
          "airbnb_listings", "city_culture_distance", "osm_transit_stops", "osm_benches", "osm_bike_km", "city_rail_distance",
          "elevation",
          # team, 22/11: not about where to plant
          "city_archaeology_zone", "city_controlled_parking", "osm_drinking_water", "city_ev_chargers", "city_fountains", "albedo_2025"}
for meta_path in sorted(glob.glob(p("raw", "layers", "*.json"))):
    meta = json.load(open(meta_path, encoding="utf-8"))
    if meta["id"] in HIDDEN:
        continue
    vals = {x["name"]: num(x["value"]) for x in rows(os.path.relpath(meta_path[:-5] + ".csv", ROOT))}
    digits = 0 if any(v is not None and abs(v) >= 100 for v in vals.values()) else 1
    layers.append(layer(meta["id"], meta["name"], meta["unit"], meta.get("kind", "rec"), meta["source"],
                        lambda n, vals=vals: vals.get(n), digits, note=meta.get("note", ""), worse=meta.get("worse", "high")))

# City-wide recorded facts for the "Σήμερα" block (no projection here).
area = sum(num(x["area_km2"]) or 0 for x in pop.values())
city = {
    "tree_cover_pct": round(sum((num(x["area_km2"]) or 0) * (num(x["ua_stl2018_pct"]) or 0) for x in pop.values()) / area, 1),  # Copernicus STL 2018
    "schools": sum(1 for x in sites if x[0] == "school"),
    "schools_low_canopy": sum(1 for x in rows("streets/sites_with_plantings.csv") if x["site_type"] == "school" and num(x["canopy_pct_150m"]) is not None and num(x["canopy_pct_150m"]) < 5),
    "plantings_2024_2026": compare["all"]["actual"]["n_trees"] if compare else None,  # Athens Trees
    "roof_school_m2": round(sum(num(x.get("schools_roof_area_m2")) or 0 for x in rows("capacity/capacity_by_neighbourhood.csv"))),
    "roof_other_m2": round(sum(num(x.get("municipal_other_roof_area_m2")) or 0 for x in rows("capacity/capacity_by_neighbourhood.csv"))),
    "sensor_gap_neighbourhoods": sum(1 for n in ids if nbcsv.get(n, {}).get("has_sensor") != "True"),
    "sensor_gap_residents": round(sum(num(pop.get(n, {}).get("pop_total")) or 0 for n in ids if nbcsv.get(n, {}).get("has_sensor") != "True"), -3),
    "green_roofs_existing": 13, "green_roofs_existing_m2": 6475,  # City climate plan 2022 p.52, finding 2026-11-21-1445
}

json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "neighbourhoods.geojson"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump({"neighbourhoods": nbs, "packages": packages, "counts": {t: len(v) for t, v in packages.items()}, "energy": ENERGY, "capitals": CAPITALS, "green_roof_eur_m2": GREEN_ROOF_EUR_M2, "facade_eur_m2": [450.0, 900.0, 1500.0], "impact": IMPACT,
           "labels": {k: v for k, v in labels.items() if k in used}, "with_plantings": WITH_PLANTINGS, "compare": compare, "city": city, "layers": layers,
           "generated_from": eng.get("generated_from")},
          open(os.path.join(OUT, "app.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(sites, open(os.path.join(OUT, "sites.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
pl_path = os.path.join(OUT, "plantings.json")
if WITH_PLANTINGS:
    # [lon, lat, year] per planting point; one point = one tree in the Athens Trees export.
    pl = [[round(num(x["lon"]), 5), round(num(x["lat"]), 5), int(x["planting_date"][:4] or 0)]
          for x in rows("athenstrees/plantings_points.csv") if num(x["lat"]) and num(x["lon"])]
    json.dump(pl, open(pl_path, "w"), separators=(",", ":"))
elif os.path.exists(pl_path):
    os.remove(pl_path)

print("neighbourhoods", len(feats), "packages", {t: len(v) for t, v in packages.items()}, "sites", len(sites),
      "plantings", WITH_PLANTINGS, "names missing", missing_names, "labels missing", sorted(c for c in used if c not in labels))
