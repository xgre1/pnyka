"""Layer ndvi_2025: mean summer-2025 NDVI per neighbourhood.
Input: the Sentinel-2 L2A median composite made by roofs/scripts/02_composite.py (tile 34SGH, June-August 2025,
cloud < 5 %, SCL-masked, reflectance already scaled; grid EPSG:32634, 10 m, transform stored in the .npz).
NDVI = (B08 - B04) / (B08 + B04) per pixel; neighbourhood value = mean over the pixels whose centre is inside the polygon
and that have >= 1 SCL-valid scene.
Usage: python -I ndvi_2025.py <repo_root> <composite_2025_summer.npz>"""
import csv, json, sys
import numpy as np
from affine import Affine
from rasterio.features import geometry_mask
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

D = sys.argv[1].rstrip('/') + '/'
z = np.load(sys.argv[2])
B = list(z['bands']); M = z['masked']; ok = z['n_valid'] > 0
t = z['transform']; T = Affine(t[0], t[1], t[2], t[3], t[4], t[5])
red, nir = M[B.index('red')], M[B.index('nir')]
with np.errstate(invalid='ignore', divide='ignore'):
    V = (nir - red) / (nir + red)
V = np.where(ok & np.isfinite(V), V, np.nan)

tr = Transformer.from_crs(4326, 32634, always_xy=True).transform
g = json.load(open(D + 'neighbourhoods.geojson', encoding='utf-8'))
rows = []
for f in g['features']:
    p = transform(tr, shape(f['geometry']))
    m = ~geometry_mask([mapping(p)], V.shape, T, all_touched=False)
    if not np.isfinite(V[m]).any():
        m = ~geometry_mask([mapping(p)], V.shape, T, all_touched=True)
    rows.append((f['properties']['name'], round(float(np.nanmean(V[m])), 3), int(np.isfinite(V[m]).sum())))
with open(D + 'raw/layers/ndvi_2025.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh); w.writerow(['name', 'value']); w.writerows([r[:2] for r in rows])
json.dump(dict(id='ndvi_2025', name='Πράσινο από δορυφόρο (NDVI 2025)', unit='NDVI (-1 έως 1)', kind='rec',
               source='Copernicus Sentinel-2 L2A (ESA, μέσω Earth Search/AWS), διάμεσος 20 καθαρών σκηνών Ιουνίου-Αυγούστου 2025, '
                      'ανάλυση 10 m, άδεια Copernicus (ελεύθερη χρήση με αναφορά)',
               note='Δείκτης βλάστησης από δορυφόρο: δεν ξεχωρίζει δέντρα από γκαζόν ή ξερά χόρτα.',
               worse='low'), open(D + 'raw/layers/ndvi_2025.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
v = [r[1] for r in rows]
print(len(rows), 'min', min(v), 'max', max(v), 'min pixels', min(r[2] for r in rows))
