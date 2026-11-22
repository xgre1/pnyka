# Capacity summary - Municipality of Athens

All areas in m2 (EPSG:2100), lengths in m. Quantities are MEASURED footprints/lengths/areas from City and open layers; they are NOT usable/installable capacity. See README.md for method and caveats. Computed 2026-11-21 by `scripts/01_compute_capacity.py`.

## Municipality totals

| Quantity | Value | Unit |
|---|---|---|
| Area | 37.96 | km2 |
| Neighbourhoods | 144 | n |
| Population (pop_total) | 646,086 | persons |
| Buildings (solar-map polygons, rep. point inside) | 65,108 | n |
| Roof footprint (geometry, clipped) | 14,422,116 | m2 |
| Roof share of area | 38.0 | % |
| Solar-usable roof area (City model USAB_AREA) | 9,142,415 | m2 |
| Solar-usable share of roof footprint | 63.4 | % |
| School roof (matched buildings, lower bound) | 189,018 | m2 |
| Municipal non-school facility roof (matched, lower bound) | 58,867 | m2 |
| Street length (OSM named streets) | 926.1 | km |
|  of which pedestrian + living_street | 69.6 | km |
| Street surface ESTIMATE (carriageway+pavement) | 8,095,817 (range 5,667,072 to 10,524,562) | m2 |
| Green/open union net of roofs (zoning + UA2012 green/sport/natural) | 6,715,742 | m2 |
|  zoned green (City zoning, union) | 5,442,754 | m2 |
|  UA2012 green urban areas | 4,917,355 | m2 |
|  UA2012 sports & leisure | 448,658 | m2 |
| Residual (not roof, not green, not est. street) - raw | 8,722,599 | m2 |
| Residual floored at 0 per neighbourhood, summed | 8,761,218 | m2 |
| Canopy, Meta CHM >=3 m | 3,636,724 / 9.6 | m2 / % |
| Tree canopy, Street Tree Layer 2018 | 3,626,340 / 9.6 | m2 / % |
| Canopy deficit to 5% (sum of per-neighbourhood floors) | 410,904 | m2 |
| Canopy deficit to 10% (sum of per-neighbourhood floors) | 1,693,147 | m2 |
| Canopy deficit to 15% (sum of per-neighbourhood floors) | 3,243,038 | m2 |
| Canopy deficit to 30% (sum of per-neighbourhood floors) | 8,186,012 | m2 |
| Illustrative trees for 10% target, crown 4/6/8 m | 134,800 / 59,950 / 33,747 | trees |
| Illustrative trees for 30% target, crown 4/6/8 m | 651,488 / 289,593 / 162,926 | trees |
| Trees planted since 2024 (num_trees; rows) | 14,228 (12,419 rows) | trees |
| Schools: total / with canopy_pct_150m < 5 | 397 / 249 | n |
| Nurseries: total / with canopy_pct_150m < 5 | 72 / 42 | n |
| Playgrounds: total / with canopy_pct_150m < 5 | 89 / 44 | n |
| Elderly clubs (Λέσχες Φιλίας): total / with canopy_pct_150m < 5 | 25 / 17 | n |

Canopy deficit netted at municipality level (area x target - existing, one number) for contrast: 5% = 0, 10% = 158,904, 15% = 2,056,717, 30% = 7,750,159 m2. The per-neighbourhood sums above are larger because a neighbourhood already above target does not offset another.

Facility matching (points to solar-map building polygons; contained, else nearest within 30 m):

| Group | Points (in municipality) | Contained | Nearest <=30 m | Unmatched | Unique buildings | Roof m2 (matched, lower bound) | Roof m2 (all buildings within 30 m, upper bound) |
|---|---|---|---|---|---|---|---|
| Schools | 397 | 330 | 57 | 10 | 249 | 189,018 | 584,722 |
| Municipal non-school (nurseries, clubs, clinics, admin, services) | 130 | 59 | 66 | 5 | 121 | 58,867 | 299,167 |

Match rate (contained or within 30 m): schools 97.5% (contained only 83.1%), municipal non-school 96.2% (contained only 45.4%). Ambiguity: 359 of 397 school points and 120 of 130 municipal points have more than one building within 30 m; 138 school points share a building with another school point (co-located schools), so unique buildings < points. A school is usually several buildings, so matched area is a lower bound and the within-30 m area an upper bound (it includes neighbours). The City has no full municipal-building register on disk or on the WFS; "municipal non-school" is built from facility point layers only.

## Group: neighbourhoods with Street Tree Layer 2018 cover <2% (62 neighbourhoods)

| Quantity | Value | Unit |
|---|---|---|
| Area | 12.65 | km2 |
| Neighbourhoods | 62 | n |
| Population (pop_total) | 290,235 | persons |
| Buildings (solar-map polygons, rep. point inside) | 30,046 | n |
| Roof footprint (geometry, clipped) | 6,382,877 | m2 |
| Roof share of area | 50.5 | % |
| Solar-usable roof area (City model USAB_AREA) | 3,964,935 | m2 |
| Solar-usable share of roof footprint | 62.1 | % |
| School roof (matched buildings, lower bound) | 61,174 | m2 |
| Municipal non-school facility roof (matched, lower bound) | 24,192 | m2 |
| Street length (OSM named streets) | 395.8 | km |
|  of which pedestrian + living_street | 25.1 | km |
| Street surface ESTIMATE (carriageway+pavement) | 3,402,995 (range 2,382,096 to 4,423,893) | m2 |
| Green/open union net of roofs (zoning + UA2012 green/sport/natural) | 283,449 | m2 |
|  zoned green (City zoning, union) | 172,892 | m2 |
|  UA2012 green urban areas | 173,440 | m2 |
|  UA2012 sports & leisure | 50,043 | m2 |
| Residual (not roof, not green, not est. street) - raw | 2,579,583 | m2 |
| Residual floored at 0 per neighbourhood, summed | 2,579,583 | m2 |
| Canopy, Meta CHM >=3 m | 316,699 / 2.5 | m2 / % |
| Tree canopy, Street Tree Layer 2018 | 105,319 / 0.8 | m2 / % |
| Canopy deficit to 5% (sum of per-neighbourhood floors) | 320,554 | m2 |
| Canopy deficit to 10% (sum of per-neighbourhood floors) | 948,191 | m2 |
| Canopy deficit to 15% (sum of per-neighbourhood floors) | 1,580,636 | m2 |
| Canopy deficit to 30% (sum of per-neighbourhood floors) | 3,477,972 | m2 |
| Illustrative trees for 10% target, crown 4/6/8 m | 75,488 / 33,570 / 18,895 | trees |
| Illustrative trees for 30% target, crown 4/6/8 m | 276,798 / 123,040 / 69,225 | trees |
| Trees planted since 2024 (num_trees; rows) | 2,420 (2,094 rows) | trees |
| Schools: total / with canopy_pct_150m < 5 | 164 / 150 | n |
| Nurseries: total / with canopy_pct_150m < 5 | 26 / 23 | n |
| Playgrounds: total / with canopy_pct_150m < 5 | 24 / 19 | n |
| Elderly clubs (Λέσχες Φιλίας): total / with canopy_pct_150m < 5 | 12 / 11 | n |

## Top 15 neighbourhoods by roof footprint (m2)

| name | community | area_km2 | roof_area_m2 | roof_share_of_area_pct | schools_roof_area_m2 |
|---|---|---|---|---|---|
| ΕΛΑΙΩΝΑΣ | 3η ΔΚ | 2.27 | 568,087 | 25.02 | 843 |
| ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ | 1η ΔΚ | 0.53 | 312,882 | 59.03 | 0.00 |
| ΚΟΛΩΝΑΚΙ | 1η ΔΚ | 0.50 | 267,377 | 53.82 | 560 |
| ΜΟΝΑΣΤΗΡΑΚΙ-ΠΛΑΚΑ | 1η ΔΚ | 0.59 | 251,733 | 42.70 | 978 |
| ΝΕΑΠΟΛΗ I | 1η ΔΚ | 0.47 | 242,326 | 52.06 | 2,130 |
| ΚΑΤΩ ΠΑΤΗΣΙΑ II | 4η ΔΚ | 0.48 | 235,382 | 48.75 | 3,376 |
| ΑΚΑΔΗΜΙΑ ΠΛΑΤΩΝΟΣ | 4η ΔΚ | 0.75 | 219,863 | 29.49 | 2,376 |
| ΑΓ.ΚΩΝ/ΝΟΣ-ΠΛ.ΒΑΘΗΣ | 1η ΔΚ | 0.41 | 205,935 | 50.72 | 0.00 |
| ΙΛΙΣΙΑ-ΠΑΡΚΟ | 1η ΔΚ | 0.82 | 198,653 | 24.26 | 426 |
| ΚΟΛΟΚΥΝΘΟΥ | 4η ΔΚ | 0.49 | 195,975 | 39.87 | 5,143 |
| ΑΓΙΟΣ ΚΩΝΣΤΑΝΤΙΝΟΣ | 4η ΔΚ | 0.35 | 173,515 | 49.67 | 3,344 |
| ΠΡΟΦΗΤΗΣ ΔΑΝΙΗΛ | 3η ΔΚ | 0.36 | 171,439 | 47.88 | 0.00 |
| ΕΞΑΡΧΕΙΑ | 1η ΔΚ | 0.28 | 170,536 | 60.86 | 822 |
| ΜΟΥΣΕΙΟ | 1η ΔΚ | 0.34 | 170,377 | 49.59 | 500 |
| ΚΟΛΩΝΟΣ | 4η ΔΚ | 0.34 | 163,040 | 48.38 | 1,762 |

## Top 15 neighbourhoods by canopy deficit to 10% (m2, Meta CHM >=3 m)

| name | community | area_km2 | canopy_deficit_to_10pct_m2 | chm_ge3m_pct | illustr_trees_10pct_crown6m |
|---|---|---|---|---|---|
| ΕΛΑΙΩΝΑΣ | 3η ΔΚ | 2.27 | 54,797 | 7.59 | 1939 |
| ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ | 1η ΔΚ | 0.53 | 44,484 | 1.61 | 1574 |
| ΑΓ.ΚΩΝ/ΝΟΣ-ΠΛ.ΒΑΘΗΣ | 1η ΔΚ | 0.41 | 34,152 | 1.59 | 1208 |
| ΚΑΤΩ ΠΑΤΗΣΙΑ II | 4η ΔΚ | 0.48 | 34,042 | 2.95 | 1205 |
| ΚΟΛΟΚΥΝΘΟΥ | 4η ΔΚ | 0.49 | 32,294 | 3.43 | 1143 |
| ΠΡΟΦΗΤΗΣ ΔΑΝΙΗΛ | 3η ΔΚ | 0.36 | 27,855 | 2.22 | 986 |
| ΚΟΛΩΝΟΣ | 4η ΔΚ | 0.34 | 25,787 | 2.35 | 913 |
| ΑΓΙΑΣ ΖΩΝΗΣ | 6η ΔΚ | 0.29 | 23,276 | 1.89 | 824 |
| ΚΟΛΩΝΑΚΙ | 1η ΔΚ | 0.50 | 23,245 | 5.32 | 823 |
| ΑΓΙΟΣ ΓΕΩΡΓΙΟΣ | 4η ΔΚ | 0.29 | 23,019 | 2.19 | 815 |
| ΘΥΜΑΡΑΚΙΑ | 4η ΔΚ | 0.30 | 21,388 | 2.78 | 757 |
| ΓΚΑΖΟΧΩΡΙ | 3η ΔΚ | 0.28 | 21,155 | 2.39 | 749 |
| ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ | 4η ΔΚ | 0.26 | 21,072 | 2.01 | 746 |
| ΠΟΛΥΓΩΝΟ Ι | 7η ΔΚ | 0.28 | 20,969 | 2.62 | 742 |
| ΚΑΜΠΑ | 3η ΔΚ | 0.41 | 20,111 | 5.06 | 712 |

(illustr_trees_10pct_crown6m = illustrative arithmetic: deficit / crown area of a 6 m crown, not a planting plan.)

## Validation

- Sum of neighbourhood areas: 37.956 km2 from geometry (37.963 km2 from the `area_km2` attribute); overlap between polygons -1.5e-14 km2. Target ~38.0: OK.
- Roof footprint 14,422,116 m2 = 38.0% of the municipality area (maximum neighbourhood 61.0%; 0 neighbourhoods >100%). Reported as computed. Streets are separately ~21% (estimate) and green/open net of roofs ~18%.
- Solar-map polygon area: geometry sum 14,758,214 m2 vs layer attribute `Area` 14,758,214 m2 (median ratio 1.000000): the attribute is just the planimetric footprint.
- Building count: layer has 66,661 features; 65,126 intersect the municipality, 65,108 have their representative point inside (= sum of buildings_n 65,108); 1,553 lie outside the municipal polygons. The 18 straddling buildings are the difference. Roof area by clipped geometry vs whole-building assignment differs by 519 m2 in total.
- Overlapping solar-map polygons: sum minus union = 13,845 m2 (0.09% of area) - negligible double counting.
- Canopy: recomputed CHM % and STL % differ from `treecover/treecover_by_neighbourhood.csv` by at most 0.0005 and 0.0005 percentage points (rounding). Low-tree group size 62 (expected 62).
- Community assignment: municipal_district_id agrees with the City community polygon layer for 143/144 neighbourhoods (centroid test; the one difference is a boundary case).
- Sites: 583 sites, all inside; csv neighbourhood field vs point-in-polygon mismatches: 0. Plantings: 12,442 rows / 14,251 trees dated 2024-01-01 or later (file spans 2001-03-02 to 2026-11-19); 23 rows fall outside the neighbourhood polygons and are not counted per neighbourhood.
- Street residual: 4 neighbourhoods have a negative raw residual (roof + green + street estimate > area), i.e. the street-width defaults overshoot there; they are floored at 0 in `residual_open_m2` and flagged.
- Urban Atlas road cross-check NOT possible for 2012: the downloaded UA2012 has no road class (the 133 km2 "Other roads" polygon failed to download) and covers only 83% of the municipality. UA2010 (City-hosted, covers 100%) has 10 road polygons totalling 6,456,371 m2 = 17% of the area, versus 21% (8,095,817 m2) from the OSM width estimate. The UA2010 figure lies inside the estimate's +-30% band (5,667,072 to 10,524,562 m2), which is mild support for the estimate's order of magnitude only: different definition (UA 'other roads and associated land' polygons with a 0.25 ha minimum unit, includes verges/interchanges), different year (2010), and not available per neighbourhood in a comparable form.
- OSM: 20,983 named ways, 2,761 km in the extract of which 1,835 km lie outside the municipality (metropolitan extract); 926 km inside. Width tag on 5.4% and lanes tag on 36.7% of length.

### Spot checks

- **ΕΛΑΙΩΝΑΣ** (3η ΔΚ): area_km2=2.3; buildings_n=832; roof_area_m2=568087.1; roof_share_of_area_pct=25.0; roof_solar_usable_m2=453604.3; schools_roof_area_m2=842.8; street_len_total_m=16116.6; street_area_est_m2=160199.4; green_open_union_net_of_roofs_m2=507523.6; residual_unclassified_raw_m2=1034497.9; canopy_chm_ge3m_m2=172233.9; chm_ge3m_pct=7.6; stl2018_pct=8.1; canopy_deficit_to_10pct_m2=54796.9; illustr_trees_10pct_crown6m=1939; sites_all4_n=4; sites_all4_canopy150m_lt5pct_n=1
- **ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ** (1η ΔΚ): area_km2=0.5; buildings_n=988; roof_area_m2=312882.3; roof_share_of_area_pct=59.0; roof_solar_usable_m2=213490.7; schools_roof_area_m2=0.0; street_len_total_m=13062.5; street_area_est_m2=106884.3; green_open_union_net_of_roofs_m2=16494.6; residual_unclassified_raw_m2=93786.6; canopy_chm_ge3m_m2=8521.0; chm_ge3m_pct=1.6; stl2018_pct=0.9; canopy_deficit_to_10pct_m2=44483.8; illustr_trees_10pct_crown6m=1574; sites_all4_n=0; sites_all4_canopy150m_lt5pct_n=0
- **ΑΓΙΟΣ ΑΡΤΕΜΗΣ** (2η ΔΚ): area_km2=0.2; buildings_n=645; roof_area_m2=112580.2; roof_share_of_area_pct=49.5; roof_solar_usable_m2=65815.5; schools_roof_area_m2=1499.0; street_len_total_m=7855.7; street_area_est_m2=65442.5; green_open_union_net_of_roofs_m2=1888.1; residual_unclassified_raw_m2=47616.4; canopy_chm_ge3m_m2=3888.5; chm_ge3m_pct=1.7; stl2018_pct=2.5; canopy_deficit_to_10pct_m2=18864.2; illustr_trees_10pct_crown6m=668; sites_all4_n=6; sites_all4_canopy150m_lt5pct_n=2
