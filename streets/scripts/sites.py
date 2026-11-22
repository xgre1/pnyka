import sys, json; sys.path.insert(0, '.')
from common import *
P = '/tmp/athens_prep/layers/'; O = '.'
nb = load_nb(); order = nb.sort_values('area').reset_index(drop=True)   # smallest polygon first, as in the original count build
T_2100_4326 = Transformer.from_crs(2100, 4326, always_xy=True).transform
LAYERS = {  # file: (site_type, name field, category field, address field, dk field)
 'schools': ('school', 'sc_descr', 'sc_categor', 'sc_address', 'dk'),
 'nurseries': ('nursery', 'name', 'type', 'addres', 'dk_text'),
 'playgrounds': ('playground', 'synoikia', 'status', 'odos1', 'dk'),
 'friendship': ('friendship_club', 'name', 'type', 'tax_diefth', 'dk')}
rows = []
for key, (typ, fn, fc, fa, fd) in LAYERS.items():
    g = json.load(open(P + key + '.geojson'))
    assert '2100' in g['crs']['properties']['name']
    for ft in g['features']:
        geom = ft['geometry']; cs = [geom['coordinates']] if geom['type'] == 'Point' else geom['coordinates']
        for c in cs:
            E, N = c[:2]; lon, lat = T_2100_4326(E, N); pt = Point(lon, lat)
            hit = [r['name'] for _, r in order.iterrows() if r.geom.contains(pt)]
            p = ft['properties']
            rows.append(dict(site_type=typ, name=p.get(fn) or '', category=p.get(fc) or '', address=p.get(fa) or '', dk=p.get(fd) or '',
                             neighbourhood=hit[0] if hit else None, lat=round(lat, 6), lon=round(lon, 6), E2100=E, N2100=N))
df = pd.DataFrame(rows); print('total points', len(df), df.groupby('site_type').size().to_dict())
print('outside polygons:', df[df.neighbourhood.isna()].groupby('site_type').size().to_dict())
df = df[df.neighbourhood.notna()].reset_index(drop=True)
c150, c50, t50, c150n = [], [], [], []
with rasterio.open(CHM) as src:
    for _, r in df.iterrows():
        pt2100 = Point(r.E2100, r.N2100)
        out = {}
        for rad in (50, 150):
            g = transform(T_2100_3857, pt2100.buffer(rad, 64))
            p, t, n = canopy_pct_and_trees(src, g, with_trees=(rad == 50)); out[rad] = (p, t)
        c150.append(out[150][0]); c50.append(out[50][0]); t50.append(out[50][1])
df['canopy_pct_150m'] = np.round(c150, 2); df['canopy_pct_50m'] = np.round(c50, 2); df['est_trees_50m'] = t50
df = df.drop(columns=['E2100', 'N2100'])
df.to_csv(O + 'sites.csv', index=False, encoding='utf-8')
feats = [dict(type='Feature', geometry=dict(type='Point', coordinates=[r.lon, r.lat]), properties={k: (None if pd.isna(v) else (v.item() if hasattr(v, 'item') else v)) for k, v in r.items() if k not in ('lat', 'lon')} | dict(lat=r.lat, lon=r.lon)) for _, r in df.iterrows()]
json.dump(dict(type='FeatureCollection', features=feats), open(O + 'sites.geojson', 'w'), ensure_ascii=False)
# checks vs neighbourhoods.csv
ex = pd.read_csv('.').set_index('name')
m = {'school': 'n_schools', 'nursery': 'n_nurseries', 'playground': 'n_playgrounds', 'friendship_club': 'n_friendship_clubs'}
for t, col in m.items():
    mine = df[df.site_type == t].groupby('neighbourhood').size().reindex(ex.index).fillna(0)
    print(t, len(df[df.site_type == t]), 'csv total', int(ex[col].sum()), 'per-nb mismatches', int((mine != ex[col]).sum()))
print('pct range', df[['canopy_pct_150m', 'canopy_pct_50m']].min().tolist(), df[['canopy_pct_150m', 'canopy_pct_50m']].max().tolist())
print('lat', df.lat.min(), df.lat.max(), 'lon', df.lon.min(), df.lon.max())
