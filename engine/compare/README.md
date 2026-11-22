# Actual plantings vs the same number of trees in order of need

One comparison for the Mayor: the trees the City actually planted, against the same number of trees placed in order of need. Python standard library only, no network, deterministic. `python3 -I engine/compare/build_compare.py` writes `actual_vs_need.json`, `actual_vs_need.csv`, `SUMMARY.md`; `python3 -I engine/compare/test_compare.py` checks them.

## What is real and what is a scenario

- ACTUAL side: real. Every tree is a row of the City's planting register (`athenstrees/plantings_points.csv`), put into a neighbourhood by point in polygon on `neighbourhoods.geojson` (own ray casting; Polygon and MultiPolygon, holes respected; first match wins, and the build counts points matching more than one polygon: 0).
- NEED side: a SCENARIO, not a plan. It takes the team's own calculation (`engine/packages.csv`, intervention `trees_pavement`) and walks the packages in order of `rank_within_intervention`. Each neighbourhood gets its package's central quantity until N is used; the last one gets the remainder, and its cost is pro-rated. The packages carry the flag `capacity_unverified`: no tree-pit register exists, so nobody knows whether this many trees fit there. The figures say where the need is, not where trees can be planted.
- The composite priority score behind the ranking is PROVISIONAL: a separate audit of the formula is running. `need_least_cover_first` repeats the walk with the same packages ordered by `ua_stl2018_pct` ascending (ties by name), so the message does not depend on the composite formula.

## Scenarios

`2024`, `2025`, `2026` (to the last register date) and `all`. N = trees actually assigned to a neighbourhood in that period, so both sides always sum to the same N. The 4 trees dated 2001 are left out of the yearly scenarios and kept in `all`. Trees outside every neighbourhood polygon (23 in the register, so N is smaller than the register total) are not in N.

## Indicators (identical for every side)

| Key | Definition |
|---|---|
| n_trees | sum of num_trees (a location can have several rows, one per species) |
| share_bare_pct | trees in the 62 neighbourhoods with `ua_stl2018_pct` < 2 / N x 100 |
| per1000_bare, per1000_rest | trees per 1,000 residents (`pop_total`) in the bare group / in the other 82 |
| ratio_bare_to_rest | per1000_bare / per1000_rest (null when the rest gets 0) |
| neighbourhoods_receiving | neighbourhoods with at least 1 tree |
| residents_receiving, residents_65plus_receiving, residents_0_14_receiving | `pop_total`, `pop_65plus`, `pop_0_14` summed over those neighbourhoods |
| top10_share_pct | share of N in the 10 neighbourhoods with most trees (ties by name) |
| lorenz_least_treed_half_share_pct | neighbourhoods ordered by `ua_stl2018_pct` ascending (ties by name), population cumulated to 50%, the one crossing 50% counted pro rata; share of N they receive |
| mean_cover_pct | tree-weighted mean of `ua_stl2018_pct`: the average new tree went to a neighbourhood with this cover |
| schools_low_canopy_reached | ACTUAL only. Schools in `streets/sites_with_plantings.csv` with `canopy_pct_150m` < 5 that have at least one planted tree (non-2001) within 150 m, recomputed from the points by haversine distance. Cross-check: the count for `all` equals the count from the file's own `new_trees_150m_since_2024` > 0 (both in `meta.reproduction_check`). Null on the need side, which has no point locations |
| cost_central_eur (need sides) | sum of `cost_central_eur` of packages.csv, pro-rated for the last package; also `packages_used`, `last_package_fraction` |

`actual_without_groves_2216_2218` repeats the actual indicators with planting ids 2216 and 2218 removed (the two large grove records of the duplicates check).

## Reproduction check

`meta.reproduction_check` holds the recomputed published figures (14,232 inside, 17.0% to the bare group, 22.8 / 9.4 / 19.1 by year, 18.6% without 2216 and 2218). `test_compare.py` asserts them within 0.1 point.

## Known limits of the need side

- Only neighbourhoods with a `trees_pavement` package (canopy deficit > 0 against a 10% target; 124 of 144) can receive trees. Each package is capped by the +1 percentage point canopy step. All 62 bare neighbourhoods have a package, but together they hold only a limited number of trees (see `meta` and SUMMARY), so for large N the share of the bare group is capped by that, not by the ranking.
- Tree cover is the 2018 Street Tree Layer; it does not see trees planted since.
- Population per single neighbourhood is uncertain by about 25-30%; totals are reliable.
- The register counts trees, not size or survival. Whether the two large entries (2216, 2218) are real plantings is unverified.

`caveats` in the json lists the codes. Greek sentences in SUMMARY.md are built only from computed numbers.
