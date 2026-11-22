"""Layer elevation: mean surface elevation (m) per neighbourhood, Copernicus DEM GLO-30.
Download (anonymous GET, AWS open data):
  https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N37_00_E023_00_DEM/Copernicus_DSM_COG_10_N37_00_E023_00_DEM.tif
  https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N38_00_E023_00_DEM/Copernicus_DSM_COG_10_N38_00_E023_00_DEM.tif
  (Athens crosses 38 N, so both tiles are needed.)
Grid EPSG:4326, 1 arc-second (~30 m). Neighbourhood value = mean over pixels whose centre is inside the polygon.
Usage: python -I elevation.py <repo_root> <N37.tif> <N38.tif>"""
import csv, json, sys
import numpy as np, rasterio
from rasterio.merge import merge
from rasterio.features import geometry_mask
from shapely.geometry import shape, mapping

D = sys.argv[1].rstrip('/') + '/'
src = [rasterio.open(p) for p in sys.argv[2:4]]
A, T = merge(src, bounds=(23.66, 37.93, 23.81, 38.05))
A = A[0].astype('float32')

g = json.load(open(D + 'neighbourhoods.geojson', encoding='utf-8'))
rows = []
for f in g['features']:
    p = shape(f['geometry'])
    m = ~geometry_mask([mapping(p)], A.shape, T, all_touched=False)
    if not m.any():
        m = ~geometry_mask([mapping(p)], A.shape, T, all_touched=True)
    rows.append((f['properties']['name'], round(float(A[m].mean())), int(m.sum())))
with open(D + 'raw/layers/elevation.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh); w.writerow(['name', 'value']); w.writerows([r[:2] for r in rows])
json.dump(dict(id='elevation', name='Υψόμετρο', unit='m', kind='rec',
               source='Copernicus DEM GLO-30 (ESA/Airbus, μέσω AWS Open Data), 2011-2015, ανάλυση 30 m, '
                      'ελεύθερη χρήση με αναφορά (άδεια Copernicus DEM)',
               note='Μοντέλο επιφάνειας: σε πυκνά δομημένα σημεία μετρά και το ύψος κτιρίων και δέντρων.',
               worse='none'), open(D + 'raw/layers/elevation.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
v = [r[1] for r in rows]
print(len(rows), 'min', min(v), 'max', max(v), 'min pixels', min(r[2] for r in rows))
