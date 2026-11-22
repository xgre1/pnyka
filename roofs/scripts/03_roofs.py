"""Step 3. Per-roof NDVI and broadband albedo for every solar-map building, then classify the facility buildings.
- Polygon (WGS84) -> make_valid -> EPSG:32634 (tile CRS, metric) -> buffer(-5 m).
- Pixels = 10 m composite pixels whose centre lies inside the shrunk polygon and that have >=1 SCL-valid scene.
- Per-pixel NDVI = (B08-B04)/(B08+B04); albedo = 0.2266 B2 + 0.1236 B3 + 0.1573 B4 + 0.3417 B8 + 0.1170 B11 + 0.0338 B12
  (Bonafoni & Sekertekin 2020, IEEE GRSL 17(9):1618-1622, doi:10.1109/LGRS.2020.2967085). Roof value = median over its pixels.
- Fewer than 4 pixels -> too_small.
- Albedo cut = percentile over ALL solar-map roofs in the municipality (representative point inside neighbourhoods.geojson) with >=4 pixels.
- The same is computed from the composite WITHOUT the SCL mask (columns *_nomask) as a check that the cloud/snow mask does not remove bright roofs.
Writes (shrink 5 m, the method): roofs/roof_status.csv, roofs/work/thresholds.json, <work_dir>/all_roofs_stats.csv.gz.
Optional 3rd argument = other shrink in m (sensitivity only): writes roofs/work/roof_status_shrink<m>.csv and thresholds_shrink<m>.json.
Usage: python -I 03_roofs.py <repo_root> <work_dir> [shrink_m]"""
import gzip, json, sys
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from pyproj import Transformer

D = sys.argv[1].rstrip('/') + '/'
WK = sys.argv[2].rstrip('/') + '/'
SHRINK, MINPIX, NDVI_T, TOP = (float(sys.argv[3]) if len(sys.argv) > 3 else 5.0), 4, 0.30, 10
SUF = '' if SHRINK == 5.0 else f'_shrink{SHRINK:g}'
C = np.array([0.2266, 0.1236, 0.1573, 0.3417, 0.1170, 0.0338])  # B2 B3 B4 B8 B11 B12

z = np.load(WK + 'composite_2025_summer.npz')
assert list(z['bands']) == ['blue', 'green', 'red', 'nir', 'swir16', 'swir22']
a, _, x0, _, e, y0 = z['transform']
nval = z['n_valid']
H, W = nval.shape


def indices(M):
    with np.errstate(all='ignore'):
        nd = (M[3] - M[2]) / (M[3] + M[2])
    al = np.tensordot(C, M, axes=1)
    return nd.astype('float32'), al.astype('float32')


ND_m, AL_m = indices(z['masked'])
ND_u, AL_u = indices(z['unmasked'])

sol = json.load(gzip.open(D + 'raw/treecover/dl/cityg_c40solarmap.json.gz', 'rt', encoding='utf8'))['features']
g = shapely.make_valid(np.array([shape(f['geometry']) for f in sol], dtype=object))
t32 = Transformer.from_crs(4326, 32634, always_xy=True)
t21 = Transformer.from_crs(4326, 2100, always_xy=True)
gu = shapely.transform(g, lambda c: np.column_stack(t32.transform(c[:, 0], c[:, 1])))
g21 = shapely.transform(g, lambda c: np.column_stack(t21.transform(c[:, 0], c[:, 1])))
area21 = shapely.area(g21)
shr = shapely.buffer(gu, -SHRINK)
cen = shapely.centroid(g)  # WGS84 centroid (fine at building scale)

nb = json.load(open(D + 'neighbourhoods.geojson', encoding='utf8'))['features']
muni = shapely.union_all([shapely.make_valid(shape(f['geometry'])) for f in nb])
shapely.prepare(muni)
inmuni = shapely.contains(muni, shapely.point_on_surface(g))

rows = []
for i, p in enumerate(shr):
    r = dict(idx=i, n_pix_total=0, n_pixels=0, ndvi=np.nan, albedo=np.nan, n_pixels_nomask=0, ndvi_nomask=np.nan, albedo_nomask=np.nan,
             min_valid_scenes=np.nan)
    if not p.is_empty and p.area > 0:
        bx0, by0, bx1, by1 = p.bounds
        c0 = max(int(np.floor((bx0 - x0) / a)), 0); c1 = min(int(np.ceil((bx1 - x0) / a)), W)
        r0 = max(int(np.floor((y0 - by1) / a)), 0); r1 = min(int(np.ceil((y0 - by0) / a)), H)
        if c1 > c0 and r1 > r0:
            cc, rr = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
            inside = shapely.contains_xy(p, x0 + (cc + 0.5) * a, y0 - (rr + 0.5) * a)
            cc, rr = cc[inside], rr[inside]
            r['n_pix_total'] = len(cc)
            if len(cc):
                nd, al = ND_m[rr, cc], AL_m[rr, cc]; ok = np.isfinite(nd) & np.isfinite(al)
                r['n_pixels'] = int(ok.sum()); r['min_valid_scenes'] = int(nval[rr, cc].min())
                if ok.any(): r['ndvi'] = float(np.median(nd[ok])); r['albedo'] = float(np.median(al[ok]))
                nd, al = ND_u[rr, cc], AL_u[rr, cc]; ok = np.isfinite(nd) & np.isfinite(al)
                r['n_pixels_nomask'] = int(ok.sum())
                if ok.any(): r['ndvi_nomask'] = float(np.median(nd[ok])); r['albedo_nomask'] = float(np.median(al[ok]))
    rows.append(r)
A = pd.DataFrame(rows)
A['roof_m2'] = area21; A['in_municipality'] = inmuni
A['lat'] = shapely.get_y(cen); A['lon'] = shapely.get_x(cen)
if not SUF:
    A.to_csv(WK + 'all_roofs_stats.csv.gz', index=False, float_format='%.5f')

ref = A[A.in_municipality & (A.n_pixels >= MINPIX)]
ref_u = A[A.in_municipality & (A.n_pixels_nomask >= MINPIX)]
cuts = {f'top{t}': float(np.percentile(ref.albedo, 100 - t)) for t in (5, 10, 20)}
cuts_u = {f'top{t}': float(np.percentile(ref_u.albedo_nomask, 100 - t)) for t in (5, 10, 20)}
TH = dict(min_pixels=MINPIX, shrink_m=SHRINK, ndvi_green=NDVI_T, bright_top_pct=TOP, albedo_cut=cuts[f'top{TOP}'], albedo_cuts=cuts,
          albedo_cuts_nomask=cuts_u, n_reference_roofs=int(len(ref)), n_reference_roofs_nomask=int(len(ref_u)),
          n_solar_roofs=int(len(A)), n_solar_roofs_in_municipality=int(A.in_municipality.sum()),
          reference_albedo_median=float(ref.albedo.median()), reference_ndvi_share_ge030=float((ref.ndvi >= 0.30).mean()))
json.dump(TH, open(D + f'roofs/work/thresholds{SUF}.json', 'w'), indent=1)


def classify(n, nd, al, ndt, cut):
    return np.where(n < MINPIX, 'too_small', np.where(nd >= ndt, 'green', np.where(al >= cut, 'bright', 'ordinary')))


m = pd.read_csv(D + 'capacity/facility_to_building_matches.csv')
m['point_order_in_layer'] = m.groupby('layer').cumcount()
m = m[m.bldg_idx >= 0].copy()
s = A.set_index('idx').loc[m.bldg_idx.values].reset_index(drop=True)
m = m.reset_index(drop=True)
out = pd.DataFrame(dict(layer=m.layer, name=m.name, bldg_idx=m.bldg_idx, roof_m2=s.roof_m2.round(1), n_pixels=s.n_pixels,
                        ndvi=s.ndvi.round(4), albedo=s.albedo.round(4),
                        status=classify(s.n_pixels.values, s.ndvi.values, s.albedo.values, NDVI_T, cuts[f'top{TOP}']),
                        lat=s.lat.round(6), lon=s.lon.round(6), neighbourhood=m.bldg_nb,
                        neighbourhood_name=[nb[k]['properties']['name'] if k >= 0 else '' for k in m.bldg_nb],
                        inside_muni=m.inside_muni, match=m['match'], point_order_in_layer=m.point_order_in_layer,
                        min_valid_scenes=s.min_valid_scenes, n_pixels_nomask=s.n_pixels_nomask,
                        ndvi_nomask=s.ndvi_nomask.round(4), albedo_nomask=s.albedo_nomask.round(4),
                        status_nomask=classify(s.n_pixels_nomask.values, s.ndvi_nomask.values, s.albedo_nomask.values, NDVI_T, cuts_u[f'top{TOP}'])))
out.to_csv(D + ('roofs/roof_status.csv' if not SUF else f'roofs/work/roof_status{SUF}.csv'), index=False)
print(json.dumps(TH, indent=1))
print(out.status.value_counts())
