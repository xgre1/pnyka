import json,math,re,os,csv,datetime,urllib.request
import pandas as pd, numpy as np
D='/tmp/athens_env/data/'; O='.'; P='/tmp/athens_prep/'
nb=pd.read_csv(D+'nb.csv'); reg=pd.read_csv(D+'reg.csv'); md=pd.read_csv(D+'md.csv')
heat=pd.read_pickle(P+'heat_all.pkl'); air=pd.read_pickle(P+'air_all.pkl')
# ---------- WKT
def parse_wkt(w):
    w=w.strip(); typ=w.split('(')[0].strip().upper()
    nums=lambda s:[tuple(map(float,c.split()[:2])) for c in s.split(',')]
    if typ=='POLYGON':
        rings=re.findall(r'\(([^()]+)\)',w); return [[nums(r) for r in rings]]
    if typ=='MULTIPOLYGON':
        polys=[]; 
        for pm in re.findall(r'\(\(.*?\)\)(?=\s*,\s*\(\(|\s*\)$)',w,re.S):
            polys.append([nums(r) for r in re.findall(r'\(([^()]+)\)',pm)])
        return polys
    raise ValueError(typ)
def ring_area(r): 
    return sum(r[i][0]*r[i+1][1]-r[i+1][0]*r[i][1] for i in range(len(r)-1))/2
def pip_ring(x,y,r):
    c=False
    for i in range(len(r)-1):
        x1,y1=r[i];x2,y2=r[i+1]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c
def in_poly(x,y,polys):
    for rings in polys:
        if pip_ring(x,y,rings[0]) and not any(pip_ring(x,y,h) for h in rings[1:]): return True
    return False
def seg_x(a,b,c,d):
    def o(p,q,r): return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    return o(a,b,c)*o(a,b,d)<0 and o(c,d,a)*o(c,d,b)<0
def ring_valid(r):
    if len(r)<4 or r[0]!=r[-1]: return False,'not closed/too short'
    n=len(r)-1
    for i in range(n):
        for j in range(i+2,n):
            if i==0 and j==n-1: continue
            if seg_x(r[i],r[i+1],r[j],r[j+1]): return False,'self-intersection'
    if abs(ring_area(r))==0: return False,'zero area'
    return True,''
def area_km2(polys):
    tot=0
    for rings in polys:
        lat0=math.radians(sum(p[1] for p in rings[0])/len(rings[0]))
        f=lambda r:[(6371.0088*math.cos(lat0)*math.radians(x),6371.0088*math.radians(y)) for x,y in r]
        a=abs(ring_area(f(rings[0])))-sum(abs(ring_area(f(h))) for h in rings[1:]); tot+=a
    return tot
# ---------- reproject EPSG:2100 -> WGS84
def egsa_to_wgs(E,N):
    a=6378137.0; f=1/298.257222101; e2=f*(2-f); k0=0.9996; lam0=math.radians(24); x=E-500000; M=N/k0
    mu=M/(a*(1-e2/4-3*e2**2/64-5*e2**3/256)); e1=(1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
    phi1=mu+(3*e1/2-27*e1**3/32)*math.sin(2*mu)+(21*e1**2/16-55*e1**4/32)*math.sin(4*mu)+(151*e1**3/96)*math.sin(6*mu)+(1097*e1**4/512)*math.sin(8*mu)
    ep2=e2/(1-e2); C1=ep2*math.cos(phi1)**2; T1=math.tan(phi1)**2; N1=a/math.sqrt(1-e2*math.sin(phi1)**2); R1=a*(1-e2)/(1-e2*math.sin(phi1)**2)**1.5; Dd=x/(N1*k0)
    phi=phi1-(N1*math.tan(phi1)/R1)*(Dd**2/2-(5+3*T1+10*C1-4*C1**2-9*ep2)*Dd**4/24+(61+90*T1+298*C1+45*T1**2-252*ep2-3*C1**2)*Dd**6/720)
    lam=lam0+(Dd-(1+2*T1+C1)*Dd**3/6+(5-2*C1+28*T1-3*C1**2+8*ep2+24*T1**2)*Dd**5/120)/math.cos(phi1)
    h=0; Nn=a/math.sqrt(1-e2*math.sin(phi)**2)
    X=Nn*math.cos(phi)*math.cos(lam)+(-199.87); Y=Nn*math.cos(phi)*math.sin(lam)+74.79; Z=Nn*(1-e2)*math.sin(phi)+246.62
    f2=1/298.257223563; e2b=f2*(2-f2); p=math.hypot(X,Y); lon=math.atan2(Y,X); lat=math.atan2(Z,p*(1-e2b))
    for _ in range(10):
        Nn=a/math.sqrt(1-e2b*math.sin(lat)**2); lat=math.atan2(Z+e2b*Nn*math.sin(lat),p)
    return math.degrees(lon),math.degrees(lat)
# ---------- neighbourhoods
polys={}; 
for _,r in nb.iterrows(): polys[int(r.neighbourhood_id)]=parse_wkt(r.polygon_geo)
area={k:area_km2(v) for k,v in polys.items()}
# ---------- layers
meta=json.load(open(P+'layers_meta.json'))
LK={'schools':'n_schools','playgrounds':'n_playgrounds','nurseries':'n_nurseries','friendship':'n_friendship_clubs','clinics':'n_clinics','pocket':'n_pocket_parks'}
counts={c:{k:None for k in polys} for c in LK.values()}; lay_report={}
BB=(37.94,38.03,23.68,23.79)
order=sorted(polys,key=lambda k:area[k])  # smallest first
for key,col in LK.items():
    m=meta[key]
    # licence from dataset page
    try:
        h=urllib.request.urlopen(urllib.request.Request('https://opendata.cityofathens.gr/dataset/'+m['slug'],headers={'User-team':'dataprep/1.0'}),timeout=60).read().decode('utf8','ignore')
        m['licence_uri']=sorted(set(re.findall(r'authority/licence/(CC_BY[_0-9]*)',h)))
    except Exception as e: m['licence_uri']='error %s'%e
    if m.get('http_status')!=200: lay_report[key]=dict(status='FAILED',error=m.get('error')); continue
    try:
        g=json.load(open(P+'layers/%s.geojson'%key)); crs=g['crs']['properties']['name']
        pts=[]
        for ft in g['features']:
            geom=ft['geometry']
            cs=[geom['coordinates']] if geom['type']=='Point' else geom['coordinates']
            for c in cs: pts.append(c[:2])
        feats=len(g['features'])
        if '2100' in crs: pts=[egsa_to_wgs(*c) for c in pts]
        elif not ('4326' in crs or 'CRS84' in crs): raise ValueError('unknown crs '+crs)
    except Exception as e:
        lay_report[key]=dict(status='FAILED',error='parse: %s'%e); continue
    inbb=sum(BB[2]<=x<=BB[3] and BB[0]<=y<=BB[1] for x,y in pts)
    cnt={k:0 for k in polys}; inside=0; multi=0
    for x,y in pts:
        hit=[k for k in order if in_poly(x,y,polys[k])]
        if hit: cnt[hit[0]]+=1; inside+=1; multi+=len(hit)>1
    counts[col]=cnt
    lay_report[key]=dict(status='OK',features=feats,points=len(pts),crs=crs,reprojected=('2100' in crs),in_bbox=inbb,inside_polygons=inside,outside=len(pts)-inside,in_multiple=multi,sum_counts=sum(cnt.values()))
    m['dl_time']=m['dl_time']
# ---------- stations
_d=pd.read_csv(D+'all.csv',usecols=['station_id','station_name','neighbourhood_name','municipal_district_id']).drop_duplicates('station_id')
_d=_d.merge(reg[['station_id','station_address']],on='station_id',how='left').rename(columns={'station_address':'station_address'})
n2id=dict(zip(nb.name,nb.neighbourhood_id)); assert _d.neighbourhood_name.isin(n2id).all()
_d['neighbourhood_id']=_d.neighbourhood_name.map(n2id)
st=_d[['station_id','station_name','station_address','neighbourhood_id','municipal_district_id','neighbourhood_name']].set_index('station_id')
st=st.join(heat[['heat_mean','heat_daily_max','heat_night','hours_above_35','hours_above_38','valid_days','summer_temp_hours']]).join(air)
st['valid_days']=st.valid_days.fillna(0).astype(int)
st['heat_included']=(st.valid_days>=46)&(st.index!=7)
st['heat_flag']=''
st.loc[st.valid_days<46,'heat_flag']='fewer_than_46_valid_days'
st.loc[st.summer_temp_hours.isna(),'heat_flag']='no_summer_temperature_data'
st.loc[7,'heat_flag']='excluded_stuck_sensor'
for c in ['heat_mean','heat_daily_max','heat_night','hours_above_35','hours_above_38']: st.loc[~st.heat_included,c+'_used']=np.nan; st.loc[st.heat_included,c+'_used']=st.loc[st.heat_included,c]
for c in ['pm2_5','pm10','no2','o3']:
    st[c+'_used']=st[c].where(st[c+'_n']>=3000)
st['air_included']=st[['pm2_5_used','pm10_used','no2_used','o3_used']].notna().any(axis=1)
st['pm_spiky']=st.pm_spiky.where(st.pm2_5_n>=3000)
print('stations',len(st),'with data',st.valid_days.notna().sum(),'heat_included',st.heat_included.sum(),'air_included',st.air_included.sum(),'spiky',st.pm_spiky.sum())
# ---------- neighbourhood aggregates
rows=[]
for _,r in nb.iterrows():
    k=int(r.neighbourhood_id); s=st[(st.neighbourhood_id==k)&(st.index.isin(heat.index)|st.index.isin(air.index))]
    d={'neighbourhood_id':k,'name':r['name'],'friendly_name':r.friendly_name,'municipal_district_id':int(r.municipal_district_id),'has_sensor':len(s)>0,'n_stations':len(s),
       'station_names':' | '.join(s.station_name) if len(s) else None,
       'n_stations_heat':int(s.heat_included.sum()),'n_stations_air':int(s.air_included.sum())}
    for c,nm in [('heat_mean','heat_mean'),('heat_daily_max','heat_daily_max'),('heat_night','heat_night'),('hours_above_35','hours_above_35'),('hours_above_38','hours_above_38'),('pm2_5','pm2_5'),('pm10','pm10'),('no2','no2'),('o3','o3')]:
        src=s[c+'_used'] if c+'_used' in s else None
        v=src.dropna().mean() if src is not None and src.notna().any() else None
        d[nm]=None if v is None or pd.isna(v) else round(float(v),3 if c.startswith('heat') else (1 if c.startswith('hours') else 2))
    d['pm_spiky']=bool(s.pm_spiky.fillna(False).astype(bool).any()) if d['n_stations_air'] else None
    for col in LK.values(): d[col]=None if counts[col] is None or counts[col][k] is None else counts[col][k]
    d['area_km2']=round(area[k],4)
    rows.append(d)
N=pd.DataFrame(rows)
N['heat_rank']=N.heat_daily_max.rank(ascending=False,method='min').astype('Int64')
cols=['neighbourhood_id','name','friendly_name','municipal_district_id','has_sensor','n_stations','n_stations_heat','n_stations_air','station_names','heat_mean','heat_daily_max','heat_night','hours_above_35','hours_above_38','pm2_5','pm10','no2','o3','pm_spiky','n_schools','n_playgrounds','n_nurseries','n_friendship_clubs','n_clinics','n_pocket_parks','area_km2','heat_rank']
N=N[cols]
N.to_csv(O+'neighbourhoods.csv',index=False,float_format='%g')
# station csv
sc=st.reset_index()
sc=sc.rename(columns={'station_address':'address','heat_mean':'heat_mean_raw'})
SC=pd.DataFrame({'station_id':sc.station_id,'station_name':sc.station_name,'address':sc.address,'neighbourhood_id':sc.neighbourhood_id,'neighbourhood_name':sc.neighbourhood_name,'municipal_district_id':sc.municipal_district_id,
 'heat_mean':sc.heat_mean_raw.round(3),'heat_daily_max':sc.heat_daily_max.round(3),'heat_night':sc.heat_night.round(3),'hours_above_35':sc.hours_above_35,'hours_above_38':sc.hours_above_38,'valid_days':sc.valid_days,'summer_temp_hours':sc.summer_temp_hours,'heat_included':sc.heat_included,'heat_flag':sc.heat_flag,
 'pm2_5':sc.pm2_5.round(2),'pm10':sc.pm10.round(2),'no2':sc.no2.round(2),'o3':sc.o3.round(2),'pm2_5_valid_hours':sc.pm2_5_n,'pm10_valid_hours':sc.pm10_n,'no2_valid_hours':sc.no2_n,'o3_valid_hours':sc.o3_n,
 'pm2_5_raw_mean':sc.pm2_5_raw.round(2),'pm2_5_dropped_hours':sc.pm2_5_dropped,'pm10_dropped_hours':sc.pm10_dropped,'no2_dropped_hours':sc.no2_dropped,'o3_dropped_hours':sc.o3_dropped,'pm_spiky':sc.pm_spiky,'air_included':sc.air_included})
# air values below 3000h are blanked
for c in ['pm2_5','pm10','no2','o3']: SC.loc[SC[c+'_valid_hours']<3000,c]=np.nan
# station values of excluded heat: keep descriptive values but heat_included flags it
SC.to_csv(O+'stations.csv',index=False,float_format='%g')
# geojson
feats=[]
for d in N.to_dict('records'):
    k=d['neighbourhood_id']; pr={}
    for kk,v in d.items():
        if v is pd.NA or (isinstance(v,float) and math.isnan(v)): v=None
        elif isinstance(v,(np.integer,)): v=int(v)
        elif isinstance(v,(np.floating,)): v=float(v)
        elif isinstance(v,(np.bool_,)): v=bool(v)
        pr[kk]=v
    pl=polys[k]
    geom={'type':'Polygon','coordinates':[[list(p) for p in ring] for ring in pl[0]]} if len(pl)==1 else {'type':'MultiPolygon','coordinates':[[[list(p) for p in ring] for ring in poly] for poly in pl]}
    feats.append({'type':'Feature','properties':pr,'geometry':geom})
json.dump({'type':'FeatureCollection','name':'neighbourhoods','features':feats},open(O+'neighbourhoods.geojson','w'),ensure_ascii=False)
json.dump({'layers':lay_report,'meta':meta},open(P+'build_report.json','w'),ensure_ascii=False,indent=1,default=str)
print(json.dumps(lay_report,indent=0,ensure_ascii=False))
print(N.has_sensor.sum(),(~N.has_sensor).sum(),N.heat_daily_max.notna().sum(),N.pm2_5.notna().sum())
print({m:meta[m].get('licence_uri') for m in meta})
