import json,csv,re,math,sys
sys.path.insert(0,'/tmp/athens_prep')
O='.'
src=open('/tmp/athens_prep/build.py').read()
# reuse geometry helpers
ns={'re':re,'math':math}; exec(src[src.index('# ---------- WKT'):src.index('# ---------- reproject')],ns)
g=json.load(open(O+'neighbourhoods.geojson'))
F=g['features']; print('geojson parses; features =',len(F)); assert len(F)==144
BB=(37.94,38.03,23.68,23.79); bad=0; badbb=0
for f in F:
    ge=f['geometry']; polys=[ge['coordinates']] if ge['type']=='Polygon' else ge['coordinates']
    for rings in polys:
        for r in rings:
            ok,why=ns['ring_valid']([tuple(p) for p in r])
            if not ok: bad+=1; print('INVALID',f['properties']['name'],why)
            if not all(BB[2]<=x<=BB[3] and BB[0]<=y<=BB[1] for x,y in r): badbb+=1; print('OUTSIDE BBOX',f['properties']['name'],min(p[0] for p in r),max(p[0] for p in r),min(p[1] for p in r),max(p[1] for p in r))
print('invalid rings:',bad,'| rings outside Athens bbox:',badbb)
rep=json.load(open('/tmp/athens_prep/build_report.json'))['layers']
cols={'schools':'n_schools','playgrounds':'n_playgrounds','nurseries':'n_nurseries','friendship':'n_friendship_clubs','clinics':'n_clinics','pocket':'n_pocket_parks'}
for k,c in cols.items():
    s=sum(f['properties'][c] for f in F); r=rep[k]
    print(f"{k}: sum of neighbourhood counts={s}, layer points inside polygons={r['inside_polygons']}, total points={r['points']}, outside={r['outside']}, in>1 polygon={r['in_multiple']}, match={s==r['inside_polygons']}")
    assert s==r['inside_polygons']
chk={65:41.22,151:31.86,55:33.04}
rows={int(r['station_id']):r for r in csv.DictReader(open(O+'stations.csv'))}
for sid,exp in chk.items():
    v=float(rows[sid]['heat_daily_max']); print(f'station {sid} heat_daily_max={v} expected~{exp} diff={abs(v-exp):.3f} ok={abs(v-exp)<=0.05}')
for fn in ['neighbourhoods.csv','stations.csv']:
    t=open(O+fn,encoding='utf8').read(); bad=re.findall(r'(?i)(?<![A-Za-z0-9_])(nan|none|null|inf)(?![A-Za-z0-9_])',t)
    n=len(list(csv.DictReader(open(O+fn,encoding='utf8')))); print(fn,'rows',n,'NaN/None/null/inf strings:',len(bad))
ex=rows[7]; print('station 7 heat_included=',ex['heat_included'],ex['heat_flag'])
print('has_sensor true/false:',sum(f['properties']['has_sensor'] for f in F),sum(not f['properties']['has_sensor'] for f in F))
print('no-sensor features with non-null metrics:',sum(1 for f in F if not f['properties']['has_sensor'] and any(f['properties'][k] is not None for k in ['heat_mean','pm2_5','pm10','no2','o3'])))
