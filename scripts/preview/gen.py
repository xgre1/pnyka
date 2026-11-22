import json,csv,sys,math
D='.'
g=json.load(open(D+'neighbourhoods.geojson',encoding='utf-8'))
tc={r['neighbourhood']:r for r in csv.DictReader(open(D+'treecover/treecover_by_neighbourhood.csv',encoding='utf-8-sig'))}
def f(x):
    try:
        v=float(x); return None if math.isnan(v) else v
    except: return None
lons=[];lats=[]
def rings(geom):
    if geom['type']=='Polygon': return geom['coordinates']
    return [r for p in geom['coordinates'] for r in p]
for ft in g['features']:
    for r in rings(ft['geometry']):
        for x,y in r: lons.append(x);lats.append(y)
x0,x1,y0,y1=min(lons),max(lons),min(lats),max(lats)
k=math.cos(math.radians((y0+y1)/2)); W=760; s=W/((x1-x0)*k); H=round((y1-y0)*s)
rows=[]
for ft in g['features']:
    p=ft['properties']; t=tc.get(p['name'],{})
    d=' '.join('M'+' L'.join(f'{(x-x0)*k*s:.1f},{(y1-y)*s:.1f}' for x,y in r)+'Z' for r in rings(ft['geometry']))
    vul=sum(int(p.get(c) or 0) for c in ['n_schools','n_nurseries','n_playgrounds','n_friendship_clubs'])
    rows.append(dict(n=p['name'],d=d,area=f(p.get('area_km2')),tree=f(t.get('ua_stl2018_pct')),tree_wc=f(t.get('wc2021_tree_pct')),
        night=f(p.get('heat_night')),daymax=f(p.get('heat_daily_max')),lst=f(t.get('city_lst_summer_day_2016_2020_c')),
        schools=int(p.get('n_schools') or 0),nurs=int(p.get('n_nurseries') or 0),play=int(p.get('n_playgrounds') or 0),clubs=int(p.get('n_friendship_clubs') or 0),vul=vul,
        sensors=int(p.get('n_stations') or 0),stations=p.get('station_names') or ''))
html=open('/tmp/athens_preview/tpl.html',encoding='utf-8').read().replace('__DATA__',json.dumps(rows,ensure_ascii=False)).replace('__W__',str(W)).replace('__H__',str(H))
open(D+'preview.html','w',encoding='utf-8').write(html)
print('ok',len(rows),W,H,len(html))
