"""Search Earth Search STAC for Athens Sentinel-2 L2A summer scenes, pick <=6/yr spread over season."""
import requests, json, sys, datetime as dt
API="https://earth-search.aws.element84.com/v1/search"
BBOX=[23.68,37.94,23.80,38.04]
out=[]
log=[]
for year in range(2017,2027):
    items=[];tok=None
    body={"collections":["sentinel-2-l2a"],"bbox":BBOX,"datetime":f"{year}-06-01T00:00:00Z/{year}-08-31T23:59:59Z","query":{"eo:cloud_cover":{"lt":10}},"limit":100}
    r=requests.post(API,json=body,timeout=60)
    log.append((year,r.status_code))
    if r.status_code!=200: print(year,r.status_code,r.text[:200]); continue
    feats=r.json()["features"]
    # keep scenes covering whole bbox: prefer tile 34SGH
    for f in feats:
        p=f["properties"]
        items.append(f)
    print(year,len(items),sorted(set(f["properties"].get("grid:code") or f["properties"].get("s2:mgrs_tile") for f in items)))
    out+=items
json.dump(out,open("/tmp/athens_ndvi/items.json","w"))
print(log)
