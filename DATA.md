# Athens neighbourhood heat, air and child-facility dataset

Component data only. There is deliberately NO composite or priority score; choose weights from the component columns.

Built on 2026-11-21 (UTC) from City of Athens open data (https://opendata.cityofathens.gr).

## Files

| File | Rows | Content |
|---|---|---|
| `neighbourhoods.geojson` | 144 features | Neighbourhood polygons (WGS84 / EPSG:4326) with every column listed below as feature properties |
| `neighbourhoods.csv` | 144 | Same properties, no geometry (UTF-8, empty cell = null) |
| `stations.csv` | 100 | Per-station heat and air metrics, flags, and inclusion status |
| `README.md` | - | This file |

Empty CSV cells and JSON `null` mean "no value". No NaN strings are written. Booleans are `True`/`False` in CSV and `true`/`false` in GeoJSON.

## neighbourhoods.* columns

| Column | Meaning |
|---|---|
| `neighbourhood_id` | `neighbourhood_id` from the portal neighbourhood layer (1-144) |
| `name` | Neighbourhood name (`name` field, Greek, as published) |
| `friendly_name` | `friendly_name` field from the portal (often empty) |
| `municipal_district_id` | Municipal district 1-7 |
| `has_sensor` | true if at least one station of `env-all-stations` is assigned to the neighbourhood (81 true, 63 false) |
| `n_stations` | Number of stations assigned to the neighbourhood |
| `n_stations_heat` | Stations actually contributing to the heat columns (after exclusions) |
| `n_stations_air` | Stations contributing to the air columns |
| `station_names` | Station names joined with ` \| ` |
| `heat_mean` | Mean of station summer mean temperature, degrees C |
| `heat_daily_max` | Mean of station mean-daily-maximum temperature, degrees C |
| `heat_night` | Mean of station mean night temperature (local 00:00-05:59), degrees C |
| `hours_above_35` / `hours_above_38` | Mean over stations of hours with reading > 35 / > 38 degrees C in summer (1 decimal) |
| `pm2_5`, `pm10`, `no2`, `o3` | Mean over stations of cleaned means, ug/m3, 2026-01-01 to 2026-11-21 |
| `pm_spiky` | true if any contributing station is flagged `pm_spiky` (null when no air data) |
| `n_schools` | Public schools (point count inside polygon) |
| `n_playgrounds` | Playgrounds |
| `n_nurseries` | Nurseries / infant-toddler day-care stations (layer "year 2019") |
| `n_friendship_clubs` | Λέσχες Φιλίας |
| `n_clinics` | Municipal clinics |
| `n_pocket_parks` | Pocket parks (Πάρκα Τσέπης) |
| `area_km2` | Polygon area, km2 (spherical R=6371.0088 km, local equirectangular projection, accurate to well under 1% at this size) |
| `heat_rank` | 1 = hottest `heat_daily_max` among the 77 neighbourhoods that have a value; ties share the lowest rank; null otherwise |

For the 63 neighbourhoods without a station every heat/air column is null, `has_sensor` is false and `n_stations` is 0. Nothing is interpolated. Facility counts are filled for all 144 neighbourhoods (zero is a real zero).

Four neighbourhoods have a station but no heat value (`has_sensor` true, heat null): ΠΟΛΥΓΩΝΟ Ι, ΚΟΛΩΝΟΣ, ΕΞΑΡΧΕΙΑ (station dropped for fewer than 46 valid days or no summer data) and ΛΟΦΟΣ ΛΑΜΠΡΑΚΗ (station 7, stuck sensor). Their air columns may still be present.

## stations.csv columns

`station_id`, `station_name`, `address` (from the registry; empty for stations missing from it), `neighbourhood_id`, `neighbourhood_name`, `municipal_district_id`.

Heat: `heat_mean`, `heat_daily_max`, `heat_night`, `hours_above_35`, `hours_above_38`, `valid_days`, `summer_temp_hours` (hourly temperature readings in the summer window). `heat_included` is true only if the station has at least 46 valid days and is not station 7. Heat values are shown for every station that has data, even when `heat_included` is false; only included stations feed the neighbourhood columns. `heat_flag` is one of `excluded_stuck_sensor` (station 7, Λόφος Λαμπράκη), `fewer_than_46_valid_days`, `no_summer_temperature_data`, or empty.

Air: `pm2_5`, `pm10`, `no2`, `o3` (cleaned means, blank if fewer than 3000 valid hours), `*_valid_hours`, `pm2_5_raw_mean` (before cleaning), `*_dropped_hours` (hours removed by the outlier caps), `pm_spiky`, `air_included` (at least one pollutant with >= 3000 valid hours).

Station 7 is excluded from heat aggregation only; its air values are used as normal.

## Method

Input: `env-all-stations` hourly CSV, 607,774 rows, 100 stations, `timestamp` (UTC) from 2026-01-01T00:00 to 2026-11-21T00:27. Exact duplicates on (`station_id`, `timestamp`) were removed (81 rows dropped, 607,693 kept, first occurrence kept).

Heat (stations.csv):
1. Timestamps converted from UTC to Europe/Athens. Summer = local 2026-06-01 00:00 up to but excluding 2026-09-01 00:00. Rows with null temperature are ignored.
2. `heat_mean` = mean of all hourly temperatures. `heat_night` = mean of hourly temperatures with local hour 0-5.
3. A day is valid if the station has >= 18 hourly temperature readings on that local date. `heat_daily_max` = mean over valid days of that day's maximum; `valid_days` = number of valid days.
4. `hours_above_35` / `hours_above_38` count hourly readings strictly above the threshold (no scaling for missing hours).
5. Kept for aggregation: stations with `valid_days` >= 46, minus station 7. Result: 93 of 100 stations; 185,356 hourly readings used by included stations. Among included stations valid days range 50-85.
6. Check values reproduced: station 65 = 41.224, station 151 = 31.857, station 55 = 33.036.

Air (stations.csv):
1. Local time from 2026-01-01 00:00 to the end of the data (2026-11-21), after de-duplication.
2. Per pollutant, hourly values above PM2.5 > 500, PM10 > 1000, NO2 > 300, O3 > 400 are dropped; mean of the remainder. Missing values are ignored.
3. The 3000 valid-hour requirement is applied per pollutant (a station can keep NO2 and lose PM). 97 stations have at least one pollutant.
4. `pm_spiky` = |raw PM2.5 mean - cleaned PM2.5 mean| / cleaned mean > 20%. 6 stations are flagged: 61, 76, 77, 100, 109, 112. Note that the cleaning only removes the extreme tail; flagged stations still have unreliable PM2.5 and PM10.

Neighbourhood aggregation:
- Station to neighbourhood: the neighbourhood name carried on each row of `env-all-stations` matches the `name` of exactly one polygon in the neighbourhood layer (81 distinct neighbourhoods). The station registry (`env-stations-registry`) lists only 78 of the 100 stations, so it was used only for addresses.
- Each neighbourhood value is the plain unweighted mean over its contributing stations. 66 neighbourhoods have one station, 11 have two and 4 have three.

Point layers:
- GeoJSON downloaded from the resource URLs below (WFS, EPSG:2100, MultiPoint or Point). Converted to WGS84 with a built-in implementation: inverse Transverse Mercator (GRS80, central meridian 24E, scale 0.9996, false easting 500000) followed by a 3-parameter datum shift GGRS87 to WGS84 (dX -199.87, dY 74.79, dZ 246.62 m). Accuracy is roughly 1-2 m, enough for neighbourhood counting. All converted points fall inside roughly lat 37.94-38.03, lon 23.68-23.79 except as noted in the validation.
- Each point is assigned to the smallest-area neighbourhood polygon containing it (polygon holes respected). No points were contained by more than one polygon. Points outside every polygon are not counted.

| Layer | Dataset slug (opendata.cityofathens.gr/dataset/...) | Features | Inside polygons | Outside |
|---|---|---|---|---|
| schools | `gis-athens-3bbfb156-7722-11ee-bdf0-0242ac120004` (Δημόσια Σχολεία, layer sxoleia_2023) | 401 | 397 | 4 |
| playgrounds | `gis-athens-894dd9fc-d618-11ee-9a8a-0242ac120004` (kpx24) | 89 | 89 | 0 |
| nurseries | `gis-athens-62bd77fc-3d5e-11ec-a4ea-0242ac120009` (brefo2019) | 72 | 72 | 0 |
| friendship clubs | `gis-athens-b1f3060c-7adf-11ec-bf2f-0242ac120006` (lesxes) | 25 | 25 | 0 |
| clinics | `gis-athens-9f6d7fe4-ca9f-11f0-b1bd-0242ac1c0007` (iatreia) | 7 | 7 | 0 |
| pocket parks | `gis-athens-d87bc472-8080-11ef-9cff-0242ac170006` (PocketParks2) | 10 | 10 | 0 |

All six downloads returned HTTP 200. Source CRS of all layers: EPSG:2100 (urn:ogc:def:crs:EPSG::2100), reprojected.

## Sources and download timestamps

Resource URL pattern (GeoJSON, CKAN resource format "GeoJSON"): `http://gis.cityofathens.gr/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typename=geonode%3A<layer>&outputFormat=json&srs=EPSG%3A2100&srsName=EPSG%3A2100` with `<layer>` as in the table above (sxoleia_2023, kpx24, brefo2019, lesxes, iatreia, PocketParks2).

| Layer | CKAN metadata_modified | Resource last_modified | Downloaded (UTC) |
|---|---|---|---|
| schools | 2026-05-28T16:22:20 | not given | 2026-11-21T02:09:36Z |
| playgrounds | 2026-05-28T16:24:09 | not given | 2026-11-21T02:09:37Z |
| nurseries | 2026-05-28T16:28:37 | not given | 2026-11-21T02:09:38Z |
| friendship clubs | 2026-05-28T16:28:25 | not given | 2026-11-21T02:09:39Z |
| clinics | 2026-05-28T16:25:36 | not given | 2026-11-21T02:09:40Z |
| pocket parks | 2026-05-28T16:21:22 | not given | 2026-11-21T02:09:41Z |

Other inputs (read from a local copy fetched earlier from the same portal, file times 2026-11-21 03:45 local): hourly data from dataset `env-all-stations` (https://opendata.cityofathens.gr/dataset/env-all-stations), station registry from `env-stations-registry`, neighbourhood polygons (`nb.csv` / `neighbourhoods-athens.json`, 144 neighbourhoods, WKT polygons in WGS84) and municipal districts (`md.csv`) were supplied as local files from the same portal's neighbourhood data; their exact dataset slug and download time were not recorded and they were not re-downloaded in this run.

Considered and not used: no dedicated park or green-space point layer exists among the 60 `gis-athens-*` datasets. "Δένδρα Εθνικού Κήπου" is a tree inventory of one garden and "ΓΠΣ Χρήσεις Γης" is a land-use polygon layer; neither was included. Pocket parks is the only green-space layer in the dataset.

## Licence

The portal's dataset pages declare the licence on each resource through the EU authority URI:
- `env-all-stations`: `CC_BY_4_0` (CC BY 4.0), as the task brief stated.
- The six GIS point layers: `CC_BY_3_0` (CC BY 3.0), NOT 4.0. The dataset pages for these layers show "Resource has open license ... CC_BY_3_0".
CKAN's own `license_id` field is empty for all of them, so the resource-level URI is the only statement found. Attribution to the City of Athens (opendata.cityofathens.gr) is required; confirm wording with the portal before publication. This derived dataset should be shared with attribution and a note that it was transformed.

## Known limits

- Sensors have no coordinates and their siting (sun, shade, height, surface) is unknown. A neighbourhood value describes one unit, not the neighbourhood. Some very high values may reflect a sun-exposed sensor.
- 63 of 144 neighbourhoods have no sensor at all; their heat and air values are null, not estimated.
- Neighbourhood values mostly rest on one sensor (66 of 81 sensor neighbourhoods). Rank differences of a few tenths of a degree are not meaningful.
- Only 77 neighbourhoods have a heat value; 4 more have a station that was excluded.
- PM sensors spike. Cleaning removes only extreme values; 6 stations are flagged `pm_spiky` and their PM figures should not be trusted without care.
- Air means cover 2026-01-01 to 2026-11-21 (about 10.7 months), not a full year and not the same period as the heat window; they mix winter and summer.
- Heat metrics cover summer 2026 only (1 Jun - 31 Aug, local time). One summer is not a climatology.
- Station 7 (Λόφος Λαμπράκη) is excluded from heat because its temperature sensor is stuck; its neighbourhood has no heat value.
- Several stations are excluded for too few valid days (10, 56, 63, 71, 114) or no summer temperature data (74).
- Hourly means for hours above thresholds count readings, not elapsed hours; stations with gaps understate exposure.
- Facility counts use the portal layers as published (nurseries layer is the 2019 edition, schools layer is `sxoleia_2023`). 4 school points fall outside every neighbourhood polygon and are not counted. Neighbourhood polygons do not tile the whole municipality.
- Counts are points inside a polygon; they say nothing about capacity, enrolment or distance to the facility.
- Neighbourhoods differ in area (`area_km2`); counts are not normalised.
