"""Build mockup/data.js from the engine export and the repo's data. Read-only on everything else.

Usage, from the repo root:  python3 mockup/build_data.py . mockup/data.js
"""
import csv
import json
import os
import sys

REPO = sys.argv[1]
OUT = sys.argv[2]
TABS = ("trees_pavement", "roof_cool_or_green_municipal")


def path(p):
    return os.path.join(REPO, p)


def rows(p):
    with open(path(p), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


eng = json.load(open(path("engine/packages.json"), encoding="utf-8"))
labels = {r["code"]: {"label": r["label_el"], "long": r["long_el"]} for r in rows("engine/labels_el.csv")}

# Two Athens measurements that the engine keeps in params.csv but not yet in the roof impacts.
# Read from params.csv (the engine's single source); dropped automatically once the JSON carries them.
extra_roof = []
for r in rows("engine/params.csv"):
    if r["intervention_id"] != "roof_cool_or_green_municipal" or r["status"] != "measured_athens":
        continue
    if r["parameter"] == "classroom_air_temp_reduction_summer_degc":
        extra_roof.append({"metric_code": "classroom_air_temp_summer", "value_up_to": num(r["high"]), "low": num(r["low"]),
                           "high": num(r["high"]), "unit": "degC", "status": "measured_athens", "source_code": "cool_roofs_kaisariani"})
    if r["parameter"] == "roof_surface_temp_reduction_degc":
        extra_roof.append({"metric_code": "roof_surface_temp", "value_up_to": num(r["high"]), "low": None,
                           "high": num(r["high"]), "unit": "degC", "status": "measured_athens", "source_code": "cool_roofs_kaisariani"})
labels.setdefault("classroom_air_temp_summer", {"label": "Έως τόσους βαθμούς δροσερότερη η τάξη το καλοκαίρι", "long": "Μέτρηση σε σχολείο της Καισαριανής χωρίς κλιματισμό."})
labels.setdefault("roof_surface_temp", {"label": "Έως τόσους βαθμούς δροσερότερη η επιφάνεια της στέγης", "long": "Ίδια μέτρηση."})
labels.setdefault("cool_roofs_kaisariani", {"label": "Ευρωπαϊκό έργο Cool Roofs, σχολείο στην Καισαριανή", "long": ""})

pk = {}
for p in eng["packages"]:
    if p["intervention"] not in TABS:
        continue
    q = dict(p)
    if p["intervention"] == "roof_cool_or_green_municipal":
        have = {i["metric_code"] for i in p["impacts"]}
        q["impacts"] = [i for i in extra_roof if i["metric_code"] not in have] + p["impacts"]
    pk.setdefault(p["neighbourhood"], {})[p["intervention"]] = q

geo = json.load(open(path("neighbourhoods.geojson"), encoding="utf-8"))
pop = {r["name"]: r for r in rows("raw/population/population_by_neighbourhood.csv")}
feats = []
for f in geo["features"]:
    n = f["properties"]["name"]
    po = pop.get(n, {})
    feats.append({"type": "Feature", "geometry": f["geometry"], "properties": {
        "name": n,
        "dk": f["properties"].get("municipal_district_id"),
        "pop": num(po.get("pop_total")),
        "pk": pk.get(n, {}),
    }})

sites = [[r["site_type"], r["name"], num(r["lat"]), num(r["lon"]), num(r["canopy_pct_150m"]), num(r["new_trees_150m_since_2024"]), r["neighbourhood"]]
         for r in rows("streets/sites_with_plantings.csv")]
plant = [[round(num(r["lat"]), 5), round(num(r["lon"]), 5)] for r in rows("athenstrees/plantings_points.csv") if num(r["lat"]) and num(r["lon"])]

used = set(TABS)
for d in pk.values():
    for p in d.values():
        used.update([p.get("people_basis_code"), p.get("evidence_code")] + p.get("data_gaps", []) + p.get("flags", []))
        used.update(i["metric_code"] for i in p["impacts"])
        used.update(i["source_code"] for i in p["impacts"])
        used.update(i["status"] for i in p["impacts"])
        used.update(w["indicator_code"] for w in p.get("why_here", []))
labels_used = {k: v for k, v in labels.items() if k in used}

data = {"nb": {"type": "FeatureCollection", "features": feats}, "sites": sites, "plant": plant, "labels": labels_used,
        "generated_from": eng.get("generated_from")}
with open(OUT, "w", encoding="utf-8") as f:
    f.write("window.DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";")
missing = sorted(c for c in used if c and c not in labels)
print("features", len(feats), "packages", sum(len(v) for v in pk.values()), "sites", len(sites), "plantings", len(plant),
      "bytes", os.path.getsize(OUT), "labels missing:", missing)
