# Capacity by neighbourhood - how much of each intervention is physically there

Measured quantities (m2, m, counts) per neighbourhood of the Municipality of Athens, for the team's cost tool: the Municipality enters unit prices, the tool multiplies by these quantities. Computed 2026-11-21. Headline numbers and validation: `capacity_summary.md`. Every column: `metrics_dictionary.csv` (unit, source and date, method, known error).

## Files

| File | Content |
|---|---|
| `capacity_by_neighbourhood.csv` | 144 rows x 86 columns |
| `capacity_by_community.csv` | 7 Municipal Communities (municipal_district_id 1-7), the municipality total, the 62-neighbourhood group with Street Tree Layer 2018 cover <2%, and the remaining 82. Ratios recomputed from sums |
| `capacity_summary.md` | Totals, group, top 15 lists, validation, spot checks |
| `metrics_dictionary.csv` | Dictionary of all columns |
| `facility_to_building_matches.csv` | Each school/municipal facility point with the building it was matched to, match type, distance, number of buildings within 30 m |
| `validation.json` | Raw validation numbers |
| `inputs_fetched/` | Two City WFS layers fetched for this task (`kt_dioikisis`, `pois_yperesies_da`); the script reads them from `/tmp/athens_capacity/dl/` (copy there to rerun) |
| `scripts/` | `01_compute_capacity.py` (all geometry), `02_report.py` (community table, summary, dictionary). Run with `/tmp/athens_streets/venv/bin/python -I` |

## Methods (short)

- CRS: everything measured in EPSG:2100 (Greek Grid). Neighbourhood polygons sum to 37.956 km2.
- Roofs: solar-map polygons (WGS84), reprojected; `roof_area_m2` is polygon area clipped to the neighbourhood. Building counts, usable area and kWp are assigned by the building's representative point (whole building). Layer attribute `Area` equals geometry area. Attribute `roof` is not documented (values 71-300, probably roof elevation; unverified) and is not used. The layer has no flat/pitched flag: flat vs pitched is UNKNOWN. `USAB_AREA` is the City solar model's usable area (63% of footprint); it is a PV notion, not a measure of paintable/green-roof area.
- Municipal and school roofs: point layers matched to the building polygon containing the point, otherwise the nearest within 30 m; points sharing a building counted once. "Municipal" here = nurseries, Λέσχες Φιλίας, clinics, administration buildings (`kt_dioikisis`, 9) and municipal services (`pois_yperesies_da`, 19). The City WFS has no full municipal building register (checked all 60 feature types in the capabilities), so municipal-building roof is a LOWER bound: it misses libraries, sports halls, markets, cultural buildings. School roof is also a lower bound (one building per point; a school is usually several). Within-30 m upper bounds are given in the summary.
- Streets: OSM named ways (20,983; Overpass snapshot 2026-11-21), densified to 10 m segments, each segment assigned by its midpoint. Length by highway class. Surface = length x width.
- Open space: union of City zoning green classes (`xriseis_green_only`), UA2012 14100, 14200, 31000, 32000, minus building footprints. Residual = area - roof - that green - estimated street area. It is a residual, carries the error of all three terms, can be negative (4 neighbourhoods; flagged and floored).
- Trees: Meta CHM share of pixels with 3 <= height <= 100 m inside the polygon (same convention as `treecover/scripts/compute.py`; reproduces `treecover_by_neighbourhood.csv` to 0.0005 pp) times polygon area. STL2018 = union of polygons clipped. Deficit to t% = max(0, area x t - canopy), per neighbourhood, so group/municipality sums are sums of per-neighbourhood deficits (not netted). Illustrative trees = ceil(deficit / crown area), crown diameter 4, 6, 8 m (12.6, 28.3, 50.3 m2).
- Sites: counts from `streets/sites_with_plantings.csv` with `canopy_pct_150m` < 5. Elderly clubs = Λέσχες Φιλίας.

## Default street widths (metres, ESTIMATE)

| highway | carriageway two-way | carriageway one-way |
|---|---|---|
| trunk | 14.0 | 7.5 |
| primary | 12.0 | 7.0 |
| secondary | 9.5 | 6.0 |
| tertiary | 7.5 | 5.0 |
| unclassified | 6.0 | 4.5 |
| residential | 6.0 | 4.0 |

Plus sidewalks 2 x 2.0 = 4.0 m (2.0 m for a one-way half of a `dual_carriageway=yes` road). `living_street` and `pedestrian`: 6.0 m total, no extra sidewalk. Overrides: numeric `width` tag (2-40 m) replaces the carriageway (5.4% of length); else `lanes` x 3.0 m (36.7% of length). Error band used: +-30% (columns `_low`/`_high`); an assumption, not a statistical interval. `street_area_defaults_only_m2` shows the result ignoring tags. Cross-check: UA2010 road land is 6.46 km2 for the municipality vs 8.10 km2 estimated (range 5.67-10.52); UA2012 has no road class in the downloaded layer.

## Caveats - read before multiplying by prices

- ROOF FOOTPRINT IS NOT USABLE ROOF. Ownership (public vs private; the solar map does not say; 97% of buildings have an empty `Type`), structural capacity, existing installations/equipment/skylights, roof access, pitched roofs (no flat/pitched flag), heritage and listed buildings (Historic Centre, Acropolis protection zone) are all unknown. The solar-map layer does not state its date. Treat the number as an upper bound of what could be treated, e.g. "up to X m2 of footprint".
- 1,553 solar-map polygons lie outside the municipal polygons and are excluded. 3,457 buildings have Height 0 (unknown height). 0.09% of polygon area overlaps another polygon.
- OSM: named streets only, so unnamed service roads, footways, stairs, cycleways, and squares are not counted; the extract also contained 1,835 km of ways outside the municipality (excluded). OSM completeness and tag quality were not audited. Dual carriageways drawn as two one-way ways use the one-way default; wide medians are not counted.
- Street surface mixes carriageway and pavement (not separated in the columns); for "cool pavement" pricing decide which part is in scope; sidewalk width is the largest single uncertainty. Pedestrian streets are listed separately by length (69.6 km, 25.1 km in the low-tree group).
- Green/open union mixes planning zoning (not land cover; some zoned green is built or paved), UA2012 (reference year 2012, 83% of the municipality covered) and the buildings layer; the residual is NOT verified unsealed ground.
- Canopy model: Meta CHM imagery is ~2018-2020, i.e. 6-8 years old; it misses trees planted since, includes some tall non-tree objects, and cannot be validated against the field here. STL2018 covers street trees of 2018 only. The two measures agree at municipality level (9.6% each) but differ per neighbourhood. The group definition (<2%) uses STL2018 as specified; the deficits use the CHM.
- Illustrative tree numbers are arithmetic, not a planting plan: no check of available planting space, soil, utilities, crown overlap, mortality or time to maturity. Municipality-level deficit to 10% is 0.16 km2 netted but 1.69 km2 when summed per neighbourhood; the latter is the quantity relevant for neighbourhood-by-neighbourhood pricing.
- Facility layers are of mixed vintage (nurseries 2018-12-24; schools: 401 points of which 4 lie outside; school point layer vs `sxoleia_2023` WFS layer not compared). Courtyards and campuses: a point can fall in a courtyard, so contained/nearest matching can pick a neighbouring building; 90% of school points have more than one building within 30 m.
- Plantings: 14,251 trees (12,442 records) dated 2024-01-01 or later in `athenstrees/plantings_points.csv`; 23 records fall outside the neighbourhood polygons and are in the municipality-level total only in `validation.json`, not in per-neighbourhood columns (per-neighbourhood sum 14,228).
- `team.md` asks that findings be recorded in σημειώματα ομάδας; this task was limited to writing under `capacity/`, so no finding file was written.
