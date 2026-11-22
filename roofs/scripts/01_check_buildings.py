"""Step 1. Load the City solar-map layer (cityg_c40solarmap) and check that its feature order matches
bldg_idx in capacity/facility_to_building_matches.csv (compare bldg_area_m2 with polygon area, EPSG:2100).
Writes roofs/work/buildings_check.txt (small text log).
Usage: python -I roofs/scripts/01_check_buildings.py <repo_root>"""
import gzip, json, os, sys
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from pyproj import Transformer

D = sys.argv[1].rstrip('/') + '/'
SOL = D + 'raw/treecover/dl/cityg_c40solarmap.json.gz'  # same layer the capacity script used (City GeoServer geonode:cityg_c40solarmap)
os.makedirs(D + 'roofs/work', exist_ok=True)
T = Transformer.from_crs(4326, 2100, always_xy=True)
sol = json.load(gzip.open(SOL, 'rt', encoding='utf8'))['features']
g = shapely.make_valid(np.array([shape(f['geometry']) for f in sol], dtype=object))
g = shapely.transform(g, lambda c: np.column_stack(T.transform(c[:, 0], c[:, 1])))
area = shapely.area(g)
m = pd.read_csv(D + 'capacity/facility_to_building_matches.csv')
mm = m[m.bldg_idx >= 0]
d = np.abs(area[mm.bldg_idx.values] - mm.bldg_area_m2.values)
lines = [f'solar features: {len(sol)}', f'match rows: {len(m)}, with bldg_idx>=0: {len(mm)}',
         f'max |area(bldg_idx) - bldg_area_m2| over all matched rows: {d.max():.6f} m2',
         f'rows with diff > 0.01 m2: {(d > 0.01).sum()}']
for _, r in mm.head(5).iterrows():
    lines.append(f'  idx {r.bldg_idx}: csv {r.bldg_area_m2:.3f}  polygon {area[r.bldg_idx]:.3f}')
open(D + 'roofs/work/buildings_check.txt', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
