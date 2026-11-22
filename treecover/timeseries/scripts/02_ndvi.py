"""Read bbox windows of B04/B08/SCL from Earth Search COGs, season-median NDVI per year, zonal stats per neighbourhood.
Reflectance = DN*scale+offset taken from STAC raster:bands per asset (handles baseline>=04.00 offset)."""
import json, os, numpy as np, pandas as pd, rasterio, shapely.wkt as wkt
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from pyproj import Transformer
from shapely.ops import transform as stransform, unary_union
from concurrent.futures import ThreadPoolExecutor
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",AWS_NO_SIGN_REQUEST="YES",GDAL_HTTP_MAX_RETRY="4",GDAL_HTTP_RETRY_DELAY="2")
OUT="."
nb=pd.read_csv("/tmp/athens_env/data/nb.csv")
tr=Transformer.from_crs(4326,32634,always_xy=True)
polys=[stransform(tr.transform,wkt.loads(w)) for w in nb.polygon_geo]
minx,miny,maxx,maxy=unary_union(polys).bounds
minx=np.floor(minx/10)*10-100;miny=np.floor(miny/10)*10-100;maxx=np.ceil(maxx/10)*10+100;maxy=np.ceil(maxy/10)*10+100
W=int((maxx-minx)/10);H=int((maxy-miny)/10);T=from_origin(minx,maxy,10,10)
print("grid",W,H)
items=[f for f in json.load(open("/tmp/athens_ndvi/items.json")) if f["properties"]["grid:code"]=="MGRS-34SGH"]
bydate={}
for f in items:
    d=f["properties"]["datetime"][:10]
    if d not in bydate or f["properties"]["s2:processing_baseline"]>bydate[d]["properties"]["s2:processing_baseline"]: bydate[d]=f
def pick(year,n=8):
    ds=sorted(d for d in bydate if d[:4]==str(year))
    if len(ds)<=n: return ds
    idx=np.unique(np.round(np.linspace(0,len(ds)-1,n)).astype(int)); return [ds[i] for i in idx]
def read(href,band,shape=None,resamp=Resampling.nearest):
    with rasterio.open(href) as ds:
        win=from_bounds(minx,miny,maxx,maxy,ds.transform)
        win=win.round_offsets().round_lengths()
        return ds.read(1,window=win,out_shape=(H,W),resampling=resamp,boundless=False)
BAD={0,1,3,6,7,8,9,10,11}
def scene(f):
    a=f["assets"];rb=lambda k:(a[k]["raster:bands"][0]["scale"],a[k]["raster:bands"][0]["offset"])
    r=read(a["red"]["href"],"red");n=read(a["nir"]["href"],"nir");s=read(a["scl"]["href"],"scl")
    sr,ro=rb("red");sn,no=rb("nir")
    R=np.clip(r*sr+ro,0,None);N=np.clip(n*sn+no,0,None)   # negative surface reflectance (noise after offset) clipped to 0
    ok=(r>0)&(n>0)&~np.isin(s,list(BAD))&((N+R)>0.02)
    with np.errstate(all="ignore"): nd=np.clip((N-R)/(N+R),-1,1)
    nd=np.where(ok&np.isfinite(nd),nd,np.nan).astype("float32")
    return nd,float(ok.mean()),float(np.nanmedian(nd)),float(np.nanmean(nd>=0.4))
res=[];scenes=[];years={}
for year in range(2017,2027):
    ds=pick(year)
    if not ds: continue
    with ThreadPoolExecutor(4) as ex: outs=list(ex.map(lambda d:scene(bydate[d]),ds))
    keep=[]
    for d,(nd,v,mdn,vg) in zip(ds,outs):
        f=bydate[d];p=f["properties"]
        use=v>=0.6
        scenes.append(dict(year=year,scene_id=f["id"],date=d,cloud_pct=round(p["eo:cloud_cover"],2),baseline=p["s2:processing_baseline"],boa_offset_applied=p.get("earthsearch:boa_offset_applied"),dn_offset_used=f["assets"]["red"]["raster:bands"][0]["offset"],valid_frac_in_aoi=round(v,3),aoi_median_ndvi=round(mdn,3),aoi_share_ndvi_ge04=round(vg,3),used=use))
        if use: keep.append(nd)
        print(year,d,p["s2:processing_baseline"],round(v,2),round(mdn,3),round(vg,3),use,flush=True)
    if not keep: continue
    st=np.stack(keep);cnt=np.sum(np.isfinite(st),0)
    with np.errstate(all="ignore"): med=np.nanmedian(st,0)
    med=np.where(cnt>=2,med,np.nan) if len(keep)>=3 else med
    years[year]=(med,len(keep))
np.savez_compressed("/tmp/athens_ndvi/median_ndvi.npz",**{str(y):m for y,(m,_) in years.items()})
masks=[rasterize([(p,1)],out_shape=(H,W),transform=T,fill=0,all_touched=False).astype(bool) for p in polys]
rows=[]
for y,(m,ns) in years.items():
    for name,mk in zip(nb.name,masks):
        v=m[mk];tot=mk.sum();v=v[np.isfinite(v)]
        rows.append(dict(neighbourhood=name,year=y,n_scenes=ns,n_pixels=int(tot),valid_pixel_frac=round(len(v)/tot,3) if tot else np.nan,
            mean_ndvi=float(v.mean()) if len(v) else np.nan,
            veg_share_pct=100*float((v>=0.4).mean()) if len(v) else np.nan,
            dense_share_pct=100*float((v>=0.6).mean()) if len(v) else np.nan))
pd.DataFrame(rows).to_csv(f"{OUT}/ndvi_by_neighbourhood_year.csv",index=False,float_format="%.4f")
pd.DataFrame(scenes).to_csv(f"{OUT}/scenes_used.csv",index=False)
