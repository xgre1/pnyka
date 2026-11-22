import sys; sys.path.insert(0,'/tmp/athens_treecover/scripts')
from geo import *
import numpy as np, json, rasterio
from rasterio.features import geometry_mask
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree
D='/tmp/athens_treecover/dl/'
res=pd.DataFrame({'neighbourhood':nb.name})
res['area_km2']=(nb.g3035.apply(lambda g:g.area)/1e6).round(5).values
def raster_stats(path,geoms,fn):
    out=[]
    with rasterio.open(path) as r:
        a=r.read(1)
        for g in geoms:
            m=~geometry_mask([g],out_shape=a.shape,transform=r.transform,all_touched=False)
            out.append(fn(a[m]) if m.sum() else np.nan)
        # pixel-centre rule: tiny polygons may have 0 pixels
    return out
n=lambda a:len(a)
# WorldCover (EPSG:4326 grid)
for y in (2020,2021):
    res[f'wc{y}_tree_pct']=np.array(raster_stats(D+f'wc{y}_athens.tif',nb.geom,lambda a:100*np.mean(a==10)))
# Copernicus rasters (3035)
res['tcd2018_mean_pct']=raster_stats(D+'tcd2018.tif',nb.g3035,lambda a:np.mean(np.where(a<=100,a,np.nan)))
res['tcd2018_ge10_pct']=raster_stats(D+'tcd2018.tif',nb.g3035,lambda a:100*np.mean(a>=10))
res['tcd2018_gt0_pct']=raster_stats(D+'tcd2018.tif',nb.g3035,lambda a:100*np.mean((a>0)&(a<=100)))
res['clcplus2021_tree_pct']=raster_stats(D+'clcplus2021.tif',nb.g3035,lambda a:100*np.mean(np.isin(a,[2,3,4])))
res['hrl_forest2018_pct']=raster_stats(D+'forest2018.tif',nb.g3035,lambda a:100*np.mean(np.isin(a,[1,2])))
res['hrl_wvl2021_woody_pct']=raster_stats(D+'wvl2021.tif',nb.g3035,lambda a:100*np.mean(a==1))
res['hrl_swf2021_pct']=raster_stats(D+'swf2021.tif',nb.g3035,lambda a:100*np.mean(a==1))
# Meta CHM (3857)
t=Transformer.from_crs(4326,3857,always_xy=True).transform
g3857=nb.geom.apply(lambda g:transform(t,g))
res['metachm_ge3m_pct']=raster_stats(D+'meta_chm_athens.tif',g3857,lambda a:100*np.mean((a>=3)&(a<=100)))
res['metachm_ge5m_pct']=raster_stats(D+'meta_chm_athens.tif',g3857,lambda a:100*np.mean((a>=5)&(a<=100)))
res['metachm_mean_height_m']=raster_stats(D+'meta_chm_athens.tif',g3857,lambda a:np.mean(np.where(a<=100,a,0)))
# vector shares
tf=Transformer.from_crs(4326,3035,always_xy=True).transform
def load(fn,filt=None):
    d=json.load(open(D+fn));out=[]
    for f in d['features']:
        if filt and not filt(f['properties']):continue
        g=shape(f['geometry'])
        if not g.is_valid:g=g.buffer(0)
        out.append((transform(tf,g),f['properties']))
    return out
def share(feats,label):
    tree=STRtree([g for g,_ in feats]);vals=[]
    for g in nb.g3035:
        idx=tree.query(g)
        u=unary_union([feats[i][0] for i in idx]).intersection(g) if len(idx) else None
        vals.append(100*u.area/g.area if u is not None else 0.0)
    res[label]=vals
stl=load('stl2018.geojson')
share(stl,'ua_stl2018_pct')
ua=load('ua2012.geojson')
for code,lab in [(['14100'],'ua2012_green_urban_pct'),(['14200'],'ua2012_sports_leisure_pct'),(['31000'],'ua2012_forest_pct')]:
    share([x for x in ua if x[1]['code_2012'] in code],lab)
res['ua2012_green_total_pct']=res.ua2012_green_urban_pct+res.ua2012_forest_pct+res.get('ua2012_herb_pct',0)
share([x for x in ua if x[1]['code_2012'] in ('32000',)],'ua2012_herbaceous_pct')
res['ua2012_green_total_pct']=res.ua2012_green_urban_pct+res.ua2012_forest_pct+res.ua2012_herbaceous_pct
# City layers
def cl(t,filt=None):
    d=json.load(open(D+f'cityg_{t}.json'));out=[]
    for f in d['features']:
        if filt and not filt(f['properties']):continue
        out.append((shape(f['geometry']),f['properties']))
    return out
tr=cl('dendra')
cnt=np.zeros(len(nb),int);cnt_ex=np.zeros(len(nb),int)
for p,pr in tr:
    for i,g in enumerate(nb.geom):
        if g.contains(p):
            cnt[i]+=1;cnt_ex[i]+=pr['Condition']=='Existing';break
res['city_national_garden_trees_all']=cnt;res['city_national_garden_trees_existing']=cnt_ex
pp=cl('PocketParks2');c=np.zeros(len(nb),int)
for p,_ in pp:
    for i,g in enumerate(nb.geom):
        if g.contains(p):c[i]+=1;break
res['city_pocket_parks_count']=c
zs=('ΑΣΤΙΚΟ ΠΡΑΣΙΝΟ - ΕΛΕΥΘΕΡΟΙ ΧΩΡΟΙ','ΚΟΙΝΟΧΡΗΣΤΟ ΠΡΑΣΙΝΟ','ΠΡΑΣΙΑ')
z=[(transform(tf,g.buffer(0)),p) for g,p in cl('xriseis',lambda p:p['xriseis'] in zs)]
share(z,'city_zoned_green_pct')
# LST
lst=[(transform(tf,g.buffer(0)),p) for g,p in cl('angLST_Athens_UrbanAtlas')]
tree=STRtree([g for g,_ in lst]);v=[]
for g in nb.g3035:
    s=w=0
    for i in tree.query(g):
        a=lst[i][0].intersection(g).area
        if a>0 and lst[i][1]['avgLST'] is not None: s+=a*lst[i][1]['avgLST'];w+=a
    v.append(s/w if w>0 else np.nan)
res['city_lst_summer_day_c']=v
res.to_pickle('/tmp/athens_treecover/res.pkl')
res.to_csv('/tmp/athens_treecover/res_raw.csv',index=False)
print(res.describe().T[['count','mean','min','max']].round(2))
