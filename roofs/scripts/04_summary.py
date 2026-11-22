"""Step 4. Counts, sensitivity and validation against the Climate Action Plan 2022 list of 13 school green roofs.
Reads roofs/roof_status.csv, roofs/work/thresholds*.json, roofs/work/roof_status_shrink*.csv, <work_dir>/all_roofs_stats.csv.gz,
raw/gis/layers/schools.geojson and the solar-map layer. Prints the tables (pasted into roofs/summary.md) and writes roofs/work/validation_cap2022.csv.
Usage: python -I 04_summary.py <repo_root> <work_dir>"""
import gzip, json, sys
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from pyproj import Transformer

D = sys.argv[1].rstrip('/') + '/'
WK = sys.argv[2].rstrip('/') + '/'
R = pd.read_csv(D + 'roofs/roof_status.csv')
TH = json.load(open(D + 'roofs/work/thresholds.json'))
GROUPS = {'schools': ['school'], 'municipal_other': ['nursery', 'friendship_club', 'clinic', 'admin_building', 'municipal_service']}
ST = ['green', 'bright', 'ordinary', 'too_small']


def uniq(df, ll):
    return df[df.layer.isin(ll) & df.inside_muni].drop_duplicates('bldg_idx')


def table(df, col='status'):
    out = []
    for gname, ll in list(GROUPS.items()) + [('all_facilities', sum(GROUPS.values(), []))]:
        u = uniq(df, ll)
        out.append(dict(group=gname, buildings=len(u), roof_m2=round(u.roof_m2.sum()),
                        **{f'{s}_n': int((u[col] == s).sum()) for s in ST}, **{f'{s}_m2': round(u.roof_m2[u[col] == s].sum()) for s in ST}))
    return pd.DataFrame(out)


print('## Main result (shrink 5 m, NDVI>=0.30, albedo top 10%)')
print(table(R).to_markdown(index=False))
print('\n## Per layer (unique buildings per layer)')
rows = []
for l in sum(GROUPS.values(), []):
    u = uniq(R, [l]); rows.append(dict(layer=l, buildings=len(u), roof_m2=round(u.roof_m2.sum()), **{s: int((u.status == s).sum()) for s in ST}))
print(pd.DataFrame(rows).to_markdown(index=False))
print('\n## SCL-mask check: status without SCL mask vs with')
u = uniq(R, sum(GROUPS.values(), []))
print(pd.crosstab(u.status, u.status_nomask).to_markdown())

print('\n## Sensitivity (all facilities, unique buildings, measurable = >=4 pixels): green / bright / ordinary')
u = uniq(R, sum(GROUPS.values(), [])); mm = u[u.n_pixels >= 4]
sens = []
for ndt in (0.25, 0.30, 0.35):
    r = {'NDVI >=': ndt}
    for t in (5, 10, 20):
        cut = TH['albedo_cuts'][f'top{t}']
        g = mm.ndvi >= ndt; b = ~g & (mm.albedo >= cut)
        r[f'albedo top {t}% (cut {cut:.3f})'] = f'{int(g.sum())} / {int(b.sum())} / {int((~g & ~b).sum())}'
    sens.append(r)
print(pd.DataFrame(sens).to_markdown(index=False))
print(f'measurable buildings: {len(mm)} of {len(u)}')

print('\n## Sensitivity to the shrink distance (NDVI>=0.30, top 10%, cut recomputed each time)')
for s in ('2.5', '0'):
    t = json.load(open(D + f'roofs/work/thresholds_shrink{s}.json'))
    print(f'shrink {s} m: reference roofs {t["n_reference_roofs"]}, albedo cut {t["albedo_cut"]:.3f}')
    print(table(pd.read_csv(D + f'roofs/work/roof_status_shrink{s}.csv')).to_markdown(index=False))

# ---------------- validation: CAP 2022 p.52, 13 school complexes with green roofs (built earlier, being replanted in 2022)
# indices = feature order in raw/gis/layers/schools.geojson (= point_order_in_layer for layer 'school').
# Rule: every school point whose sc_address names the CAP street(s) with the same (or no) street number.
# Exceptions, by name because the address does not match: 49o (layer: Kipon & Acharnon / Tsounta & Kipon), 134o (layer: Erythraias 14-18).
CAP = [
    ('9o-71o Nip., 71o-84o Dim. / Gen. Kolokotroni (1st DK)', [68, 154, 210]),
    ('8o-67o Nip., 2o-5o Dim. / Damareos 65 (2nd DK)', [225, 365, 389]),
    ('90o Dim., 123o Dim. / Amfikratous 6 & Vathykleous (2nd DK)', [301, 208, 307, 76]),
    ('137o Dim. / Alkifronos 51-53 (3rd DK)', [191]),
    ('87o Dim. / Orfeos & Achniadon 3-5 (3rd DK)', [396, 374]),
    ('30o Nip., 60o Dim. / Aimonos & Tilefanous (4th DK)', [155, 391]),
    ('127o Dim. / Kallipoleos 10 (4th DK)', [175]),
    ('173o Dim. / Ariovarzanou & Efthykratous (5th DK)', [19]),
    ('49o Lykeio / Acharnon 411-415 (5th DK)', [245, 88]),
    ('172o Dim. / Skopelou 67-71 (6th DK)', [8]),
    ('66o-80o Nip., 53o-99o Dim. / Ygeias 11a (6th DK)', [160, 222, 318]),
    ('134o Dim. / L. K. Tsaldari 11 (7th DK)', [366]),
    ('2o Peiramatiko Gymnasio / P. Kyriakou & Tsocha (7th DK)', [190, 259, 272]),
]
A = pd.read_csv(WK + 'all_roofs_stats.csv.gz')
sol = json.load(gzip.open(D + 'raw/treecover/dl/cityg_c40solarmap.json.gz', 'rt', encoding='utf8'))['features']
t21 = Transformer.from_crs(4326, 2100, always_xy=True)
bg = shapely.make_valid(np.array([shape(f['geometry']) for f in sol], dtype=object))
bg = shapely.transform(bg, lambda c: np.column_stack(t21.transform(c[:, 0], c[:, 1])))
tree = shapely.STRtree(bg)
sch = json.load(open(D + 'raw/gis/layers/schools.geojson', encoding='utf8'))['features']
spt = np.array([list(shape(f['geometry']).geoms)[0] if hasattr(shape(f['geometry']), 'geoms') else shape(f['geometry']) for f in sch], dtype=object)
RS = R[R.layer == 'school'].set_index('point_order_in_layer')
MEAS = (A.n_pixels >= 4).values
GREEN = MEAS & (A.ndvi >= 0.30).values


def near(idxs, dist=30):
    b = set()
    for i in idxs:
        b |= set(tree.query(spt[i], predicate='dwithin', distance=dist).tolist())
    return sorted(b)


val = []
listed = set()
for label, idxs in CAP:
    listed |= set(idxs)
    mb = [int(RS.bldg_idx[i]) for i in idxs if i in RS.index]
    mst = [RS.status[i] for i in idxs if i in RS.index]
    nb30 = near(idxs)
    val.append(dict(complex=label, school_points=';'.join(sch[i]['properties']['sc_descr'] for i in idxs),
                    matched_bldgs=';'.join(map(str, sorted(set(mb)))), matched_status=';'.join(sorted(set(mst))) or 'unmatched',
                    matched_max_ndvi=round(max([RS.ndvi[i] for i in idxs if i in RS.index and RS.n_pixels[i] >= 4], default=np.nan), 3),
                    bldgs_within_30m=len(nb30), measurable_within_30m=int(MEAS[nb30].sum()), green_within_30m=int(GREEN[nb30].sum()),
                    max_ndvi_within_30m=round(float(np.nanmax(np.where(MEAS[nb30], A.ndvi.values[nb30], np.nan))), 3) if MEAS[nb30].any() else np.nan))
V = pd.DataFrame(val)
V.to_csv(D + 'roofs/work/validation_cap2022.csv', index=False)
print('\n## Validation: CAP 2022 13 school complexes')
print(V.drop(columns=['school_points']).to_markdown(index=False))
mhit = V.matched_status.str.contains('green').sum(); mmeas = (~V.matched_max_ndvi.isna()).sum()
print(f'matched building green: {mhit}/13 (complexes with a measurable matched building: {mmeas})')
print(f'any green building within 30 m: {(V.green_within_30m > 0).sum()}/13 (complexes with a measurable building within 30 m: {(V.measurable_within_30m > 0).sum()})')
# control: every other school point inside the municipality
listed_b = {int(RS.bldg_idx[i]) for i in listed if i in RS.index}  # buildings of the listed complexes are not controls
oth = [i for i in range(len(sch)) if i not in listed and i in RS.index and bool(RS.inside_muni[i]) and int(RS.bldg_idx[i]) not in listed_b]
g_any = m_any = 0
for i in oth:
    nb30 = near([i]); m_any += int(MEAS[nb30].any()); g_any += int(GREEN[nb30].any())
print(f'control, other school points: green building within 30 m for {g_any} of {m_any} points with a measurable building within 30 m ({len(oth)} points)')
oth_r = RS.loc[oth]; oth_r = oth_r[oth_r.n_pixels >= 4].drop_duplicates('bldg_idx')
print(f'control, other schools matched building: green {int((oth_r.status == "green").sum())} of {len(oth_r)} measurable')
