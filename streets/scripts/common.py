import json, numpy as np, pandas as pd, rasterio
import shapely.wkt as wkt
from shapely.ops import transform
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from scipy import ndimage as ndi

CHM = '/tmp/athens_treecover/dl/meta_chm_athens.tif'
NB = '/tmp/athens_env/data/nb.csv'
H_MIN = 3          # canopy height threshold (m)
LM_WIN = 5         # local-max window, pixels (~4.7 m ground, pixel = 1.194 m in EPSG:3857 = 0.94 m on the ground at 38N)
SIGMA = 0.5        # light gaussian smoothing, pixels (sigma=1.0 undercounts ~14x vs the National Garden inventory; see README)
T_4326_2100 = Transformer.from_crs(4326, 2100, always_xy=True).transform
T_2100_3857 = Transformer.from_crs(2100, 3857, always_xy=True).transform
T_4326_3857 = Transformer.from_crs(4326, 3857, always_xy=True).transform

def load_nb():
    nb = pd.read_csv(NB)
    nb['geom'] = nb.polygon_geo.apply(wkt.loads)
    nb['area'] = nb.geom.apply(lambda g: g.area)
    return nb

def canopy_pct_and_trees(src, geom3857, with_trees=True, chm_cache={}):
    """Return (canopy %, n local maxima, n valid pixels) inside geom (EPSG:3857), by pixel centre."""
    minx, miny, maxx, maxy = geom3857.bounds
    pad = 4 * src.res[0]
    win = from_bounds(minx - pad, miny - pad, maxx + pad, maxy + pad, src.transform).round_offsets().round_lengths()
    win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
    a = src.read(1, window=win)
    tr = src.window_transform(win)
    m = ~geometry_mask([geom3857], out_shape=a.shape, transform=tr, all_touched=False)
    n = int(m.sum())
    if n == 0: return np.nan, 0, 0
    pct = 100.0 * float(np.mean(a[m] >= H_MIN))
    trees = 0
    if with_trees:
        trees = int((local_max(a) & m).sum())
    return pct, trees, n

def local_max(a):
    s = ndi.gaussian_filter(a.astype('float32'), SIGMA)
    return (s == ndi.maximum_filter(s, size=LM_WIN)) & (s >= H_MIN)
