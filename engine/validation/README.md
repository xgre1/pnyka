# Validation of the priority ranking (trees and roofs tabs)

This folder audits whether `rank_within_intervention` in `engine/packages.csv` rests on data or on arbitrary choices. It covers `trees_pavement` («Δρόμοι») and `roof_cool_or_green_municipal` («Κτίρια»). Nothing outside this folder was changed. The engine, `params.csv`, `rules.csv` and `packages.*` are only read.

Run: `python3 -I engine/validation/validation.py` (standard library only, no network, about 30 s). Fixed seeds: weights 20261121, population 20261122, permutations 20261123, moderate weights 20261124. Two runs give identical output.

The plain-language conclusions are in `VERDICT.md`. Every number is in `results.json`.

## Files

| File | What |
|---|---|
| `validation.py` | All the analyses. It reimplements the engine score and stops if the reproduction fails. |
| `results.json` | Every number, per intervention: `reproduction`, `construct`, `sensitivity`, `external`, `alternatives`, `proposed_variants`, `baseline_top30`. Also `validators_spearman`, which shows how the validation variables relate to each other. |
| `sensitivity_summary.csv` | One row per perturbation: overlap of the top 10, 20 and 30 (mean, p5, p95), Spearman against the baseline, the share of the baseline 1M EUR selection that is kept, and the size of the robust core. |
| `robust_core_trees.csv`, `robust_core_roofs.csv` | Per neighbourhood: baseline rank and score, the share of random-weight runs and of population runs in which it is in the top 20, and whether it is in the core (at least 90%). |
| `external_validation.csv` | Each ranking against variables that are not in it. Columns: mean of the top 20, mean of the bottom 20, mean of all packages, mean and p5/p95 of random picks of 20 (or 30), and a one-sided permutation p-value. |
| `alternatives.csv` | The naive rules (`kind=naive`) and the proposed fixes (`kind=proposed`) side by side: overlap with the current ranking, the external checks, and the 1M EUR selection. |

## The checks

0. **Reproduction.** The script reimplements the engine formula: percentiles with mid-ranks, computed among the neighbourhoods that have the value, over all 144. Need is the mean of the available need percentiles, people is the percentile among the packages, score = (need + people) / 2. Ranks use the score rounded to 4 decimals, with ties broken by name. The result is compared with `packages.csv`. Trees: 124/124 packages, max |Δ priority_score| = 0.0000499, 0 rank mismatches. Roofs: 115/115, max |Δ| = 0.0000500, 0 mismatches. The csv stores 4 decimals, so a difference of 0.00005 or less is exact.
1. **Construct audit** (`construct`). Covers:
   - Spearman correlations between the need percentiles, over the packages of the tab.
   - Missing values per indicator.
   - Scores grouped by how many indicators were available, and whether neighbourhoods without a sensor are over-represented in the top 20 (permutation test).
   - The effect of adding `night_temp_c`.
   - Area effects: deficit against area, residents against area, and the score against area. Also a variant with the deficit per area.
   - The share of score variance carried by each term (cov(term, score) / var(score); the shares sum to 1).
   - Ties.
   - Roofs only (`roof_logic`): each indicator against LST, buildings and roof m2, and alternative roof rankings built from heat and buildings.
2. **Sensitivity** (`sensitivity`):
   - (a) 2,000 random weightings. Need-indicator weights follow Dirichlet(1,..,1) and (w_need, w_people) follows Dirichlet(1,1). The runs are also split into (a1) need weights only and (a2) need vs people only. As a supplement, (a3) draws every weight log-uniform between ½ and 2.
   - (b) Leave one indicator out, and for trees also drop the people part.
   - (c) Min-max and z-scores instead of percentiles.
   - (d) Population ×U(0.7, 1.3), independent per neighbourhood, 2,000 runs. Applied to pop_total, pop_0_14, pop_65plus and density, so new trees per 1000 scales by 1/f.
   - (e) The 1,000,000 EUR budget: packages are taken in rank order, at central cost, indivisible, and skipped if they do not fit (the engine's rule). The script reports the share of the baseline selection kept under (a) and (d).
3. **External validation** (`external`). The ranking is checked against data it does not use:
   - Satellite summer daytime LST (`city_lst_summer_day_2016_2020_c`, all 144).
   - `wc2021_tree_pct`, an independent canopy product. `metachm_ge3m_pct` is also shown, but it is **not** independent for trees: `canopy_deficit_m2` is computed from the Meta CHM, and the per-area deficit has Spearman −1.00 with it.
   - Night temperature, **only out of sample**: the score is recomputed without `night_temp_c` and compared with `heat_night` across the 67 (trees) or 66 (roofs) packages that have a sensor. The in-sample version would be circular and is not used.
   - Trees: the share of municipal residents, of residents 65+ and of low-canopy schools in the top 20 and top 30, against 10,000 random picks.
   - Roofs: matched municipal buildings, roof m2, and schools + nurseries + clubs in the top 20.
4. **Naive alternatives** (`alternatives`): tree cover alone, density alone, low-canopy sites count alone, plus LST alone, residents alone (trees) and buildings alone (roofs). Each gets the same external checks.
5. **Proposed fixes** (`proposed_variants`). Each is computed here and the engine is not changed. Each reports its overlap with the current top 20, the same external checks, and its own robustness: 2,000 random weightings and, for trees, 2,000 population runs. "Balanced" means the need score is turned back into a percentile among the packages before it is averaged with the people percentile. That way need and people have the same spread.

## Limits of this audit

- LST is a 2016-2020 summer *daytime surface* temperature. Across the 144 neighbourhoods it has almost no relation to tree cover (Spearman −0.09) and only a weak one to night air temperature at the sensors (0.24, n=77). So it is a weak yardstick for the tree ranking.
- Night temperature comes from one sensor per neighbourhood, at an unknown placement.
- `wc2021_tree_pct` is independent, but it is highly correlated with the tree cover the score uses (0.93).
- Population is a modelled estimate (±25-30%).
- No occupant counts exist for municipal buildings.
- A permutation p-value tests "better than a random pick". It does not test "best possible".
