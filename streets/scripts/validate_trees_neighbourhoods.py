"""Validation: (a) neighbourhood canopy vs existing CSV; (b) local-max tree count vs National Garden inventory."""
import sys, json; sys.path.insert(0, '.')
from common import *
O = '.'
nb = load_nb(); ex = pd.read_csv(O + 'treecover/treecover_by_neighbourhood.csv').set_index('neighbourhood')
res = []
with rasterio.open(CHM) as src:
    for _, r in nb.iterrows():
        g = transform(T_4326_3857, r.geom)
        p, _, n = canopy_pct_and_trees(src, g, with_trees=False)
        res.append((r['name'], p, n))
    df = pd.DataFrame(res, columns=['neighbourhood', 'canopy_pct', 'px']).set_index('neighbourhood')
    df['existing'] = ex.metachm_ge3m_pct
    d = df.dropna()
    out = dict(n=len(d), corr=float(np.corrcoef(d.canopy_pct, d.existing)[0, 1]), mad=float((d.canopy_pct - d.existing).abs().mean()), max_abs=float((d.canopy_pct - d.existing).abs().max()), n_nan_mine=int(df.canopy_pct.isna().sum()))
    # National Garden
    dd = json.load(open('/tmp/athens_treecover/dl/cityg_dendra.json'))['features']
    pts = np.array([f['geometry']['coordinates'] for f in dd]); cond = np.array([f['properties'].get('Condition') for f in dd])
    from shapely.geometry import MultiPoint
    hull = MultiPoint([tuple(p) for p in pts]).convex_hull
    hull3857 = transform(T_4326_3857, hull)
    p, trees, n = canopy_pct_and_trees(src, hull3857)
    out['natgarden'] = dict(inventory_points=len(pts), inventory_existing=int((cond == 'Existing').sum()), conditions={k: int((cond == k).sum()) for k in set(cond)},
        hull_area_ha=hull3857.area * np.cos(np.radians(38)) ** 2 / 1e4, canopy_pct_in_hull=p, detected_maxima=trees,
        ratio_all=trees / len(pts), ratio_existing=trees / max(1, int((cond == 'Existing').sum())))
    # sensitivity to window size
    sens = {}
    import common
    for w in (3, 5, 7, 9):
        common.LM_WIN = w; _, t, _ = canopy_pct_and_trees(src, hull3857); sens[w] = t
    out['natgarden']['maxima_by_window_px'] = sens
df.to_csv('/tmp/athens_streets/nb_canopy_check.csv')
json.dump(out, open('/tmp/athens_streets/validation.json', 'w'), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
