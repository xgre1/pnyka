import sys,json; sys.path.insert(0,'.')
import common
from common import *
dd=json.load(open('/tmp/athens_treecover/dl/cityg_dendra.json'))['features']
from shapely.geometry import MultiPoint
hull=transform(T_4326_3857,MultiPoint([tuple(f['geometry']['coordinates']) for f in dd]).convex_hull)
out={}
with rasterio.open(CHM) as s:
  for sg in (0,0.5,1.0,2.0):
    for w in (3,5):
      common.SIGMA=sg;common.LM_WIN=w
      a=common.canopy_pct_and_trees(s,hull)[1]; out[f's{sg}_w{w}']=a
print(out)
