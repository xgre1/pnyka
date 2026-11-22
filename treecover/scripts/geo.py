import pandas as pd, shapely.wkt as w
from shapely.ops import transform
from pyproj import Transformer
nb=pd.read_csv('/tmp/athens_env/data/nb.csv')
nb['geom']=nb.polygon_geo.apply(w.loads)
t=Transformer.from_crs(4326,3035,always_xy=True).transform
nb['g3035']=nb.geom.apply(lambda g:transform(t,g))
