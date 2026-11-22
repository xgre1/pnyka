import urllib.request,urllib.parse,json
B='https://opendata.cityofathens.gr/api/3/action/'
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-team':'dataprep/1.0'}),timeout=60))
seen={}
for q in ['gis-athens','name:gis-athens*']:
    for start in range(0,400,100):
        try: r=get(B+'package_search?rows=100&start=%d&q=%s'%(start,urllib.parse.quote(q)))
        except Exception as e: print(q,e); break
        for p in r['result']['results']: seen[p['name']]=p
        if not r['result']['results']: break
print(len(seen))
for n,p in sorted(seen.items()):
    print(n,'|',p['title'],'|',p.get('license_id'),'|',[(x['format'],x['id'][:6]) for x in p['resources']])
json.dump(seen,open('pkgs.json','w'))
