# Sources tried (run 2026-11-21, no account / login / payment used anywhere)

Study bbox: lon 23.68-23.80, lat 37.94-38.04 (neighbourhood union bounds 23.685-23.791, 37.949-38.033).

## Worked, no login (and used)

| Source | Endpoint | Res / year | Licence | Notes |
|---|---|---|---|---|
| ESA WorldCover 2021 v200 | https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36E021_Map.tif | 10 m, 2021 | CC BY 4.0 | HTTP 200/206; COG, read the Athens window by HTTP range. Tree = class 10. |
| ESA WorldCover 2020 v100 | https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_N36E021_Map.tif | 10 m, 2020 | CC BY 4.0 | HTTP 200. |
| Copernicus HRL Tree Cover Density 2018 | https://image.discomap.eea.europa.eu/arcgis/rest/services/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer (exportImage, format=tiff, imageSR=3035) | 10 m, 2018, values 0-100 | Copernicus open (free, attribution) | HTTP 200. Real pixel values (verified against /identify). |
| Copernicus HRL Forest Type 2018 | .../GioLandPublic/HRL_ForestType_2018/ImageServer | 10 m, 2018 | same | HTTP 200 |
| Copernicus HRL Woody Vegetation Layer 2021 | .../GioLandPublic/HRL_WoodyVegetationLayer_2021/ImageServer | 5 m, 2021 | same | HTTP 200 (this is the "newer" HRL tree/woody product, 2021) |
| Copernicus HRL Small Woody Features 2021 | .../GioLandPublic/HRL_SmallWoodyFeatures_2021_005m/ImageServer | 5 m, 2021 | same | HTTP 200 |
| Copernicus CLC+ Backbone 2021 | https://image.discomap.eea.europa.eu/arcgis/rest/services/CLC_plus/CLMS_CLCplus_RASTER_2021_010m_eu/ImageServer | 10 m, 2021 | same | HTTP 200. Classes 2,3,4 = trees. |
| Urban Atlas Street Tree Layer 2018 (vector) | https://image.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas/UA_StreetTreeLayer_2018/MapServer/0 (query, objectIds, f=geojson) | polygons, 2018 | Copernicus open | HTTP 200; 1915 polygons in bbox. Only layer 0 (vector) queryable; layer 1 (raster) query returns 400. |
| Urban Atlas land use 2012 (vector) | .../UrbanAtlas/UA_UrbanAtlas_2012/MapServer/2 | polygons, 2012 | Copernicus open | HTTP 200; 15,983 of 15,984 polygons. One huge polygon (OBJECTID 10149039, "Other roads", 133 km2) returns HTTP 405 on download and was skipped; irrelevant for green classes. |
| Meta/WRI High Resolution Canopy Height | https://s3.amazonaws.com/dataforgood-fb-data/forests/v1/alsgedi_global_v6_float/chm/122100203.tif (tile index: .../tiles.geojson) | ~1.19 m (EPSG:3857), imagery ~2018-2020 per docs | CC BY 4.0 per docs | HTTP 200 (301 MB COG, windowed read ~11 MB). Directory listing of chm/ is 403 (expected). |
| City of Athens GeoServer WFS | http://gis.cityofathens.gr/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&outputFormat=application/json&typename=geonode:<layer> | see below | not stated in CKAN metadata (license_title = None) | HTTP 200 for all five layers pulled |
| City of Athens CKAN | https://opendata.cityofathens.gr/api/3/action/package_list, package_show, package_search | n/a | n/a | HTTP 200; 471 datasets, 59 `gis-athens-*`. |

### City of Athens layers (WFS typename, features, content)
- `dendra` ("Δένδρα Εθνικού Κήπου", gis-athens-8303d4c8-...): 6,354 points, fields fid, gid, Point_Numb, Parcel_ID, Position_X/Y (projected), Condition (Existing 4,622 / New 1,722 / Cut 10), desc (Latin + Greek species, 106 distinct), family. All inside the National Garden (lon 23.7347-23.7403, lat 37.9714-37.9758). Single park, not city-wide. Survey date not stated (CKAN metadata_modified 2026-05-28). Formats: WMS, WFS, GeoJSON, GML, CSV, XLS, ZIP.
- `PocketParks2` ("Πάρκα Τσέπης", gis-athens-d87bc472-...): 10 points; fields fid, gid, descr, parko_id, streetname. Only names/locations, no area.
- `angLST_Athens_UrbanAtlas` ("Athens Temperature Atlas 2016-2020", gis-athens-057aff6a-...): 6,092 MultiPolygons (Urban Atlas polygons, PROD_DATE 2010 basemap); fields CITIES, LUZ_OR_CIT, CODE, ITEM, avgLST, std_avgLST, min/max_avgLST. Average daytime LST Jun-Aug 2016-2020 in C (courtesy EXTREMA Global Services, ARTi Analytics BV). Land SURFACE temperature, polygon-level (std often 0).
- `c40solarmap` ("Solar Map", gis-athens-1f978bca-...): 66,661 building MultiPolygons, 60 MB GeoJSON; fields Height, roof, Area, Type, fclass, name, IRR_GLOBAL, IRR_SUN, IRR_SKY, USAB_AREA, N_PANELS, ACT_AREA, KWP, KWH_YEAR, C02_REDUC, ... No vegetation information; downloaded, not used.
- `xriseis` (ΓΠΣ land uses ΦΕΚ 80Δ/88): 13,466 zoning polygons; used only for zoned green (`ΑΣΤΙΚΟ ΠΡΑΣΙΝΟ - ΕΛΕΥΘΕΡΟΙ ΧΩΡΟΙ`, `ΚΟΙΝΟΧΡΗΣΤΟ ΠΡΑΣΙΝΟ`, `ΠΡΑΣΙΑ`). Zoning, not actual cover.
- No gis-athens layer for city-wide street trees, parks polygons or green areas exists (59 titles checked: only the three tree/park-related ones above plus playgrounds "Παιδικές Χαρές", not used). CKAN package_search q=trees -> 0 results; q=δέντρα -> only dendra. Separate `env-0xx-parko-*` park datasets exist on CKAN (not downloaded).

## Needs login / not obtainable

- Athens Trees ("Πληροφοριακό Σύστημα Δενδροφυτεύσεων"), https://athenstrees.cityofathens.gr : HTTP 200 for the page, but it is a Laravel + React back-office SPA (routes: login, register, dashboard, my-requests, tree-planting-requests, tree-plantings, tree-types, organizations, users). Unauthenticated `GET /api/tree-plantings` and `/api/tree-types` return HTTP 401 `{"message":"Unauthenticated."}`. No public API or download found. Registration would be required; not done. Press refers to the app for following plantings; the public-facing adopt-a-tree map is run by Novoville (https://novoville.com/adopt-a-tree-athens -> 302/200 text.novoville.com/adopt-a-tree_athens, app only; no data endpoint looked for).
- CLMS download portal (https://land.copernicus.eu/...) for full-resolution HRL TCD/STL/UA 2018 downloads: needs EU Login; not attempted. The portal page itself returned HTTP 200 (after 301 redirect). Urban Atlas 2018 land use full vector: `DownloadLayers/UA_UrbanAtlas_2018_DL` MapServer returns only a footprint (count 1), `UA_UrbanAtlasChange_2012_2018` only has 18 changed polygons in bbox, and `UrbanAtlas/UA_UrbanAtlas_2018` does not exist (HTTP 404 "Service not found"). So UA land use is 2012 only without login. `DownloadLayers/UA_STL_2018_DL` also footprint only (count 1).

## Failed / blocked

- OSM via Overpass (https://overpass-api.de/api/interpreter): NOT RUN. The tooling sandbox refused the POST (needs the operator's OK for host overpass-api.de); no workaround attempted. A plain HEAD to /api/status returned HTTP 406 (no UA). OSM tree counts and park share are therefore missing from the CSV. Queries to run are described in README.
- ETH Global Canopy Height 10 m 2020: https://share.phys.ethz.ch/~pf/nlangdata/ETH_GlobalCanopyHeight_10m_2020_version1/3deg_cogs/ETH_GlobalCanopyHeight_10m_2020_N36E021_Map.tif returned HTTP 429 (first HEAD), then HTTP 301 -> https://doi.org/10.3929/ethz-b-000609802 -> research-collection.ethz.ch landing page HTTP 429 on GET. Not downloaded.
- https://athenstrees.gr, www.athenstrees.gr: connection timeout (curl 28). athens-trees.cityofathens.gr, trees.cityofathens.gr, dentra/potizo.cityofathens.gr: DNS failure. https://www.cityofathens.gr/athens-trees: HTTP 404. (athens-trees.gr, trees.athens.gr, athenstrees.org: no connection.)
- Meta CHM directory listing (.../chm/): HTTP 403 (expected; single tile fetch works).
- Plain curl download of the full 65 MB WorldCover tile from AWS stalled at ~8 MB twice; replaced by HTTP range reads (success).
- STL 'UrbanAtlas/STL' MapServer layer 0 (2,692 polygons in bbox, fields COUNTRY, CITIES, FUA_OR_CIT, STL; vintage unspecified) also downloadable but not used.
