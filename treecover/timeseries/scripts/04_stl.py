"""STL 2012 vs 2018 per-neighbourhood tree cover from EEA ArcGIS MapServers (no login)."""
import requests, json, numpy as np, pandas as pd, shapely.wkt as wkt
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree
from pyproj import Transformer
OUT="."
B="https://image.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas"
SRC={2012:f"{B}/STL/MapServer/0/query",2018:f"{B}/UA_StreetTreeLayer_2018/MapServer/0/query"}
env="23.66,37.92,23.82,38.06"
nb=pd.read_csv("/tmp/athens_env/data/nb.csv")
tr=Transformer.from_crs(4326,32634,always_xy=True).transform
polys=[transform(tr,wkt.loads(w)) for w in nb.polygon_geo]
res={}
for y,u in SRC.items():
    feats=[];off=0;log=[]
    while True:
        for attempt in range(4):
          r=requests.get(u,params=dict(f="geojson",where="1=1",geometry=env,geometryType="esriGeometryEnvelope",inSR=4326,spatialRel="esriSpatialRelIntersects",outFields="*",outSR=4326,resultOffset=off,resultRecordCount=500,returnGeometry="true"),timeout=180)
          if r.status_code==200 and r.text.startswith("{"): break
          print(y,"retry",r.status_code,r.text[:150])
        log.append(r.status_code);j=r.json()
        if "error" in j: print(y,"ERR",j["error"]);break
        f=j.get("features",[]);feats+=f;off+=len(f)
        if not f or not j.get("exceededTransferLimit"):break
    print(y,"HTTP",set(log),"features",len(feats),"props sample",feats[0]["properties"] if feats else None)
    geoms=[transform(tr,shape(x["geometry"])) for x in feats if x["geometry"]]
    geoms=[g.buffer(0) for g in geoms]
    U=unary_union(geoms);res[y]=U
    print(y,"STL area in AOI km2",round(U.intersection(unary_union(polys)).area/1e6,3))
rows=[]
for n,p in zip(nb.name,polys):
    r=dict(neighbourhood=n,area_km2=p.area/1e6)
    for y,U in res.items(): r[f"stl{y}_pct"]=100*U.intersection(p).area/p.area
    rows.append(r)
d=pd.DataFrame(rows);d["delta_pp_2012_2018"]=d.stl2018_pct-d.stl2012_pct
tot=unary_union(polys)
print("municipal STL pct:",{y:round(100*U.intersection(tot).area/tot.area,2) for y,U in res.items()})
from scipy import stats
t=pd.read_csv(".").set_index("neighbourhood")
print("check vs existing ua_stl2018_pct: spearman",stats.spearmanr(d.stl2018_pct,t.ua_stl2018_pct.reindex(d.neighbourhood)).correlation,"max abs diff",(d.stl2018_pct.values-t.ua_stl2018_pct.reindex(d.neighbourhood).values).__abs__().max())
print("spearman 2012 vs 2018",stats.spearmanr(d.stl2012_pct,d.stl2018_pct).correlation)
print(d.delta_pp_2012_2018.describe().round(2))
d.to_csv(f"{OUT}/stl_2012_2018_by_neighbourhood.csv",index=False,float_format="%.3f")
pd.set_option("display.width",200)
print(d.sort_values("delta_pp_2012_2018").head(6).round(2).to_string());print(d.sort_values("delta_pp_2012_2018").tail(6).round(2).to_string())
