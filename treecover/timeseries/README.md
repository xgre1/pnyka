# Athens neighbourhood vegetation time series (Sentinel-2 NDVI, 2017-2026) and STL 2012 vs 2018

Everything here is produced from open data read anonymously (no login, no accounts). Scripts are in `scripts/` (run order 01, 02, 03, 04; venv and downloads were under `/tmp/athens_ndvi/`).

## Files
- `ndvi_by_neighbourhood_year.csv` long format: neighbourhood, year, n_scenes, n_pixels, valid_pixel_frac, mean_ndvi, veg_share_pct (median NDVI >= 0.4), dense_share_pct (>= 0.6). 144 neighbourhoods x 10 years. **2017 is in the file but is flagged unreliable (see below) and excluded from all change statistics.**
- `change_by_neighbourhood.csv` first-two-years vs last-two-years (2018-19 vs 2025-26), linear trend and p-value, noise floor, `change_reliable`, `direction`, raw and normalised deltas, same for vegetated share (`veg_change_reliable`).
- `scenes_used.csv` every candidate scene: id, date, scene cloud %, baseline, offset applied, valid fraction inside the AOI, AOI median NDVI, `used` flag.
- `municipal_by_year.csv` pixel-weighted municipal totals per year.
- `stl_2012_2018_by_neighbourhood.csv` Copernicus Urban Atlas Street Tree Layer 2012 and 2018 per neighbourhood and difference.

## Method
- STAC: `https://earth-search.aws.element84.com/v1/search`, collection `sentinel-2-l2a`, bbox 23.68,37.94,23.80,38.04, 1 Jun-31 Aug each year 2017-2026, `eo:cloud_cover < 10`. Earth Search worked; Planetary Computer was not needed.
- Tile: MGRS 34SGH only. It covers the whole municipality (grid of 943x956 px at 10 m in EPSG:32634 had full valid coverage). 35SKC items also intersect the bbox but only at the tile edge, so they were ignored (avoids mixing two geometries).
- Assets read with GDAL/rasterio over HTTPS range requests from `sentinel-cogs.s3.us-west-2.amazonaws.com` (AWS_NO_SIGN_REQUEST=YES): `red` (B04), `nir` (B08), `scl` (20 m, nearest-neighbour resampled to 10 m), windowed to the bounds of all neighbourhoods plus 100 m.
- Scene choice: per year up to 8 evenly spaced candidate dates (the brief said ~6; 8 candidates because some scenes fail the local clear test), one item per date (highest processing baseline when an old and a reprocessed 05.00 item exist for the same date). A scene is kept only if >= 60% of the AOI is clear after the SCL mask. Resulting scenes per year: 2017: 3, 2018: 6, 2019: 7, 2020: 8, 2021: 7, 2022: 8, 2023: 8, 2024: 8, 2025: 8, 2026: 7.
- SCL mask: removed classes 0,1 (no data, saturated), 3 (cloud shadow), 6 (water), 7 (unclassified), 8,9,10 (clouds, cirrus), 11 (snow). Kept 2,4,5.
- **Processing baseline / offset**: reflectance = DN x scale + offset using the per-asset `raster:bands` scale/offset in the STAC item (authoritative). Items with baseline < 04.00 natively have offset 0 (2017 N00.01, 2018-2021 N02.xx/03.xx); baseline >= 04.00 items (2022 onwards) carry the 1000 DN offset (`-0.1`). Earth Search also published reprocessed baseline 05.00 copies of 2018-2021 scenes (`earthsearch:boa_offset_applied = True`, offset -0.1); where such a copy exists it was used, so 2018-2026 are all baseline >= 04.00 and offset-consistent. Negative reflectances after the offset were clipped to 0, NDVI computed only where NIR+red > 0.02 and clipped to [-1,1]. (A first run without clipping produced impossible NDVI means >1 in dark pine forest; this was fixed and all outputs are from the fixed run.)
- Per pixel: median NDVI over the season's kept scenes (>= 2 valid observations required when >= 3 scenes).
- Zonal stats: pixel centre inside polygon (rasterio `rasterize`, all_touched=False), unweighted by partial pixel coverage. Small neighbourhoods (<0.1 km2 = <1000 px) are noisy.

## Validation (Spearman, n = 144)
- 2018 vegetated share (NDVI >= 0.4) vs `ua_stl2018_pct`: 0.840 (dense share >= 0.6: 0.879)
- 2021 vs `wc2021_tree_pct`: 0.821 (dense 0.850); vs `metachm_ge3m_pct`: 0.842 (dense 0.853)
- 2020 vs `wc2021_tree_pct`: 0.837; vs `metachm_ge3m_pct`: 0.865
So spatially the index tracks the existing tree products well (rank agreement), but NDVI >= 0.4 is all green vegetation, not trees, so absolute values (municipal 27-34%) are far above tree cover (10-14%) and are not tree cover.

## Municipal totals (pixel-weighted)
| year | scenes | mean NDVI | vegetated % (>=0.4) | dense % (>=0.6) |
|---|---|---|---|---|
| 2017 (unreliable) | 3 | 0.197 | 15.6 | 4.8 |
| 2018 | 6 | 0.366 | 34.4 | 24.6 |
| 2019 | 7 | 0.361 | 33.7 | 23.4 |
| 2020 | 8 | 0.361 | 33.6 | 23.4 |
| 2021 | 7 | 0.359 | 33.4 | 23.4 |
| 2022 | 8 | 0.329 | 29.6 | 19.4 |
| 2023 | 8 | 0.325 | 29.2 | 19.4 |
| 2024 | 8 | 0.320 | 28.6 | 18.6 |
| 2025 | 8 | 0.329 | 29.9 | 19.8 |
| 2026 | 7 | 0.311 | 27.7 | 17.7 |

2017: all 2017 scenes (baseline N00.01) have very low SCL clear fractions (33-86%) and a municipal NDVI far below every other year (median scene NDVI 0.15-0.23 vs 0.22-0.31), a step that cannot be real vegetation. Treated as a data/processing artefact and excluded from change statistics.

There is a step down between 2021 (33.4%) and 2022 (29.6%) that persists to 2026. It coincides with the switch from reprocessed-05.00 to native 04.00+ products and with a multi-year Greek drought, and it hits the greenest neighbourhoods hardest; with this data it cannot be separated into processing vs drought vs real loss.

## Noise and stability
- Municipal-mean NDVI swing between years 2018-2026: 0.055 (0.366 to 0.311); vegetated share swing 6.7 pp. Within 2018-2021 the year-to-year swing is only ~0.007.
- Stable reference: 19 dense built neighbourhoods (wc2021 < 2%, STL2018 < 1%, MetaCHM < 2%) and Lykavittos (+Kolonaki-Lykavittos). Raw SD of their mean NDVI across years: built median 0.0135, Lykavittos 0.064 (raw, the pine forest dries down), Kolonaki-Lykavittos 0.028.
- Normalisation: subtract each year's city-wide median deviation (median over 144 neighbourhoods of NDVI minus the neighbourhood's own multi-year median). Year effects range from +0.020 (2021) to -0.020 (2026) NDVI.
- Residual SD about each neighbourhood's own linear trend after normalisation: built median 0.0062 (p90 0.010), Lykavittos 0.016, all-neighbourhood median 0.0075 NDVI; vegetated share about 1.0 pp. These are the noise floors (each neighbourhood uses max(own residual SD, 0.0075)).
- Real vs noise: a normalised change in mean NDVI of ~0.015-0.02 (about 2 pp vegetated share) is the smallest detectable; changes below that are noise.

## Change (2018-19 mean vs 2025-26 mean)
`change_reliable` = |normalised delta mean NDVI| > 2 x noise AND linear-trend p < 0.05 (no multiple-testing correction; with 144 tests some false positives are expected).
- 44 flagged: 16 gains, 28 losses.
- **Read the gains with care.** They are relative to the city-wide trend: the normalisation removes the municipal decline, so "gains" are neighbourhoods whose raw NDVI stayed flat while the city fell. Their raw deltas are ~0 (-0.005 to +0.004). The only neighbourhood with a raw positive change beyond noise is ΣΥΝΤΑΓΜΑ (raw +0.032, tiny, 0.017 km2, 170 px, p = 0.02). No neighbourhood shows a reliable absolute gain in green cover; the absolute picture is a broad decline (median raw delta -0.028, 117 of 144 neighbourhoods below -2 noise).
- Top relative losses (normalised delta NDVI): ΠΡΟΜΠΟΝΑ2 -0.179, ΛΥΚΑΒΗΤΤΟΣ -0.121, ΑΡΧΑΙΟΛΟΓΙΚΟΣ ΧΩΡΟΣ ΑΚΡΟΠΟΛΗΣ-ΦΙΛΟΠΑΠΠΟΥ -0.105, ΣΧΟΛΗ ΕΥΕΛΠΙΔΩΝ -0.098, ΑΤΤΙΚΟ ΑΛΣΟΣ -0.074, ΠΑΡΚΟ ΧΩΡΟΦΥΛΑΚΗΣ-ΣΤΡΑΤΙΩΤΙΚΑ ΝΟΣΟΚΟΜΕΙΑ -0.074, Α ΝΕΚΡΟΤΑΦΕΙΟ -0.069, ΑΛΣΟΣ ΓΟΥΔΗ-ΦΥΤΩΡΙΟ ΔΗΜΟΥ ΑΘΗΝΑΙΩΝ -0.069, ΠΕΝΤΑΓΩΝΟ -0.069, ΕΛΑΙΩΝΑΣ -0.062. They are parks, hills and cemeteries with high NDVI, which is the signature of drought/dry-down of irrigated and unirrigated vegetation (and possibly baseline), not necessarily tree loss. ΠΡΟΜΠΟΝΑ2 (0.068 km2) is the only one with a large veg-share drop (-19 pp) worth a manual look.
- Top relative gains: ΣΥΝΤΑΓΜΑ +0.059, ΑΝΩ ΠΑΤΗΣΙΑ +0.031, ΑΓΙΑ ΤΡΙΑΔΑ +0.030, ΑΓΙΑΣ ΖΩΝΗΣ +0.028, ΦΩΚΙΩΝΟΣ ΝΕΓΡΗ +0.025, ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ +0.024, ΚΑΤΩ ΠΑΤΗΣΙΑ I +0.024, ΨΥΡΡΗ-ΚΟΥΜΟΥΝΔΟΥΡΟΥ +0.024, ΜΕΤΑΞΟΥΡΓΕΙΟ +0.022, ΔΟΥΡΓΟΥΤΙ ΙΙ +0.022 (all relative, see above).
- Plain conclusion: a reliable *absolute* change in green cover per neighbourhood cannot be asserted from this data. What is detectable is (a) a city-wide decline in summer NDVI after 2021 whose cause (drought, baseline, real loss) is not separable here and (b) relative differences between neighbourhoods of >= ~0.02 NDVI. A true tree-count/cover change needs a different source (e.g. same-algorithm tree layers) or a drought-normalising reference such as a spring or multi-season NDVI.

## STL (Copernicus Urban Atlas Street Tree Layer) multi-year
- Two editions are queryable anonymously on `https://image.discomap.eea.europa.eu/arcgis/rest/services/UrbanAtlas`: `STL/MapServer/0` (UA2012 STL, field `STL`) and `UA_StreetTreeLayer_2018/MapServer/0` (field `stl`); download copies under `DownloadLayers/UA_STL_2012_DL` and `UA_STL_2018_DL`. No 2021 STL exists on either EEA server (`land.discomap` has UA 2012 and change layers only; UA/STL 2021 is not exposed on these services).
- Per-neighbourhood tree cover from the geometries (area-based intersection, EPSG:32634): municipal 2012 = 11.86%, 2018 = 9.55% (the 2018 value reproduces `ua_stl2018_pct`, max abs diff 0.0005). Neighbourhood change 2012 to 2018: median -1.8 pp, range -24.6 to +5.0 pp; Spearman 2012 vs 2018 = 0.91. Biggest drops: Α ΝΕΚΡΟΤΑΦΕΙΟ -24.6, ΠΕΝΤΑΓΩΝΟ -10.1, ΣΧΟΛΗ ΕΥΕΛΠΙΔΩΝ -10.0, ΛΥΚΑΒΗΤΤΟΣ -8.9; biggest gains ΠΡΟΜΠΟΝΑ2 +5.0, ΩΔΕΙΟ +4.0.
- Methodology caveat: the editions are separate productions (2012 on the UA2012 mask/2012 imagery, 2018 on the 2018 mask/imagery, different attribute schemas and producers' service descriptions). Both define STL as tree rows/patches >= 500 m2 and >= 10 m wide over artificial surfaces. I could not verify that the delineation rules are identical, so a part of the -2.3 pp municipal fall may be method change rather than tree loss; treat as indicative.

## Failures / HTTP notes
- First pip install attempt: "Network is unreachable" (no HTTP status; transient, succeeded on retry).
- EEA STL 2012 query: one HTTP 500 (HTML error page) on a paged request; retry succeeded (HTTP 200).
- EEA ArcGIS folder `Urban_Atlas` does not exist: HTTP 200 with JSON body `{"code":404,"message":"Folder not found"}`.
- No other failures; Earth Search STAC returned HTTP 200 for all 10 yearly searches.

## Caveats
NDVI measures all green vegetation (grass, shrubs, crops, irrigated lawns), not only trees. 10 m pixels miss single street trees and mix canopy with pavement/buildings (mixed pixels depress NDVI in narrow streets); thresholds 0.4/0.6 are conventional, not calibrated for Athens. Summer NDVI depends on rainfall of the preceding winter/spring, drought and irrigation, so the absolute level moves between years independent of canopy. Scene sets differ per year (dates, clear fractions); the median composite reduces but does not remove this. Small neighbourhoods have few pixels and larger noise. Sentinel-2 processing baselines changed over 2017-2026 and cannot be fully harmonised from the public archive.
