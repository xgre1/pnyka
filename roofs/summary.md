# Roof status of municipal and school buildings: green / bright / ordinary / too_small

Computed 2026-11-21 from Sentinel-2 L2A, summer 2025. Every number below was computed by us with the scripts in `roofs/scripts/` (output of `04_summary.py`), unless marked otherwise.

## Headline

**Most facility roofs cannot be measured at 10 m.** After shrinking each building polygon by 5 m, only 39 of the 366 facility buildings keep 4 or more pixels. For those 39 buildings: 5 are green, 1 is bright and 33 are ordinary. The other 327 buildings (65% of the roof area) are `too_small`. These counts measure only the large roofs. They are not a census of public roofs.

## Main result (shrink 5 m, NDVI >= 0.30, albedo top 10%, cut 0.325)

Unique buildings, facility point inside the municipality. A building shared by a school and a municipal service is counted in both groups, but only once in `all_facilities`. Areas are polygon footprints in EPSG:2100.

| group | buildings | roof m2 | green n | bright n | ordinary n | too_small n | green m2 | bright m2 | ordinary m2 | too_small m2 |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| schools | 249 | 189,017 | 5 | 0 | 27 | 217 | 6,719 | 0 | 56,483 | 125,815 |
| municipal_other | 121 | 58,867 | 0 | 1 | 7 | 113 | 0 | 6,764 | 17,352 | 34,751 |
| all_facilities | 366 | 243,804 | 5 | 1 | 33 | 327 | 6,719 | 6,764 | 72,061 | 158,260 |

Per layer: school 249 (5 / 0 / 27 / 217), nursery 68 (0 / 1 / 2 / 65), friendship_club 24 (0 / 0 / 0 / 24), clinic 7 (0 / 0 / 1 / 6), admin_building 9 (0 / 0 / 1 / 8), municipal_service 14 (0 / 0 / 3 / 11). Order is green / bright / ordinary / too_small.

The 5 green school buildings are listed with their schools. All of them have only 4 or 5 pixels, which is at the minimum. They are: bldg 61452 (60ο Δημοτικό and 130ο Νηπιαγωγείο, NDVI 0.77), bldg 19110 (2ο Πειραματικό Λύκειο, 2ο ΓΕΛ ΕΣΠ and 2ο Γυμνάσιο ΕΣΠ, 0.38), bldg 295 (43ο ΓΕΛ and 43ο Γυμνάσιο, 0.38), bldg 80 (6ο Γυμνάσιο and 3ο ΓΕΛ ΕΣΠ, 0.35) and bldg 198 (90ο and 123ο Δημοτικό, 0.33). The single bright building is bldg 4414, 6,764 m2, matched to nursery «5Δ.Κ. ΑΜΑΣΙΟΥ Α΄» (31 pixels, albedo 0.349). A footprint of that size is probably a larger complex and not only the nursery. Check it before quoting.

Seventeen facility points did not match any building (see `capacity/`), and they are not in the CSV. One of them is the 173ο Δημοτικό.

## Sensitivity

**Thresholds** (all facilities, the 39 measurable buildings; each cell is green / bright / ordinary):

| NDVI >= | albedo top 5% (cut 0.369) | top 10% (cut 0.325) | top 20% (cut 0.265) |
|--:|:--|:--|:--|
| 0.25 | 9 / 0 / 30 | 9 / 1 / 29 | 9 / 4 / 26 |
| 0.30 | 5 / 0 / 34 | 5 / 1 / 33 | 5 / 4 / 30 |
| 0.35 | 3 / 0 / 36 | 3 / 1 / 35 | 3 / 4 / 32 |

**Shrink distance** (not part of the method; shown only to make the mixing effect visible). With NDVI >= 0.30, top 10%, and the cut recomputed each time:
- 5 m (method): 39 measurable; 5 green, 1 bright.
- 2.5 m: cut 0.284, 2,237 reference roofs; 122 measurable; 20 green (21,754 m2), 5 bright.
- 0 m: cut 0.250, 8,606 reference roofs; 203 measurable; 35 green (28,304 m2), 13 bright.

The green count grows fast when the shrink is smaller. This is what edge mixing with courtyard trees looks like. Treat the green counts at 2.5 m and 0 m as upper bounds, not as measurements.

**SCL mask check.** The cloud and snow mask could remove white roofs. We recomputed everything without the mask, and all 366 buildings keep the same status. The cut changes from 0.325 to 0.323.

## Validation: Climate Action Plan 2022 (13 school complexes with green roofs)

Source: CAP 2022 p. 52 (text extract at `<scratchpad>/energy_b/cap2022.txt`, lines 3070-3108; not in the repo). It lists 13 school complexes and gives 6,475 m2 in total. In 2022 the text says these roofs «τώρα αποκαθιστούνται και επαναφυτεύονται», so we do not know their state in 2025. We matched each complex to points in `raw/gis/layers/schools.geojson` by street address. The details are in `roofs/work/validation_cap2022.csv` and in `04_summary.py`.

- **Measurable: only 3 of the 13 complexes.** For 9 complexes, every building within 30 m of the school points is `too_small`. The 173ο has no matched building.
- **All 3 measurable complexes are flagged green:**
  - 90ο/123ο Δημοτικό, Αμφικράτους: NDVI 0.33.
  - 30ο Νηπ./60ο Δημοτικό, Αίμονος & Τηλεφάνους: NDVI 0.77. A value this high is more like tree canopy than an extensive green roof. We cannot tell the two apart at 10 m.
  - 2ο Πειραματικό, Π. Κυριακού 12: NDVI 0.38. The Γυμνάσιο's own building at Φιλήμονος 36 & Τσόχα is ordinary (0.29).
- **Control:** of the 28 measurable matched buildings of the other schools, 2 are green (7%). Within 30 m, other school points have a green building in 5 of 91 cases.
- **Verdict:** 3 hits, 0 misses and 10 not measurable. The sample is too small to call this a validation of the method. It is consistent with the method working on large roofs.
- **Address mismatches:** for the 49ο Λύκειο, the layer gives Κήπων & Αχαρνών and not Αχαρνών 411-415. For the 134ο, the layer gives Ερυθραίας 14-18 and not Τσαλδάρη 11. Both were matched by name.

## Data and method

- **Buildings:** City solar map `cityg_c40solarmap`, read from `raw/treecover/dl/cityg_c40solarmap.json.gz` (66,661 features). It matches `bldg_idx` exactly: the area difference is 0.000000 m2 on all 516 matched rows (`roofs/work/buildings_check.txt`). We did not re-download it, because the City GeoServer did not answer (see below).
- **Scenes:** 20 Sentinel-2 L2A scenes, tile 34SGH, eo:cloud_cover < 5, baseline 05.11, all with valid AOI share >= 0.88 (`roofs/work/scenes_used.json`). Dates: 2025-06-03, 06-08, 06-13, 06-18, 06-23, 06-25, 07-03, 07-05, 07-08, 07-13, 07-15, 07-18, 07-23, 07-25, 07-28, 08-04, 08-07, 08-12, 08-17, 08-22.
- **Reflectance:** DN x scale + offset, taken from STAC `raster:bands` (1e-4 and -0.1), clipped at 0. SCL classes 0, 1, 3, 6, 7, 8, 9, 10 and 11 are masked. We take the per-pixel median. B11 and B12 are bilinearly resampled to 10 m.
- **Roof pixels:** EPSG:32634, polygon buffered by -5 m, pixel centre inside, at least 4 pixels required. The roof value is the median of its pixels.
- **NDVI:** (B08 - B04) / (B08 + B04). A roof is green if NDVI >= 0.30.
- **Albedo:** 0.2266 B2 + 0.1236 B3 + 0.1573 B4 + 0.3417 B8 + 0.1170 B11 + 0.0338 B12 (Bonafoni & Sekertekin 2020, IEEE GRSL 17(9):1618-1622, doi:10.1109/LGRS.2020.2967085).
  - We did not read the coefficients in the paper itself: the publisher pages returned 403. We read them in a citation, Table 4.3 "wB" of the Lund University thesis https://lup.lub.lu.se/student-papers/record/9142313/file/9142314.pdf, which gives no constant term. A web search summary of other citing papers gives the same six values.
- **Bright:** albedo >= 90th percentile of all solar-map roofs in the municipality with >= 4 pixels. That is 761 roofs, with median albedo 0.183, and the cut is **0.325**. The reference set is itself only large roofs, because small roofs are too_small.

## Limits

- **10 m pixels.** With a 5 m shrink a compact roof needs roughly 30 x 30 m of footprint (a shrunk core of about 20 x 20 m) to be measured. The median solar-map polygon is 164 m2. Most public roofs are therefore `too_small`, including 10 of the 13 known green-roof schools.
- **Mixing.** Even inside the shrunk polygon, a 10 m pixel mixes the roof with parapets, stair towers, HVAC units, water tanks, skylights and overhanging trees. A green result can be trees from the courtyard (see the shrink sensitivity). A bright result can be a light courtyard or a light-coloured pavement next to the building.
- **PV panels** are dark, so a roof covered with PV reads as `ordinary`, not as "already used".
- **Pitched roofs** (tiles) have a different reflectance and a non-nadir geometry. The solar map has no flat/pitched flag.
- **Dates.** The solar-map date is unknown, so buildings may have changed. The CAP 2022 list describes roofs that were being replanted in 2022, and their 2025 state is unknown.
- **Summer NDVI.** Extensive green roofs (sedum, dry meadow) can be brown in an Athens summer. A real green roof can then read below 0.30, which is a miss we cannot detect.
- **Matching.** There is one building per facility point (`capacity/README.md`). A school is often several buildings, and the matched one may not be the roof that was greened.
- **Relative cut.** "Bright" is relative to Athens roofs in summer 2025. It is not a certified cool-roof reflectance.

## What did not work

- **City GeoServer.** `http://gis.cityofathens.gr/geoserver/ows` (WFS GetFeature for `geonode:cityg_c40solarmap`, and GetCapabilities) accepted the connection but sent no bytes within 30-100 s, three times. HTTPS was refused. CKAN lists the dataset as «Απόδοση Ηλιακής Ενέργειας ανά κτίριο - "Solar Map"» (layer `geonode:c40solarmap`, ZIP `http://gis.cityofathens.gr/download/144`, not tried). We used the copy already in `raw/`.
- **Primary paper.** The publisher and university pages (unipg, MDPI) returned 403, so we could not read the paper itself.
