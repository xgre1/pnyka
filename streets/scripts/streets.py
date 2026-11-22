"""Street analysis. NOT RUN ON REAL DATA (OSM download was blocked). Usage: streets.py ways.json trees.json
ways.json/trees.json = Overpass `out geom` JSON (see overpass_query.txt). Writes streets.geojson/csv, streets_by_name.csv."""
import sys, json, collections; sys.path.insert(0, '.')
from common import *
from shapely.geometry import LineString
from shapely.ops import unary_union
O = '.'; BUF = 12
T_4326_2100_ = T_4326_2100; T_2100_4326 = Transformer.from_crs(2100, 4326, always_xy=True).transform
nb = load_nb(); order = nb.sort_values('area').reset_index(drop=True)
ways = json.load(open(sys.argv[1]))['elements']; tr = json.load(open(sys.argv[2]))['elements'] if len(sys.argv) > 2 else []
osm_pts = [transform(T_4326_2100_, Point(e['lon'], e['lat'])) for e in tr if e['type'] == 'node']
for e in tr:
    if e['type'] == 'way' and 'geometry' in e: osm_pts += [transform(T_4326_2100_, Point(p['lon'], p['lat'])) for p in e['geometry']]  # tree_row: vertices only (approximation)
tree_idx = STRtree(osm_pts)
segs = collections.defaultdict(list)   # (name, neighbourhood) -> [LineString in 2100]
for w in ways:
    if 'geometry' not in w or 'name' not in w.get('tags', {}): continue
    ll = LineString([(p['lon'], p['lat']) for p in w['geometry']])
    for _, r in order.iterrows():
        part = ll.intersection(r.geom)
        if part.is_empty: continue
        for g in ([part] if part.geom_type == 'LineString' else [x for x in getattr(part, 'geoms', []) if x.geom_type == 'LineString']):
            segs[(w['tags']['name'], r['name'])].append(transform(T_4326_2100_, g))
        ll = ll.difference(r.geom)   # each piece is assigned to the smallest polygon containing it
        if ll.is_empty: break
rows, feats = [], []
with rasterio.open(CHM) as src:
    for (name, n), lines in segs.items():
        ml = unary_union(lines); L = ml.length
        if L < 1: continue
        buf = ml.buffer(BUF, 16); p, t, px = canopy_pct_and_trees(src, transform(T_2100_3857, buf))
        osm = len(tree_idx.query(buf, predicate='contains'))
        px_area = px * (1.194 * np.cos(np.radians(38))) ** 2
        rows.append(dict(name=name, neighbourhood=n, length_m=round(L, 1), canopy_pct_12m=round(p, 2), est_trees=t, trees_per_100m=round(100 * t / L, 2), osm_trees=osm, buffer_px=px))
        feats.append(dict(type='Feature', geometry=json.loads(json.dumps(transform(T_2100_4326, ml).__geo_interface__)), properties=rows[-1]))
df = pd.DataFrame(rows); df.drop(columns='buffer_px').to_csv(O + 'streets.csv', index=False, encoding='utf-8')
json.dump(dict(type='FeatureCollection', features=feats), open(O + 'streets.geojson', 'w'), ensure_ascii=False)
def agg(g):  # pixel-weighted canopy; trees summed (trees in buffer overlaps at neighbourhood joins are negligible)
    return pd.Series(dict(neighbourhoods='; '.join(sorted(g.neighbourhood)), length_m=g.length_m.sum(), canopy_pct_12m=round(np.average(g.canopy_pct_12m, weights=g.buffer_px), 2),
        est_trees=g.est_trees.sum(), trees_per_100m=round(100 * g.est_trees.sum() / g.length_m.sum(), 2), osm_trees=g.osm_trees.sum()))
df.groupby('name').apply(agg).reset_index().to_csv(O + 'streets_by_name.csv', index=False, encoding='utf-8')
