import json,urllib.request,datetime,re
p=json.load(open('pkgs.json'))
keys={'schools':'3bbfb15','playgrounds':'894dd9f','nurseries':'62bd77f','friendship':'b1f3060','clinics':'9f6d7fe','pocket':'d87bc47'}
meta={}
for k,pre in keys.items():
    n=[n for n in p if n[11:18]==pre][0]
    # package_show for license
    try:
        ps=json.load(urllib.request.urlopen(urllib.request.Request('https://opendata.cityofathens.gr/api/3/action/package_show?id='+n,headers={'User-team':'dataprep/1.0'}),timeout=60))['result']
    except Exception as e: ps=p[n]
    r=[r for r in ps['resources'] if r['format']=='GeoJSON'][0]
    m={'slug':n,'title':ps['title'],'resource_url':r['url'],'resource_id':r['id'],'resource_last_modified':r.get('last_modified'),'package_modified':ps['metadata_modified'],'license_id':ps.get('license_id'),'license_title':ps.get('license_title'),'notes_license_hits':re.findall(r'.{60}CC.BY.{40}',(ps.get('notes') or ''),re.S)[:2],'extras':ps.get('extras'),'dl_time':datetime.datetime.utcnow().isoformat()+'Z'}
    try:
        resp=urllib.request.urlopen(urllib.request.Request(r['url'],headers={'User-team':'dataprep/1.0'}),timeout=180)
        m['http_status']=resp.status; b=resp.read(); open('layers/%s.geojson'%k,'wb').write(b); m['bytes']=len(b)
    except Exception as e:
        m['http_status']=getattr(e,'code',None); m['error']=str(e)
    meta[k]=m; print(k,m['http_status'],m.get('bytes'),m.get('error'),ps.get('license_id'),m['notes_license_hits'])
json.dump(meta,open('layers_meta.json','w'),ensure_ascii=False,indent=1)
