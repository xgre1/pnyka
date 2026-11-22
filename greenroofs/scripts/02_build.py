"""City of Athens roofs for green-roof proposals.

Run (after 01_fetch_osm.py):  <venv numpy shapely pyproj pandas>/bin/python -I greenroofs/scripts/02_build.py
Inputs:
  capacity/facility_to_building_matches.csv   City facility points -> solar-map building (bldg_idx)
  raw/treecover/dl/cityg_c40solarmap.json.gz  City solar map buildings (bldg_idx = feature order)
  roofs/roof_status.csv, roofs/work/validation_cap2022.csv   existing green roofs
  app/public/data/neighbourhoods.geojson      144 neighbourhoods (id, name)
  Overpass cache from 01_fetch_osm.py
Outputs in greenroofs/: city_roofs.geojson, app_city_roofs.geojson, city_roofs_by_neighbourhood.csv,
  unclear_candidates.csv, work/build_log.json
"""
import csv
import gzip
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "layers"))
import _osm  # noqa: E402

# ---------------------------------------------------------------- parameters
USABLE_SHARE = 0.6        # share of roof usable for a green roof (equipment, skylights, edges)
MIN_USABLE_M2 = 50.0      # skip roofs with less usable area
NODE_SNAP_M = 15.0        # OSM node not inside a building: nearest solar building within this distance
MERGE_OVERLAP = 0.5       # OSM polygon already covered >= this share by a chosen building -> same building
APP_DECIMALS = 5
OUT = os.path.join(REPO, "greenroofs")
SCHOOL_NOTE = "σχολικό κτίριο: συντήρηση από τον Δήμο, ιδιοκτησία να ελεγχθεί"

# strict City evidence in operator / owner tags
CITY_OP = re.compile(r"Δήμο[ςυ] Αθηνα[ιί]ων|Δήμος Αθηνών|Municipality of Athens|City of Athens|"
                     r"Δημοτικό Βρεφοκομείο Αθηνών", re.I)
OP_TAGS = ["operator", "owner", "operator:el", "operator:en", "owner:el", "owner:en"]
# City evidence in the name (weaker; recorded as evidence=name)
CITY_NAME = re.compile(r"^(Δημοτικ(ή|ό|ός|ές|ά) (Βιβλιοθήκη|Θέατρο|Αγορά|Πινακοθήκη|Κοινότητα|Γυμναστήριο|"
                       r"Κολυμβητήριο|Ωδείο|Αθλητικ|Πολιτιστικ|Κέντρο|Βρεφονηπιακ|Παιδικ|Ακαδημία)|"
                       r"Δημαρχείο|.*Δήμου Αθηναίων)", re.I)
# only these kinds of OSM objects can be a roofed City building
AMENITY_OK = {"library", "social_facility", "clinic", "doctors", "prep_school", "childcare", "kindergarten",
              "community_centre", "townhall", "marketplace", "theatre", "arts_centre", "cinema",
              "events_venue", "school", "public_building", "conference_centre", "exhibition_centre",
              "nursing_home", "music_school", "dancing_school", "public_bath", "toilets_building"}
LEISURE_OK = {"sports_centre", "sports_hall", "stadium", "fitness_centre"}
TOURISM_OK = {"museum", "gallery"}
AMENITY_NET = {"townhall", "library", "marketplace", "community_centre", "social_facility", "theatre",
               "arts_centre"}

T = Transformer.from_crs(4326, 2100, always_xy=True)


def to2100(g):
    return shapely.transform(g, lambda c: np.column_stack(T.transform(c[:, 0], c[:, 1])))


def loadj(p):
    return json.load(gzip.open(p, "rt", encoding="utf8") if p.endswith(".gz") else open(p, encoding="utf8"))


def ring(geom):
    pts = [(p["lon"], p["lat"]) for p in geom or []]
    return pts if len(pts) >= 4 and pts[0] == pts[-1] else None


def osm_polygon(el):
    """lon/lat polygon of a closed way or multipolygon relation, else None."""
    if el["type"] == "way":
        r = ring(el.get("geometry"))
        return Polygon(r).buffer(0) if r else None
    if el["type"] == "relation":
        outers, inners = [], []
        for m in el.get("members", []):
            r = ring(m.get("geometry")) if m.get("type") == "way" else None
            if r:
                (inners if m.get("role") == "inner" else outers).append(Polygon(r).buffer(0))
        if outers:
            g = unary_union(outers)
            return g.difference(unary_union(inners)) if inners else g
    return None


def osm_point(el):
    if el["type"] == "node":
        return shapely.Point(el["lon"], el["lat"])
    if "center" in el:
        return shapely.Point(el["center"]["lon"], el["center"]["lat"])
    return None


def city_operator(t):
    for k in OP_TAGS:
        if k in t and CITY_OP.search(t[k]):
            return f"{k}={t[k]}"
    return None


def kind_ok(t):
    return ("building" in t or t.get("amenity") in AMENITY_OK or t.get("leisure") in LEISURE_OK
            or t.get("tourism") in TOURISM_OK or t.get("office") == "government")


def osm_category(t, name):
    a, le, b = t.get("amenity", ""), t.get("leisure", ""), t.get("building", "")
    n = name or ""
    if a == "townhall" or b == "townhall" or "Δημαρχείο" in n or "Κοινότητα" in n:
        return "admin"
    if a == "library" or "Βιβλιοθήκη" in n:
        return "library"
    if re.search("Τεχνόπολ", " ".join(t.get(k, "") for k in OP_TAGS)):
        return "culture"
    if a == "marketplace" or "Αγορά" in n:
        return "market"
    if a in ("childcare", "kindergarten") or b == "kindergarten" or re.search("Παιδικός|Βρεφονηπιακ", n):
        return "nursery"
    if re.search("Λέσχη Φιλίας|ΚΑΠΗ", n):
        return "friendship_club"
    if a in ("clinic", "doctors") or re.search("Ιατρείο|Πολυιατρείο", n):
        return "clinic"
    if (a == "school" or b == "school") and re.search("Σχολείο|Γυμνάσιο|Λύκειο|Νηπιαγωγείο", n, re.I):
        return "school"
    if le in LEISURE_OK or b in ("sports_hall", "sports_centre", "stadium") or re.search("Γυμναστήριο|Κολυμβητήριο|Αθλητικ", n):
        return "sports"
    if a in ("theatre", "arts_centre", "cinema", "events_venue", "exhibition_centre", "conference_centre") \
            or t.get("tourism") in TOURISM_OK or re.search("Θέατρο|Πινακοθήκη|Πολιτιστικ|Πνευματικό Κέντρο|Ωδείο|Τεχνόπολ", n):
        return "culture"
    if b in ("industrial", "warehouse", "office") or t.get("office") == "government":
        return "municipal_service"
    return "other_city"


def main():
    log = {}
    # ---------------------------------------------------- neighbourhoods
    nbj = loadj(os.path.join(REPO, "app/public/data/neighbourhoods.geojson"))["features"]
    nb_id = [f["properties"]["id"] for f in nbj]
    nb_name = [f["properties"]["name"] for f in nbj]
    nbg = to2100(shapely.make_valid(np.array([shape(f["geometry"]) for f in nbj], dtype=object)))
    nbtree = STRtree(nbg)

    def nb_of(g2100):
        p = g2100.representative_point()
        for i in nbtree.query(p, predicate="within"):
            return int(i)
        return -1

    # ---------------------------------------------------- solar-map buildings
    sol = loadj(os.path.join(REPO, "raw/treecover/dl/cityg_c40solarmap.json.gz"))["features"]
    bg_ll = shapely.make_valid(np.array([shape(f["geometry"]) for f in sol], dtype=object))
    bg = to2100(bg_ll)
    btree = STRtree(bg)
    rp = shapely.point_on_surface(bg)
    log["solar_features"] = len(sol)

    # ---------------------------------------------------- existing green roofs
    rs = pd.read_csv(os.path.join(REPO, "roofs/roof_status.csv"))
    green_s2 = set(rs.loc[rs.status == "green", "bldg_idx"].astype(int))
    cap = pd.read_csv(os.path.join(REPO, "roofs/work/validation_cap2022.csv"))
    green_cap = set()
    for v in cap.matched_bldgs.dropna().astype(str):
        green_cap |= {int(x) for x in v.split(";") if x.strip()}
    log["green_s2_buildings"] = len(green_s2)
    log["green_cap2022_matched_buildings"] = len(green_cap)

    recs = {}  # key -> record (geometry in 2100)

    def add(key, geom, name, category, control, source, evidence, bldg_idx=None):
        if key in recs:
            r = recs[key]
            if evidence not in r["evidence"]:
                r["evidence"] += "; " + evidence
            if name and name not in r["names"]:
                r["names"].append(name)
            return
        recs[key] = dict(geom=geom, names=[name] if name else [], category=category, control=control,
                         source=source, evidence=evidence, bldg_idx=bldg_idx)

    # ---------------------------------------------------- A: City facility layers
    fm = pd.read_csv(os.path.join(REPO, "capacity/facility_to_building_matches.csv"))
    layer_cat = {"school": "school", "nursery": "nursery", "friendship_club": "friendship_club",
                 "clinic": "clinic", "municipal_service": "municipal_service", "admin_building": "admin"}
    prio = ["school", "nursery", "friendship_club", "clinic", "municipal_service", "admin"]
    fm = fm[fm.bldg_idx >= 0]
    log["facility_points_matched"] = int(len(fm))
    for b, grp in fm.groupby("bldg_idx"):
        cats = sorted({layer_cat[x] for x in grp.layer}, key=prio.index)
        names = list(dict.fromkeys(str(n).strip() for n in grp.name if str(n).strip() and str(n) != "nan"))
        # school classes inside a hospital: the building is the hospital's, not the City's
        in_hospital = all(n.upper().startswith("ΝΟΣ.") for n in names) or (sol[int(b)]["properties"].get("Type") == "hospital")
        add(("bldg", int(b)), bg[int(b)], None, cats[0], "unclear" if in_hospital else "city_register",
            "Δήμος Αθηναίων, σημεία " + "/".join(sorted(set(grp.layer))) + " (capacity/facility_to_building_matches.csv)",
            "city_layer:" + ",".join(sorted(set(grp.layer))) + " match:" + ",".join(sorted(set(grp.match)))
            + ("; νοσοκομειακό κτίριο (σχολική τάξη νοσοκομείου ή solar Type=hospital)" if in_hospital else ""),
            int(b))
        recs[("bldg", int(b))]["names"] = names
    log["facility_buildings"] = len(recs)

    # ---------------------------------------------------- B, C: OSM
    els = {}
    log["osm_cache_files"] = {}
    for key in ("greenroofs_city_operator", "greenroofs_city_amenities", "greenroofs_city_names"):
        p = os.path.join(_osm.CACHE, key + ".json")
        if not os.path.exists(p):
            log["osm_cache_files"][key] = "MISSING (Overpass failed)"
            print("WARNING: missing", p, file=sys.stderr)
            continue
        n0 = len(els)
        for el in loadj(p)["elements"]:
            els[(el["type"], el["id"])] = el
        log["osm_cache_files"][key] = len(els) - n0
    log["osm_elements_fetched"] = len(els)

    unclear = []
    chosen_union = []  # list of (geom2100, key) for overlap merging

    def chosen_tree():
        return STRtree([g for g, _ in chosen_union]) if chosen_union else None

    city_els = []
    for (typ, oid), el in els.items():
        t = el.get("tags", {})
        name = t.get("name") or t.get("name:el") or t.get("official_name") or ""
        ev = city_operator(t)
        if ev is None and CITY_NAME.search(name) and not re.search("Σχολείο|ΣΧΟΛΕΙΟ", name):
            other = any(k in t and not CITY_OP.search(t[k]) for k in OP_TAGS)
            if not other:
                ev = f"name={name}"
        if ev is not None and kind_ok(t):
            city_els.append((el, t, name, ev))
        elif ev is None and (t.get("amenity") in AMENITY_NET or t.get("leisure") == "sports_centre"):
            pt = osm_point(el)
            pg = osm_polygon(el)
            g = to2100(pg) if pg is not None else (to2100(pt) if pt is not None else None)
            if g is None:
                continue
            ni = nb_of(g)
            if ni < 0:
                continue
            unclear.append(dict(osm=f"{typ}/{oid}", name=name, amenity=t.get("amenity") or t.get("leisure"),
                                operator=t.get("operator", ""), owner=t.get("owner", ""),
                                neighbourhood_id=nb_id[ni], neighbourhood_name=nb_name[ni],
                                lat=round((pg if pg is not None else pt).representative_point().y, 6),
                                lon=round((pg if pg is not None else pt).representative_point().x, 6)))
    log["osm_city_elements_kind_ok"] = len(city_els)

    # facility buildings enter the overlap index first
    for k, r in recs.items():
        chosen_union.append((r["geom"], k))

    def order(item):
        el, t = item[0], item[1]
        if el["type"] != "node" and "building" in t:
            return 0
        return 1 if el["type"] != "node" else 2

    n_osm_merged = 0
    for el, t, name, ev in sorted(city_els, key=order):
        typ, oid = el["type"], el["id"]
        cat = osm_category(t, name)
        evidence = f"osm {typ}/{oid}: {ev}"
        src = "OpenStreetMap (Overpass, 2026-11-21, ODbL)"
        pg = osm_polygon(el) if typ != "node" else None
        targets = []  # list of (key, geom)
        if pg is not None and "building" in t:
            g = to2100(pg)
            tr = chosen_tree()
            hit = None
            if tr is not None:
                for j in tr.query(g, predicate="intersects"):
                    gj, kj = chosen_union[j]
                    ov = g.intersection(gj).area
                    if ov >= MERGE_OVERLAP * min(g.area, gj.area):
                        hit = kj
                        break
            targets = [(hit, None)] if hit else [(("osm", f"{typ}/{oid}"), g)]
        elif pg is not None:
            g = to2100(pg)
            idx = btree.query(g, predicate="intersects")
            targets = [(("bldg", int(i)), bg[int(i)]) for i in idx if g.contains(rp[int(i)])]
        else:
            pt = osm_point(el)
            if pt is None:
                continue
            p = to2100(pt)
            inside = [int(i) for i in btree.query(p, predicate="within")]
            if inside:
                b = min(inside, key=lambda k: bg[k].area)
                targets = [(("bldg", b), bg[b])]
            else:
                tr = chosen_tree()
                if tr is not None:
                    hit = [chosen_union[j][1] for j in tr.query(p, predicate="within")]
                    if hit:
                        targets = [(hit[0], None)]
                if not targets:
                    nn = btree.query_nearest(p, max_distance=NODE_SNAP_M)
                    if len(nn):
                        b = int(nn[0])
                        targets = [(("bldg", b), bg[b])]
        for key, g in targets:
            if key in recs:
                n_osm_merged += 1
                add(key, None, name, None, None, None, evidence)
                continue
            add(key, g, name, cat, "osm_operator", src, evidence, key[1] if key[0] == "bldg" else None)
            chosen_union.append((g, key))
    log["osm_hits_merged_into_existing"] = n_osm_merged

    # ---------------------------------------------------- D: City name in the solar-map layer's own `name`
    n_solar_name = 0
    for i, f in enumerate(sol):
        pr = f["properties"]
        name = (pr.get("name") or "").strip()
        if not name or not CITY_NAME.search(name) or re.search("Σχολείο|ΣΧΟΛΕΙΟ", name):
            continue
        key = ("bldg", i)
        ev = f"solar-map name={name}"
        if key in recs:
            add(key, None, name, None, None, None, ev)
            continue
        tr = chosen_tree()
        if tr is not None and any(bg[i].intersection(chosen_union[j][0]).area >= MERGE_OVERLAP * min(bg[i].area, chosen_union[j][0].area)
                                  for j in tr.query(bg[i], predicate="intersects")):
            continue
        add(key, bg[i], name, osm_category({"building": pr.get("Type") or ""}, name), "osm_operator",
            "Ηλιακός χάρτης Δήμου (cityg_c40solarmap, πεδίο name, προέρχεται από OSM)", ev, i)
        chosen_union.append((bg[i], key))
        n_solar_name += 1
    log["solar_name_added"] = n_solar_name

    # ---------------------------------------------------- finalize
    feats, skipped_small, skipped_out = [], 0, 0
    for key, r in recs.items():
        g = r["geom"]
        ni = nb_of(g)
        if ni < 0:
            skipped_out += 1
            continue
        roof = g.area
        usable = roof * USABLE_SHARE
        if usable < MIN_USABLE_M2:
            skipped_small += 1
            continue
        b = r["bldg_idx"]
        gev = []
        if b is not None and b in green_s2:
            gev.append("Sentinel-2 NDVI>=0.30 (roofs/roof_status.csv)")
        if b is not None and b in green_cap:
            gev.append("ΣΔΚ 2022 σ.52, σχολικό συγκρότημα με πράσινο δώμα (roofs/work/validation_cap2022.csv)")
        if b is not None:
            gl = bg_ll[b]
        else:
            gl = shapely.transform(g, lambda c: np.column_stack(
                Transformer.from_crs(2100, 4326, always_xy=True).transform(c[:, 0], c[:, 1])))
        if isinstance(gl, MultiPolygon) and len(gl.geoms) == 1:
            gl = gl.geoms[0]
        if gl.geom_type not in ("Polygon", "MultiPolygon"):
            polys = [x for x in getattr(gl, "geoms", []) if x.geom_type == "Polygon"]
            gl = MultiPolygon(polys) if len(polys) > 1 else polys[0]
        names = r["names"]
        is_school = r["category"] == "school" or any(re.search("ΣΧΟΛΕΙΟ|Σχολείο|Γυμνάσιο|ΓΥΜΝΑΣΙΟ|Λύκειο|ΛΥΚΕΙΟ|ΓΕΛ|ΕΠΑΛ|Νηπιαγωγείο", n) for n in names)
        feats.append(dict(type="Feature", geometry=mapping(gl), properties=dict(
            name="; ".join(names)[:200] if names else "(χωρίς όνομα)",
            category=r["category"], control=r["control"],
            owner_note=SCHOOL_NOTE if is_school else "",
            neighbourhood_id=nb_id[ni], neighbourhood_name=nb_name[ni],
            roof_m2=round(roof, 1), usable_m2=round(usable, 1),
            already_green=bool(gev), green_evidence="; ".join(gev),
            source=r["source"], evidence=r["evidence"],
            building_id=(f"solar:{b}" if b is not None else f"osm:{key[1]}"))))
    log["skipped_usable_lt_min"] = skipped_small
    log["skipped_outside_neighbourhoods"] = skipped_out
    log["features"] = len(feats)
    os.makedirs(os.path.join(OUT, "work"), exist_ok=True)
    with open(os.path.join(OUT, "city_roofs.geojson"), "w", encoding="utf8") as f:
        json.dump(dict(type="FeatureCollection", features=feats), f, ensure_ascii=False)

    # app file
    keep = ["name", "category", "control", "owner_note", "neighbourhood_id", "neighbourhood_name",
            "roof_m2", "usable_m2", "already_green"]
    app = []
    for ft in feats:
        p = ft["properties"]
        if p["control"] not in ("city_register", "osm_operator"):
            continue
        g = shapely.set_precision(shape(ft["geometry"]), 10 ** -APP_DECIMALS)
        gm = json.loads(json.dumps(mapping(g)), parse_float=lambda s: round(float(s), APP_DECIMALS))
        app.append(dict(type="Feature", geometry=gm, properties={k: p[k] for k in keep}))
    with open(os.path.join(OUT, "app_city_roofs.geojson"), "w", encoding="utf8") as f:
        json.dump(dict(type="FeatureCollection", features=app), f, ensure_ascii=False, separators=(",", ":"))
    log["app_features"] = len(app)

    # by neighbourhood
    cats = ["school", "nursery", "friendship_club", "clinic", "municipal_service", "admin", "library",
            "market", "sports", "culture", "other_city"]
    df = pd.DataFrame([ft["properties"] for ft in app])
    rows = []
    for i, n in zip(nb_id, nb_name):
        d = df[df.neighbourhood_id == i]
        row = dict(id=i, name=n, n_buildings=len(d))
        for c in cats:
            row[f"usable_m2_{c}"] = round(d.loc[d.category == c, "usable_m2"].sum(), 1)
        row["usable_m2_total"] = round(d.usable_m2.sum(), 1)
        rows.append(row)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "city_roofs_by_neighbourhood.csv"), index=False)

    for ft in feats:
        p = ft["properties"]
        if p["control"] == "unclear":
            c = shape(ft["geometry"]).representative_point()
            unclear.append(dict(osm=p["building_id"], name=p["name"], amenity=p["category"], operator="",
                                owner=p["evidence"], neighbourhood_id=p["neighbourhood_id"],
                                neighbourhood_name=p["neighbourhood_name"], lat=round(c.y, 6), lon=round(c.x, 6)))
    pd.DataFrame(unclear).rename(columns={"osm": "id", "amenity": "kind", "owner": "owner_or_evidence"}).to_csv(
        os.path.join(OUT, "unclear_candidates.csv"), index=False)
    log["unclear_osm_candidates"] = len(unclear)

    # summary numbers for README / report
    full = pd.DataFrame([ft["properties"] for ft in feats])
    log["by_category_control"] = {f"{a}|{b}": [int(len(g)), round(float(g.usable_m2.sum()))]
                                  for (a, b), g in full.groupby(["category", "control"])}
    log["usable_m2_total_app"] = round(float(df.usable_m2.sum()))
    log["roof_m2_total_app"] = round(float(df.roof_m2.sum()))
    log["neighbourhoods_with_candidate"] = int((pd.DataFrame(rows).n_buildings > 0).sum())
    log["already_green_features"] = int(df.already_green.sum())
    log["school_owner_note_features"] = int((df.owner_note != "").sum())
    osm_only = full[full.control == "osm_operator"]
    log["osm_only_n"] = int(len(osm_only))
    log["osm_only_names"] = sorted(set(osm_only.name))[:400]
    with open(os.path.join(OUT, "work", "build_log.json"), "w", encoding="utf8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in log.items() if k != "osm_only_names"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
