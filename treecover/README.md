# Tree cover by neighbourhood, Municipality of Athens

Files: `treecover_by_neighbourhood.csv` (144 rows, name exactly as `name` in nb.csv), `metrics_dictionary.csv` (source, year, resolution, licence per column), `sources.md` (every source tried and its HTTP outcome), `lowest15_tree_cover_with_sensor.csv`, `analysis_output.txt` (full correlation output), `scripts/` (Python; geo.py, dl_vec.py, compute.py, analyse.py; downloads were kept in /tmp/athens_treecover).

## Method
- Polygons: `polygon_geo` WKT from nb.csv, verified WGS84 (lon 23.685-23.791, lat 37.949-38.033), 144 valid, non-overlapping, 37.986 km2 total (areas computed in EPSG:3035).
- Rasters (WorldCover 10 m, Copernicus HRL/CLC+ 10 and 5 m, Meta canopy height ~1.2 m): a pixel counts for a neighbourhood if its centre falls inside the polygon; share = class pixels / pixels inside. Copernicus rasters were exported at native pixel size in EPSG:3035 with nearest-neighbour; the exported TCD values were spot-checked against the service /identify (match).
- Vectors (Urban Atlas Street Tree Layer 2018, Urban Atlas 2012 land use, City zoning): union of polygons intersected with the neighbourhood in EPSG:3035, share of neighbourhood area.
- Municipal totals are area-weighted over the 144 polygons.
- Heat: heat_station.csv, stations averaged per neighbourhood (`dmax` = summer mean daily max, `night` = night temperature). 77 of 144 neighbourhoods have a sensor (64 with 1 sensor, 10 with 2, 3 with 3). Station 7 was already excluded upstream (stuck sensor).

## Results

Municipal tree cover (area-weighted, 144 polygons):

| Source | % |
|---|---|
| WorldCover 2021 tree class (primary pixel metric) | 14.5 |
| WorldCover 2020 | 13.2 |
| Urban Atlas Street Tree Layer 2018 (polygon area share) | 9.6 |
| CLC+ Backbone 2021 trees | 9.7 |
| Meta canopy height >= 3 m | 9.6 (>= 5 m: 6.7) |
| HRL Woody Vegetation 2021 (trees + shrubs, 5 m) | 11.0 |
| HRL Tree Cover Density 2018: mean TCD / pixels with TCD > 0 | 2.0 / 4.7 |
| HRL Forest Type 2018 | 0.8 |

Sanity check against the published ~10 % (EEA Urban Atlas 2018; figure not re-verified here): the like-for-like comparison is the Urban Atlas Street Tree Layer 2018, same programme and year, which gives 9.6 %, consistent. CLC+ 2021 and Meta CHM land at the same value independently. WorldCover (14.5 %) is higher, not like-for-like: different definition (class 10 includes any tree-dominated 10 m pixel, mixed pixels), different year, and the neighbourhood polygons (37.99 km2) are not exactly the municipal boundary used by EEA. HRL TCD 2018 is much lower and is not a tree/no-tree share; it returns 0 at the sampled Lycabettus-slope and Filopappou points (confirmed with the service /identify, so not an export artefact), so it should not be used as an absolute measure here.

Agreement between sources across the 144 neighbourhoods (Pearson / Spearman vs WorldCover 2021): WC2020 0.98/0.96, CLC+ 2021 0.96/0.95, Street Tree Layer 2018 0.95/0.93, Meta CHM >=3 m 0.93/0.85, HRL WVL 2021 0.89/0.80, UA2012 green urban 0.90/0.77, HRL TCD 2018 mean 0.73/0.77, HRL Forest Type 0.30/0.26. Five independent products agree closely (r >= 0.93 for ranking of neighbourhoods); TCD 2018 agrees only moderately. Top by WorldCover: Lykavittos 84.7 %, Zappeio-Stadio 65.3 %, Acropolis-Filopappou 64.5 %. Neighbourhood-level differences are driven largely by a few large parks and hills.

### Tree cover vs heat (n = 77 neighbourhoods with a sensor)

| Tree metric | vs summer mean daily max: Pearson (p) / Spearman (p) | vs night temp: Pearson (p) / Spearman (p) |
|---|---|---|
| WorldCover 2021 | -0.13 (0.25) / -0.19 (0.11) | -0.31 (0.006) / -0.40 (<0.001) |
| WorldCover 2020 | -0.11 (0.32) / -0.19 (0.10) | -0.34 (0.003) / -0.50 (<0.001) |
| Street Tree Layer 2018 | -0.18 (0.12) / -0.22 (0.06) | -0.35 (0.002) / -0.45 (<0.001) |
| CLC+ 2021 | -0.10 (0.39) / -0.18 (0.13) | -0.26 (0.02) / -0.44 (<0.001) |
| Meta CHM >= 3 m | -0.10 (0.37) / -0.13 (0.26) | -0.23 (0.04) / -0.45 (<0.001) |
| HRL TCD 2018 mean | -0.26 (0.02) / -0.14 (0.23) | -0.31 (0.005) / -0.42 (<0.001) |

Plain reading: the daytime-maximum relationship is weak and mostly not statistically distinguishable from zero (|r| about 0.1-0.2; only the TCD Pearson reaches p < 0.05 and its Spearman does not). The night-temperature relationship is weak-to-moderate and negative (more tree cover, cooler nights; Spearman about -0.4 to -0.5), which is statistically clear at n = 77 but explains only about 10-25 % of variance, and is not proof of a causal cooling effect (hills and parks are also at the city edge and higher in altitude, with fewer buildings). Restricting to the 13 neighbourhoods with 2+ sensors (n = 13, WC2021 vs dmax r = -0.19, p = 0.53) or neighbourhoods >= 0.15 km2 (n = 71) gives the same picture. Full numbers for all metrics in `analysis_output.txt`.

Caveat: 64 of the 77 neighbourhood temperatures rest on a single sensor of unknown siting (rooftop, balcony, street, in-park), so the neighbourhood temperature is a noisy proxy and the tree-cover signal may be diluted or confounded.

Table of the 15 lowest-WorldCover-2021 neighbourhoods with a sensor is in `lowest15_tree_cover_with_sensor.csv` (all have WC2021 < 2 %; their summer max ranges 34.3-39.2 C vs a median of 36.8 C across the 77, i.e. the hot end and the cool end both occur among low-tree-cover places).

## Caveats
- 10 m products miss individual street trees and narrow canopies (< ~10 m wide); small neighbourhoods (many are 0.15-0.3 km2, smallest 0.017 km2 = Syntagma) have only a few hundred pixels, so percentages are noisy; mixed pixels (tree over road/building) are classed by the dominant cover or density, so tree share in dense streets is under-estimated, and park/hill pixels over-represented.
- Classification years differ (TCD 2018, WorldCover 2020/2021, CLC+ 2021, Meta ~2018-2020 imagery, Urban Atlas 2012/2018); the city planted trees since. Heat data periods are those of heat_station.csv, not matched year-by-year.
- HRL TCD 2018 appears to under-detect Mediterranean pine and olive canopy in this area; WorldCover class 10 may include dense shrub/olive canopy; Meta CHM heights are model estimates (RMSE a few metres).
- `ua2012_*` is 2012 and a land-use class, not cover. `city_zoned_green_pct` is zoning, not actual green. The National Garden tree layer covers one park only (6,354 points, 4,622 existing), so `city_national_garden_trees_*` is non-zero for a single neighbourhood and is not a city-wide tree count. `city_lst_summer_day_2016_2020_c` is satellite surface temperature, not air temperature.
- Urban Atlas forest (31000) and herbaceous (32000) classes cover 0 % of every neighbourhood polygon (they lie on hills outside the polygons), so those columns are not included.
- OSM mapped trees and OSM park share are NOT computed: the Overpass request was blocked by the tooling and was not retried. To add them, POST to https://overpass-api.de/api/interpreter queries for `node["natural"="tree"]`, `way["natural"="tree_row"]`, `leisure=park|garden`, `landuse=forest|grass|recreation_ground` in the bbox, then count points / intersect areas per polygon (the pipeline in scripts/compute.py has the helper pattern).
- The Athens Trees system (athenstrees.cityofathens.gr) requires login; no planted-tree data could be obtained.

## Validation
144/144 neighbourhoods present, names identical and in nb.csv order; all `*_pct` columns within 0-100 (checked); polygon areas sum to 37.986 km2 with no overlaps; no NaN in tree metrics (67 neighbourhoods have no sensor, so heat columns are blank there).
