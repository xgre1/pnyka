#!/usr/bin/env python
"""Per-neighbourhood physical-intervention capacity for the Municipality of Athens.
Run:  /tmp/athens_streets/venv/bin/python -I 01_compute_capacity.py
Writes capacity_by_neighbourhood.csv + validation.json + facility_to_building_matches.csv under capacity/.
Metric CRS = EPSG:2100 (GGRS87 / Greek Grid).
"""
import json, gzip, math, re
import numpy as np, pandas as pd, shapely, rasterio
from shapely import STRtree
from shapely.geometry import shape
from rasterio.features import geometry_mask
from pyproj import Transformer

D = '.'
OUT = D + 'capacity/'
DL = D + 'raw/treecover/dl/'
T2100 = Transformer.from_crs(4326, 2100, always_xy=True)
T3857 = Transformer.from_crs(4326, 3857, always_xy=True)
V = {}  # validation / meta record


def proj(geoms, T):
    return shapely.transform(np.asarray(geoms, dtype=object), lambda c: np.column_stack(T.transform(c[:, 0], c[:, 1])))


def loadj(p):
    return json.load(gzip.open(p, 'rt', encoding='utf8') if p.endswith('.gz') else open(p, encoding='utf8'))


def feats_to_geoms(feats, T=T2100):
    g = shapely.make_valid(np.array([shape(f['geometry']) for f in feats], dtype=object))
    return proj(g, T) if T is not None else g


def R(series_or_arr):
    return np.asarray(series_or_arr)


# ---------------------------------------------------------------- neighbourhoods
nbj = loadj(D + 'neighbourhoods.geojson')['features']
nb = pd.DataFrame([f['properties'] for f in nbj])[['name', 'municipal_district_id', 'area_km2']].rename(
    columns={'municipal_district_id': 'community_id', 'area_km2': 'area_km2_source'})
nbg = feats_to_geoms(nbj)
nb['area_m2'] = shapely.area(nbg)
nb['area_km2'] = nb.area_m2 / 1e6
assert nb.name.is_unique
NB = len(nb)
nbtree = STRtree(nbg)
V['n_neighbourhoods'] = NB
V['sum_area_km2_geometry'] = float(nb.area_km2.sum())
V['sum_area_km2_source_attr'] = float(nb.area_km2_source.sum())
muni = shapely.union_all(nbg)
V['municipality_union_area_km2'] = float(muni.area / 1e6)
V['neighbourhood_overlap_km2'] = float((nb.area_m2.sum() - muni.area) / 1e6)

dk = loadj(D + 'registry/gis/dimotikes_koinotites1.geojson')['features']
dkg = feats_to_geoms(dk)
dkno = [f['properties']['no'] for f in dk]
agree = 0
for i, g in enumerate(nbg):
    c = g.representative_point()
    for j, d in enumerate(dkg):
        if d.contains(c):
            agree += int(dkno[j] == nb.community_id[i]); break
V['community_id_agrees_with_dk_polygon_layer'] = f'{agree}/{NB}'


def nb_of_points(pts):
    """neighbourhood index containing each point (-1 outside)."""
    res = np.full(len(pts), -1)
    q = nbtree.query(pts, predicate='within')
    for pi, ni in zip(q[0][::-1], q[1][::-1]):
        res[pi] = ni
    return res


def by_nb(idx, vals=None, dtype=float):
    idx = R(idx)
    v = np.ones(len(idx)) if vals is None else R(vals)
    s = pd.Series(v).groupby(idx).sum()
    return s.reindex(range(NB)).fillna(0).astype(dtype).values


# ---------------------------------------------------------------- 1 roofs
sol = loadj(DL + 'cityg_c40solarmap.json.gz')['features']
bg = feats_to_geoms(sol)
P = pd.DataFrame([f['properties'] for f in sol])
P['geom_area'] = shapely.area(bg)
V['solar_features'] = len(sol)
V['solar_sum_geom_area_m2_all'] = float(P.geom_area.sum())
V['solar_sum_attr_Area_m2_all'] = float(P.Area.sum())
V['solar_attr_Area_over_geom_median'] = float((P.Area / P.geom_area).median())
V['solar_n_Height_zero'] = int((P.Height == 0).sum())
rp = shapely.point_on_surface(bg)
P['nb_idx'] = nb_of_points(rp)
V['solar_features_repoint_inside_municipality'] = int((P.nb_idx >= 0).sum())
V['solar_features_repoint_outside'] = int((P.nb_idx < 0).sum())
btree = STRtree(bg)
nbi, bi = btree.query(nbg, predicate='intersects')  # row0 = nb idx, row1 = building idx
V['solar_features_intersecting_municipality'] = int(len(np.unique(bi)))
inter = shapely.area(shapely.intersection(bg[bi], nbg[nbi]))
nb['roof_area_m2'] = by_nb(nbi, inter)
V['roof_clipped_total_m2'] = float(nb.roof_area_m2.sum())
ub = shapely.union_all(bg)
V['buildings_union_area_m2'] = float(ub.area)
V['buildings_overlap_m2'] = float(P.geom_area.sum() - ub.area)

inn = P[P.nb_idx >= 0]
nb['buildings_n'] = by_nb(inn.nb_idx, None, int)
nb['roof_area_bldg_assigned_m2'] = by_nb(inn.nb_idx, inn.geom_area)
nb['roof_area_attr_Area_m2'] = by_nb(inn.nb_idx, inn.Area)
nb['roof_solar_usable_m2'] = by_nb(inn.nb_idx, inn.USAB_AREA)
nb['solar_kwp'] = by_nb(inn.nb_idx, inn.KWP)
nb['solar_kwh_year'] = by_nb(inn.nb_idx, inn.KWH_YEAR)
sm = inn[inn.geom_area < 50]
nb['buildings_lt_50m2_n'] = by_nb(sm.nb_idx, None, int)
nb['roof_share_of_area_pct'] = 100 * nb.roof_area_m2 / nb.area_m2
nb['roof_solar_usable_share_pct'] = 100 * nb.roof_solar_usable_m2 / nb.roof_area_bldg_assigned_m2.replace(0, np.nan)

# ---------------------------------------------------------------- municipal / school buildings
layers = {
    'school': D + 'raw/gis/layers/schools.geojson',
    'nursery': D + 'raw/gis/layers/nurseries.geojson',
    'friendship_club': D + 'raw/gis/layers/friendship.geojson',
    'clinic': D + 'raw/gis/layers/clinics.geojson',
    'admin_building': '/tmp/athens_capacity/dl/kt_dioikisis.json',      # City WFS geonode:kt_dioikisis
    'municipal_service': '/tmp/athens_capacity/dl/pois_yperesies_da.json',  # City WFS geonode:pois_yperesies_da
}
rows = []
for lname, path in layers.items():
    j = loadj(path)
    assert '2100' in j['crs']['properties']['name'], path
    pts, nm = [], []
    for f in j['features']:
        gg = shape(f['geometry'])
        for p in (list(gg.geoms) if hasattr(gg, 'geoms') else [gg]):
            pts.append(p); pr = f['properties']; nm.append(pr.get('name') or pr.get('sc_descr') or pr.get('label') or '')
    V[f'pts_{lname}_features'] = len(j['features']); V[f'pts_{lname}_points'] = len(pts)
    pa = np.array(pts, dtype=object); pn = nb_of_points(pa)
    for i, p in enumerate(pts):
        rows.append(dict(layer=lname, x=p.x, y=p.y, pt_nb=int(pn[i]), name=nm[i]))
PT = pd.DataFrame(rows)
ptg = shapely.points(PT.x.values, PT.y.values)
PT['inside_muni'] = PT.pt_nb >= 0
cont = {}
for pi, b_ in zip(*btree.query(ptg, predicate='within')):
    cont.setdefault(pi, []).append(b_)
nn = btree.query_nearest(ptg, max_distance=30, return_distance=True, all_matches=False)
nearmap = {int(a): (int(b), float(d)) for a, b, d in zip(nn[0][0], nn[0][1], nn[1])}
d30 = btree.query(ptg, predicate='dwithin', distance=30)
n30 = pd.Series(d30[0]).value_counts()
bidx, how, dist = [], [], []
for i in range(len(PT)):
    c = cont.get(i, [])
    if c:
        bidx.append(min(c, key=lambda k: P.geom_area[k])); how.append('contained'); dist.append(0.0)
    elif i in nearmap:
        bidx.append(nearmap[i][0]); how.append('nearest<=30m'); dist.append(nearmap[i][1])
    else:
        bidx.append(-1); how.append('unmatched'); dist.append(np.nan)
PT['bldg_idx'] = bidx; PT['match'] = how; PT['match_dist_m'] = dist
PT['n_bldgs_within_30m'] = [int(n30.get(i, 0)) for i in range(len(PT))]
PT['bldg_area_m2'] = [P.geom_area[b] if b >= 0 else np.nan for b in bidx]
PT['bldg_nb'] = [int(P.nb_idx[b]) if b >= 0 else -1 for b in bidx]
PT['bldg_type_attr'] = [P.Type[b] if b >= 0 else '' for b in bidx]
PT.drop(columns=['x', 'y']).to_csv(OUT + 'facility_to_building_matches.csv', index=False)

GROUPS = {'schools': ['school'], 'municipal_other': ['nursery', 'friendship_club', 'clinic', 'admin_building', 'municipal_service']}


def group_stats(ll):
    s = PT[PT.layer.isin(ll) & PT.inside_muni]
    m = s[s.match != 'unmatched']
    u = m.drop_duplicates('bldg_idx')
    idx = {b_ for pi, b_ in zip(*d30) if PT.layer[pi] in ll and PT.inside_muni[pi]}
    return dict(points=len(s), contained=int((s.match == 'contained').sum()), nearest30=int((s.match == 'nearest<=30m').sum()),
                unmatched=int((s.match == 'unmatched').sum()),
                points_with_gt1_bldg_within_30m=int((s.n_bldgs_within_30m > 1).sum()),
                points_with_gt3_bldg_within_30m=int((s.n_bldgs_within_30m > 3).sum()),
                unique_buildings=len(u), points_sharing_building=int(len(m) - len(u)),
                roof_area_matched_m2=float(u.bldg_area_m2.sum()),
                roof_area_upper_bound_all_bldgs_within_30m_m2=float(P.geom_area.values[list(idx)].sum()) if idx else 0.0,
                matched_median_area_m2=float(u.bldg_area_m2.median()) if len(u) else 0.0)


V['match_schools'] = group_stats(GROUPS['schools'])
V['match_municipal_other'] = group_stats(GROUPS['municipal_other'])
V['match_all_facilities_union'] = group_stats(GROUPS['schools'] + GROUPS['municipal_other'])
for l in layers:
    V['match_layer_' + l] = group_stats([l])
V['points_outside_municipality'] = {l: int(((PT.layer == l) & ~PT.inside_muni).sum()) for l in layers}
for gname, ll in GROUPS.items():
    s = PT[PT.layer.isin(ll) & PT.inside_muni]
    m = s[s.match != 'unmatched']
    u = m.drop_duplicates('bldg_idx')
    nb[f'{gname}_points_n'] = by_nb(s.pt_nb, None, int)
    nb[f'{gname}_points_matched_n'] = by_nb(m.pt_nb, None, int)
    nb[f'{gname}_buildings_n'] = by_nb(u.bldg_nb, None, int)
    nb[f'{gname}_roof_area_m2'] = by_nb(u.bldg_nb, u.bldg_area_m2)
sb = set(PT[PT.layer.isin(GROUPS['schools'])].bldg_idx) - {-1}
mb = set(PT[PT.layer.isin(GROUPS['municipal_other'])].bldg_idx) - {-1}
V['buildings_matched_by_both_school_and_municipal_other'] = len(sb & mb)
V['school_and_municipal_union_unique_buildings'] = len(sb | mb)
V['school_and_municipal_union_roof_m2'] = float(P.geom_area.values[list(sb | mb)].sum())

# ---------------------------------------------------------------- 2 streets
osm = loadj(D + 'streets/osm/osm_named_streets_athens.json.gz')
V['osm_timestamp'] = osm['osm3s']['timestamp_osm_base']
ways = [e for e in osm['elements'] if e['type'] == 'way' and len(e.get('geometry', [])) >= 2]
lines = np.array([shapely.LineString([(g['lon'], g['lat']) for g in e['geometry']]) for e in ways], dtype=object)
lines = shapely.segmentize(proj(lines, T2100), 10.0)
tags = [e['tags'] for e in ways]
hw = np.array([t.get('highway') for t in tags])

# DEFAULT WIDTHS (m) -- documented in README.md
CARR = {'trunk': (14.0, 7.5), 'primary': (12.0, 7.0), 'secondary': (9.5, 6.0), 'tertiary': (7.5, 5.0),
        'unclassified': (6.0, 4.5), 'residential': (6.0, 4.0)}  # (two-way carriageway, one-way carriageway)
SIDEWALK_BOTH, SIDEWALK_ONE = 4.0, 2.0
TOTAL_ONLY = {'living_street': 6.0, 'pedestrian': 6.0}
LANE_W = 3.0


def fnum(s):
    if s is None: return None
    m = re.match(r'\s*(\d+(?:[.,]\d+)?)', str(s))
    return float(m.group(1).replace(',', '.')) if m else None


def width(t, use_tags=True):
    h = t.get('highway'); ow = t.get('oneway') in ('yes', '1', 'true'); dual = t.get('dual_carriageway') == 'yes'
    w = fnum(t.get('width')) if use_tags else None
    wok = bool(w and 2 <= w <= 40)
    if h in TOTAL_ONLY:
        return (w if wok else TOTAL_ONLY[h]), ('width_tag' if wok else 'default')
    c = CARR[h][1 if ow else 0]; src = 'default'
    if use_tags:
        l = fnum(t.get('lanes'))
        if wok: c, src = w, 'width_tag'
        elif l and 1 <= l <= 8: c, src = l * LANE_W, 'lanes_tag'
    return c + (SIDEWALK_ONE if (ow and dual) else SIDEWALK_BOTH), src


wt, wsrc = zip(*[width(t) for t in tags]); wd = np.array([width(t, False)[0] for t in tags])
wt = np.array(wt); wsrc = np.array(wsrc)
co, ci = shapely.get_coordinates(lines, return_index=True)
ok = ci[:-1] == ci[1:]
a_, b_ = co[:-1][ok], co[1:][ok]
wi = ci[:-1][ok]
sn = nb_of_points(shapely.points((a_ + b_) / 2))
S = pd.DataFrame(dict(way=wi, len=np.hypot(*(b_ - a_).T), nb=sn, hw=hw[wi], w=wt[wi], wd=wd[wi], src=wsrc[wi]))
V['osm_ways'] = len(ways); V['osm_total_length_m'] = float(S.len.sum())
V['osm_length_outside_municipality_m'] = float(S[S.nb < 0].len.sum())
V['osm_ways_with_width_tag'] = int(sum(1 for t in tags if fnum(t.get('width'))))
V['osm_ways_with_lanes_tag'] = int(sum(1 for t in tags if fnum(t.get('lanes'))))
V['osm_length_share_width_tag_pct'] = float(100 * S[S.src == 'width_tag'].len.sum() / S.len.sum())
V['osm_length_share_lanes_tag_pct'] = float(100 * S[S.src == 'lanes_tag'].len.sum() / S.len.sum())
V['osm_highway_counts'] = {k: int(v) for k, v in pd.Series(hw).value_counts().items()}
Si = S[S.nb >= 0].copy()
Si['a'] = Si.len * Si.w; Si['ad'] = Si.len * Si.wd
for h in ['trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'living_street', 'pedestrian']:
    x = Si[Si.hw == h]; nb[f'street_len_{h}_m'] = by_nb(x.nb, x.len)
nb['street_len_total_m'] = by_nb(Si.nb, Si.len)
nb['street_len_pedestrian_and_living_m'] = nb.street_len_pedestrian_m + nb.street_len_living_street_m
nb['street_area_est_m2'] = by_nb(Si.nb, Si.a)
nb['street_area_est_low_m2'] = 0.7 * nb.street_area_est_m2
nb['street_area_est_high_m2'] = 1.3 * nb.street_area_est_m2
nb['street_area_defaults_only_m2'] = by_nb(Si.nb, Si.ad)
nb['street_area_est_share_pct'] = 100 * nb.street_area_est_m2 / nb.area_m2
nb['street_density_km_per_km2'] = nb.street_len_total_m / 1000 / nb.area_km2


# ---------------------------------------------------------------- 3 open / unsealed
def clipped_union_area(geoms):
    gu = shapely.union_all(geoms)
    out = np.zeros(NB)
    for n_ in nbtree.query(gu, predicate='intersects'):
        out[n_] = shapely.intersection(gu, nbg[n_]).area
    return out, gu


zg = feats_to_geoms(loadj(D + 'registry/gis/xriseis_green_only.geojson')['features'])
nb['green_zoning_m2'], zu = clipped_union_area(zg)
ua = loadj(DL + 'ua2012.geojson')['features']
uag = feats_to_geoms(ua)
uac = np.array([f['properties']['code_2012'] for f in ua])
sel = lambda codes: uag[np.isin(uac, codes)]
nb['ua2012_green_urban_m2'], u141 = clipped_union_area(sel(['14100']))
nb['ua2012_sports_leisure_m2'], u142 = clipped_union_area(sel(['14200']))
nb['ua2012_natural_forest_grass_m2'], u3 = clipped_union_area(sel(['31000', '32000']))
nb['ua2012_vacant_land_m2'], _ = clipped_union_area(sel(['13400']))
green_all = shapely.union_all([zu, u141, u142, u3])
nb['green_open_union_gross_m2'] = [shapely.intersection(green_all, nbg[n_]).area for n_ in range(NB)]
cand = btree.query(green_all, predicate='intersects')
green_net = shapely.difference(green_all, shapely.union_all(bg[cand]))
nb['green_open_union_net_of_roofs_m2'] = [shapely.intersection(green_net, nbg[n_]).area for n_ in range(NB)]
ua10 = loadj(DL + 'cityg_angLST_Athens_UrbanAtlas.json')['features']
ua10g = feats_to_geoms(ua10)
ua10c = np.array([f['properties']['CODE'] for f in ua10])
roadsel = ua10g[np.isin(ua10c, ['12210', '12220'])]
nb['ua2010_road_land_m2'] = clipped_union_area(roadsel)[0] if len(roadsel) else np.zeros(NB)
V['ua2012_codes_present'] = {k: int(v) for k, v in pd.Series(uac).value_counts().items()}
V['ua2012_has_road_class'] = bool(np.isin(uac, ['12210', '12220']).any())
V['ua2010_road_polygons'] = int(len(roadsel))
V['ua2012_coverage_of_municipality_pct'] = float(100 * shapely.intersection(shapely.union_all(uag), muni).area / muni.area)
V['ua2010_coverage_of_municipality_pct'] = float(100 * shapely.intersection(shapely.union_all(ua10g), muni).area / muni.area)
nb['residual_unclassified_raw_m2'] = nb.area_m2 - nb.roof_area_m2 - nb.green_open_union_net_of_roofs_m2 - nb.street_area_est_m2
nb['residual_open_m2'] = nb.residual_unclassified_raw_m2.clip(lower=0)
nb['residual_negative_flag'] = nb.residual_unclassified_raw_m2 < 0

# ---------------------------------------------------------------- 4 trees
stl = loadj(DL + 'stl2018.geojson.gz')['features']
nb['stl2018_canopy_m2'] = clipped_union_area(feats_to_geoms(stl))[0]
V['stl2018_polygons'] = len(stl)
g3857 = proj(shapely.make_valid(np.array([shape(f['geometry']) for f in nbj], dtype=object)), T3857)
frac, valid = [], []
with rasterio.open(DL + 'meta_chm_athens.tif') as r:
    V['chm_crs'] = str(r.crs); V['chm_res_m'] = list(r.res)
    arr = r.read(1); nd = r.nodata
    V['chm_nodata'] = None if nd is None else float(nd)
    for g_ in g3857:
        m = ~geometry_mask([g_], out_shape=arr.shape, transform=r.transform, all_touched=False)
        a = arr[m]; n = a.size
        frac.append(float(((a >= 3) & (a <= 100)).sum() / n) if n else np.nan)
        valid.append(float(((a >= 0) & (a <= 100)).sum() / n) if n else np.nan)
nb['chm_ge3m_pct'] = 100 * np.array(frac)
nb['canopy_chm_ge3m_m2'] = np.array(frac) * nb.area_m2
nb['chm_valid_pixel_pct'] = 100 * np.array(valid)
V['chm_min_valid_pixel_pct'] = float(nb.chm_valid_pixel_pct.min())
tc = pd.read_csv(D + 'treecover/treecover_by_neighbourhood.csv')[['neighbourhood', 'ua_stl2018_pct', 'metachm_ge3m_pct']].rename(
    columns={'neighbourhood': 'name', 'ua_stl2018_pct': 'stl_csv', 'metachm_ge3m_pct': 'chm_csv'})
nb = nb.merge(tc, on='name', how='left'); assert nb.stl_csv.notna().all()
nb['stl2018_pct'] = 100 * nb.stl2018_canopy_m2 / nb.area_m2
V['chm_pct_max_abs_diff_vs_treecover_csv'] = float((nb.chm_ge3m_pct - nb.chm_csv).abs().max())
V['stl_pct_max_abs_diff_vs_treecover_csv'] = float((nb.stl2018_pct - nb.stl_csv).abs().max())
nb['low_tree_group_stl_lt2pct'] = nb.stl_csv < 2
V['n_low_tree_group'] = int(nb.low_tree_group_stl_lt2pct.sum())
for t in (5, 10, 15, 30):
    nb[f'canopy_deficit_to_{t}pct_m2'] = (nb.area_m2 * t / 100 - nb.canopy_chm_ge3m_m2).clip(lower=0)
for d in (4, 6, 8):
    ca = math.pi * d * d / 4
    for t in (5, 10, 15, 30):
        nb[f'illustr_trees_{t}pct_crown{d}m'] = np.ceil(nb[f'canopy_deficit_to_{t}pct_m2'] / ca).astype(int)
pl = pd.read_csv(D + 'athenstrees/plantings_points.csv')
V['plantings_rows'] = len(pl); V['plantings_date_min'] = str(pl.planting_date.min()); V['plantings_date_max'] = str(pl.planting_date.max())
pl = pl[pl.planting_date >= '2024-01-01'].copy()
pl['nb'] = nb_of_points(proj(shapely.points(pl.lon.values, pl.lat.values), T2100))
V['plantings_rows_since_2024'] = len(pl); V['plantings_trees_since_2024'] = int(pl.num_trees.sum())
V['plantings_rows_outside_municipality'] = int((pl.nb < 0).sum())
pi_ = pl[pl.nb >= 0]
nb['plantings_since_2024_rows'] = by_nb(pi_.nb, None, int)
nb['plantings_since_2024_trees'] = by_nb(pi_.nb, pi_.num_trees, int)

# ---------------------------------------------------------------- 5 sites
sites = pd.read_csv(D + 'streets/sites_with_plantings.csv')
sites['nb'] = nb_of_points(proj(shapely.points(sites.lon.values, sites.lat.values), T2100))
nbname = nb.name.values
sites['nb_name'] = [nbname[i] if i >= 0 else '' for i in sites.nb]
V['sites_rows'] = len(sites); V['sites_outside_municipality'] = int((sites.nb < 0).sum())
V['sites_neighbourhood_field_mismatch_vs_point_in_polygon'] = int((sites.nb_name != sites.neighbourhood).sum())
V['sites_canopy_missing'] = int(sites.canopy_pct_150m.isna().sum())
V['sites_by_type'] = sites.site_type.value_counts().to_dict()
si = sites[sites.nb >= 0]
for typ, col in [('school', 'schools'), ('nursery', 'nurseries'), ('playground', 'playgrounds'), ('friendship_club', 'elderly_clubs')]:
    s = si[si.site_type == typ]
    nb[f'sites_{col}_n'] = by_nb(s.nb, None, int)
    x = s[s.canopy_pct_150m < 5]
    nb[f'sites_{col}_canopy150m_lt5pct_n'] = by_nb(x.nb, None, int)
cols_n = [f'sites_{c}_n' for c in ('schools', 'nurseries', 'playgrounds', 'elderly_clubs')]
nb['sites_all4_n'] = nb[cols_n].sum(axis=1)
nb['sites_all4_canopy150m_lt5pct_n'] = nb[[c[:-2] + '_canopy150m_lt5pct_n' for c in cols_n]].sum(axis=1)

pop = pd.read_csv(D + 'raw/population/population_by_neighbourhood.csv')[['name', 'pop_total']]
nb = nb.merge(pop, on='name', how='left')
V['pop_missing'] = int(nb.pop_total.isna().sum()); V['pop_total_sum'] = float(nb.pop_total.sum())

V['max_roof_share_pct'] = float(nb.roof_share_of_area_pct.max())
V['n_roof_share_gt100'] = int((nb.roof_share_of_area_pct > 100).sum())
V['n_residual_negative'] = int(nb.residual_negative_flag.sum())
V['buildings_n_sum'] = int(nb.buildings_n.sum())
V['roof_bldg_assigned_vs_clipped_diff_m2'] = float(nb.roof_area_bldg_assigned_m2.sum() - nb.roof_area_m2.sum())

nb.insert(1, 'community', nb.community_id.astype(str) + 'η ΔΚ')
nb.drop(columns=['chm_csv', 'stl_csv']).to_csv(OUT + 'capacity_by_neighbourhood.csv', index=False, float_format='%.3f')
nb.to_pickle('/tmp/athens_capacity/nb.pkl')
json.dump(V, open(OUT + 'validation.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('done')
