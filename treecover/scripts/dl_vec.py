import requests, json
B='https://image.discomap.eea.europa.eu/arcgis/rest/services/'
def pull(path,out):
    q=dict(where='1=1',geometry='23.68,37.94,23.79,38.04',geometryType='esriGeometryEnvelope',inSR=4326,spatialRel='esriSpatialRelIntersects')
    ids=requests.get(B+path+'/query',params=dict(q,returnIdsOnly='true',f='json'),timeout=120).json()['objectIds']
    print(path,'ids',len(ids),flush=True)
    feats=[]
    for i in range(0,len(ids),200):
        chunk=ids[i:i+200]
        for attempt in range(4):
            r=requests.post(B+path+'/query',data=dict(objectIds=','.join(map(str,chunk)),outFields='*',outSR=4326,f='geojson'),timeout=180)
            if r.status_code==200 and 'features' in r.json(): break
            print('retry',i,r.status_code,flush=True)
        feats+=r.json()['features']
    json.dump({'type':'FeatureCollection','features':feats},open(out,'w'))
    print('saved',out,len(feats))
import sys
for a in sys.argv[1:]:
    p,o=a.split('=');pull(p,o)
