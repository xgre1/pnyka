"""Layer albedo_2025: mean summer-2025 broadband albedo of the BUILT/BARE surfaces (roofs, roads, squares) per neighbourhood.
Input: the Sentinel-2 L2A median composite made by roofs/scripts/02_composite.py (tile 34SGH, June-August 2025,
cloud < 5 %, SCL-masked, reflectance already scaled; grid EPSG:32634, 10 m, transform stored in the .npz).
Albedo = 0.2266 B2 + 0.1236 B3 + 0.1573 B4 + 0.3417 B8 + 0.1170 B11 + 0.0338 B12
(Bonafoni & Sekertekin 2020, IEEE GRSL 17(9):1618-1622, doi:10.1109/LGRS.2020.2967085), same as roofs/scripts/03_roofs.py.
Why only non-vegetated pixels (NDVI < 0.3, the roofs/ 'green' cut): over all pixels, pine forest (Lykavittos) is the darkest
surface in the city, so 'low albedo = worse' would flag the parks. Masking vegetation keeps the layer about dark roofs/asphalt.
Neighbourhood value = mean over the non-vegetated pixels whose centre is inside the polygon and that have >= 1 SCL-valid scene.
Usage: python -I albedo_2025.py <repo_root> <composite_2025_summer.npz>"""
import csv, json, sys
import numpy as np
from affine import Affine
from rasterio.features import geometry_mask
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

NDVI_GREEN = 0.30
D = sys.argv[1].rstrip('/') + '/'
z = np.load(sys.argv[2])
B = list(z['bands']); M = z['masked']; ok = z['n_valid'] > 0
t = z['transform']; T = Affine(t[0], t[1], t[2], t[3], t[4], t[5])
W = dict(blue=0.2266, green=0.1236, red=0.1573, nir=0.3417, swir16=0.1170, swir22=0.0338)
V = sum(w * M[B.index(b)] for b, w in W.items())
red, nir = M[B.index('red')], M[B.index('nir')]
with np.errstate(invalid='ignore', divide='ignore'):
    ND = (nir - red) / (nir + red)
V = np.where(ok & np.isfinite(V) & (ND < NDVI_GREEN), V, np.nan)

tr = Transformer.from_crs(4326, 32634, always_xy=True).transform
g = json.load(open(D + 'neighbourhoods.geojson', encoding='utf-8'))
rows = []
for f in g['features']:
    p = transform(tr, shape(f['geometry']))
    m = ~geometry_mask([mapping(p)], V.shape, T, all_touched=False)
    if not np.isfinite(V[m]).any():
        m = ~geometry_mask([mapping(p)], V.shape, T, all_touched=True)
    rows.append((f['properties']['name'], round(float(np.nanmean(V[m])), 3), int(np.isfinite(V[m]).sum())))
with open(D + 'raw/layers/albedo_2025.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh); w.writerow(['name', 'value']); w.writerows([r[:2] for r in rows])
json.dump(dict(id='albedo_2025', name='Πόσο ανοιχτόχρωμες είναι ταράτσες και δρόμοι (albedo 2025)', unit='albedo (0 έως 1)', kind='rec',
               source='Copernicus Sentinel-2 L2A (ESA, μέσω Earth Search/AWS), διάμεσος 20 καθαρών σκηνών Ιουνίου-Αυγούστου 2025, '
                      'ανάλυση 10 m, άδεια Copernicus (ελεύθερη χρήση με αναφορά); τύπος Bonafoni & Sekertekin 2020',
               note='Εκτίμηση από δορυφόρο μόνο στις επιφάνειες χωρίς βλάστηση· το πράσινο εξαιρείται.',
               worse='low'), open(D + 'raw/layers/albedo_2025.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
v = [r[1] for r in rows]
print(len(rows), 'min', min(v), 'max', max(v), 'min pixels', min(r[2] for r in rows))
