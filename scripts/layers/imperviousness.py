"""Layer imperviousness: mean sealed-soil share (%) per neighbourhood, Copernicus HRL Imperviousness Density 2018 (10 m).
Download (anonymous GET, EEA ArcGIS ImageServer; native grid is 10 m EPSG:3857, exported to EPSG:3035 10 m, nearest neighbour):
  https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_ImperviousnessDensity_2018/ImageServer/exportImage?bbox=5524800,1760800,5533900,1770400&bboxSR=3035&imageSR=3035&size=910,960&format=tiff&interpolation=RSP_NearestNeighbor&f=image
Values 0-100 = % sealed; > 100 treated as no data. Neighbourhood value = mean over pixels whose centre is inside the polygon.
Usage: python -I imperviousness.py <repo_root> <imd2018_3035_10m.tif>"""
import csv, json, sys
import numpy as np, rasterio
from rasterio.features import geometry_mask
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

D = sys.argv[1].rstrip('/') + '/'
with rasterio.open(sys.argv[2]) as r:
    A = r.read(1).astype('float32'); T = r.transform
A[A > 100] = np.nan

tr = Transformer.from_crs(4326, 3035, always_xy=True).transform
g = json.load(open(D + 'neighbourhoods.geojson', encoding='utf-8'))
rows = []
for f in g['features']:
    p = transform(tr, shape(f['geometry']))
    m = ~geometry_mask([mapping(p)], A.shape, T, all_touched=False)
    if not np.isfinite(A[m]).any():
        m = ~geometry_mask([mapping(p)], A.shape, T, all_touched=True)
    rows.append((f['properties']['name'], round(float(np.nanmean(A[m])), 1), int(np.isfinite(A[m]).sum())))
with open(D + 'raw/layers/imperviousness.csv', 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh); w.writerow(['name', 'value']); w.writerows([r[:2] for r in rows])
json.dump(dict(id='imperviousness', name='Τσιμέντο και άσφαλτος (στεγανοποίηση)', unit='% επιφάνειας', kind='rec',
               source='Copernicus Land Monitoring Service (EEA), HRL Imperviousness Density 2018, ανάλυση 10 m, '
                      'ελεύθερη και ανοιχτή χρήση με αναφορά (πολιτική δεδομένων Copernicus)',
               note='Στοιχεία του 2018· δεν δείχνουν αλλαγές μετά από τότε.',
               worse='high'), open(D + 'raw/layers/imperviousness.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
v = [r[1] for r in rows]
print(len(rows), 'min', min(v), 'max', max(v), 'min pixels', min(r[2] for r in rows))
