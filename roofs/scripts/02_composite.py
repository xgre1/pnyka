"""Step 2. Sentinel-2 L2A summer 2025 (June-August) median composite, tile 34SGH, over the extent of the City solar-map layer.
- STAC search: Earth Search v1, GET only.
- Scenes: tile MGRS-34SGH, eo:cloud_cover < 5, then valid (SCL-clear) share of the AOI >= 0.6 (same rule as treecover/timeseries/scripts/02_ndvi.py).
- Bands B02,B03,B04,B08 (10 m) and B11,B12 (20 m, bilinear-resampled to the 10 m grid). SCL (20 m) nearest.
- Reflectance = DN*scale + offset from STAC raster:bands of each asset (baseline 05.11: scale 1e-4, offset -0.1); clipped at 0.
- SCL mask: classes {0,1,3,6,7,8,9,10,11} invalid (as in the treecover script).
- Output: per-pixel median reflectance with SCL mask (primary) and without SCL mask (check), plus valid-scene count.
Usage: python -I 02_composite.py <repo_root> <work_dir>   (work_dir = scratch folder for the .npz, not the repo)"""
import gzip, json, os, sys, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import numpy as np, rasterio, shapely
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from shapely.geometry import shape
from pyproj import Transformer

os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", AWS_NO_SIGN_REQUEST="YES",
                  GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="2")
D = sys.argv[1].rstrip('/') + '/'
WK = sys.argv[2].rstrip('/') + '/'
os.makedirs(WK, exist_ok=True)
API = "https://earth-search.aws.element84.com/v1/search"
BANDS = ['blue', 'green', 'red', 'nir', 'swir16', 'swir22']  # B02 B03 B04 B08 B11 B12
BAD = [0, 1, 3, 6, 7, 8, 9, 10, 11]
MAXCLOUD = 5

# ---- AOI: solar-map extent in UTM 34N (tile CRS), snapped to the 20 m grid of the tile (origin 699960, 4300020)
sol = json.load(gzip.open(D + 'raw/treecover/dl/cityg_c40solarmap.json.gz', 'rt', encoding='utf8'))['features']
g = np.array([shape(f['geometry']) for f in sol], dtype=object)
lo0, la0, lo1, la1 = shapely.total_bounds(g)
tr = Transformer.from_crs(4326, 32634, always_xy=True)
xs, ys = tr.transform([lo0, lo0, lo1, lo1], [la0, la1, la0, la1])
OX, OY = 699960, 4300020
minx = OX + np.floor((min(xs) - 200 - OX) / 20) * 20; maxx = OX + np.ceil((max(xs) + 200 - OX) / 20) * 20
maxy = OY - np.floor((OY - max(ys) - 200) / 20) * 20; miny = OY - np.ceil((OY - min(ys) + 200) / 20) * 20
W = int((maxx - minx) / 10); H = int((maxy - miny) / 10)
print('grid', W, H, minx, maxy, flush=True)

# ---- STAC search (GET)
q = dict(collections='sentinel-2-l2a', bbox=f'{lo0},{la0},{lo1},{la1}', datetime='2025-06-01T00:00:00Z/2025-08-31T23:59:59Z', limit=100)
url = API + '?' + urllib.parse.urlencode(q)
feats = []
while url:
    js = json.load(urllib.request.urlopen(url, timeout=120))
    feats += js['features']
    url = next((l['href'] for l in js.get('links', []) if l['rel'] == 'next'), None) if js['features'] else None
feats = [f for f in feats if f['properties'].get('grid:code') == 'MGRS-34SGH']
feats = {f['id']: f for f in feats}.values()
cand = sorted([f for f in feats if f['properties']['eo:cloud_cover'] < MAXCLOUD], key=lambda f: f['properties']['datetime'])
print('34SGH scenes', len(feats), 'cloud<5:', len(cand), flush=True)


def read(href, resamp):
    with rasterio.open(href) as ds:
        win = from_bounds(minx, miny, maxx, maxy, ds.transform)
        return ds.read(1, window=win, out_shape=(H, W), resampling=resamp, boundless=False)


def scene(f):
    a = f['assets']
    scl = read(a['scl']['href'], Resampling.nearest)
    out = {}
    for b in BANDS:
        rs = Resampling.nearest if a[b]['raster:bands'][0].get('spatial_resolution', 10) == 10 else Resampling.bilinear
        out[b] = read(a[b]['href'], rs)
    sc = {b: (a[b]['raster:bands'][0]['scale'], a[b]['raster:bands'][0]['offset']) for b in BANDS}
    nodata = np.any([out[b] == 0 for b in BANDS], axis=0)
    ok = ~nodata & ~np.isin(scl, BAD)
    return out, sc, ok, nodata


meta, DN, OK, ND, SC = [], [], [], [], None
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(scene, cand))
for f, (out, sc, ok, nodata) in zip(cand, res):
    p = f['properties']; v = float(ok.mean()); use = v >= 0.6
    meta.append(dict(scene_id=f['id'], date=p['datetime'][:10], cloud_pct=round(p['eo:cloud_cover'], 2), baseline=p['s2:processing_baseline'],
                     boa_offset_applied=p.get('earthsearch:boa_offset_applied'), scale=sc['red'][0], offset=sc['red'][1],
                     valid_frac_in_aoi=round(v, 3), used=use))
    print(meta[-1], flush=True)
    if use:
        assert SC is None or SC == sc, 'scale/offset differ between scenes'
        SC = sc; DN.append(np.stack([out[b] for b in BANDS])); OK.append(ok); ND.append(nodata)
DN = np.stack(DN); OK = np.stack(OK); ND = np.stack(ND)  # (S,6,H,W), (S,H,W)
med_m, med_u = [], []
for i, b in enumerate(BANDS):
    s, o = SC[b]
    R = np.clip(DN[:, i].astype('float32') * s + o, 0, None)
    med_m.append(np.nanmedian(np.where(OK, R, np.nan), 0).astype('float32'))
    med_u.append(np.nanmedian(np.where(ND, np.nan, R), 0).astype('float32'))
cnt = OK.sum(0).astype('int16')
np.savez_compressed(WK + 'composite_2025_summer.npz', masked=np.stack(med_m), unmasked=np.stack(med_u), n_valid=cnt,
                    transform=np.array([10, 0, minx, 0, -10, maxy]), bands=np.array(BANDS))
os.makedirs(D + 'roofs/work', exist_ok=True)
json.dump(meta, open(D + 'roofs/work/scenes_used.json', 'w'), indent=1)
print('scenes used', len(DN), 'pixels with 0 valid scenes:', int((cnt == 0).sum()), 'of', cnt.size)
