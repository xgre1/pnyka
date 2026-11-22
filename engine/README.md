# Reference calculation: intervention packages generated from data

A proposal for the team, not a decision. Python standard library only; no network, no LLM, no UI. The packages are not written by hand: for every one of the 144 neighbourhoods the script finds where a gap exists and proposes interventions. Every quantity comes from a dataset in this repo, every coefficient from `params.csv` (with a source and a status), and where a number does not exist the output field is EMPTY and the gap is named.

## Files

| File | What |
|---|---|
| `params.csv` | Every coefficient. Columns: intervention_id, parameter, unit, low, central, high, source_file, source_ref, status, note. Status is one of measured_athens, published_elsewhere, city_contract, assumption, missing. |
| `rules.csv` | The rules as data: eligibility, quantity function, people basis, need indicators, cost parameters, evidence, data gaps. |
| `need_defs.csv` | The need indicators: source, field, direction (lower or higher = more need), note. |
| `generate_packages.py` | The calculation. `python3 engine/generate_packages.py` writes everything below; `--budget N` prints what N euro buys in EACH tab (trees, roofs) and writes it to `budget_<N>.md`; `--rank-by people_per_eur` is a non-default comparison, see Budget mode. |
| `test_engine.py` | Plain-assert tests. `python3 engine/test_engine.py` |
| `packages.csv`, `packages_top20.md`, `need_indicators.csv`, `budget_250k.md`, `budget_1m.md`, `budget_5m.md`, `packages.json` | Outputs (regenerated every run). `budget_1m_by_need.md` (one need list across interventions) is no longer written: it contradicted the per-tab budget of decision 1528. |
| `validation/` | The audit of the ranking (`VERDICT.md`, `validation.py`, `results.json`). It audited the ranking BEFORE the change described in Priority score; `validation.py` reproduces that old engine and stops if the engine no longer matches it, so it is a record, not a check to rerun. `test_engine.py` imports its functions to check that the new trees and roofs scores equal its variants. |
| `labels_el.csv` | Greek labels for every code used in `packages.json`. Hand-written input, not generated. Columns: code, kind, label_el, long_el. |
| `OPEN_QUESTIONS.md` | Judgement calls for humans. |

If `research/cost/roofs_pavements/defaults.csv` exists at run time and has columns `intervention_id` and `parameter` (plus any of the params.csv columns), its rows fill parameters that are `missing` in params.csv or add new ones (status `assumption` unless the file says otherwise). A row for a parameter that already has a value is ignored and reported on stderr. Any `assumption` row added this way must also be listed in this README (the test checks). The file that exists today has its own layout (`parameter`, `applies_to`, `source`, ...; no `intervention_id`), so the engine does not read it; stderr says so. Its row `cool_roof_cost_installed` (13.5 / 20 / 25 EUR/m2) was copied BY HAND into `params.csv` as `roof_cool_or_green_municipal.roof_cost_per_m2_eur` (the `test_prices_match_cost_model` test checks the three values against the file). If the City changes the price, change it in `params.csv`.

## Step 1: need indicators (`need_indicators.csv`)

For every neighbourhood: raw value and percentile rank. Rank only among neighbourhoods that HAVE the value; missing stays missing (empty), never imputed. Percentile = 100 x (mid-rank position) / (n - 1), mid-rank for ties; 100 means highest need. For indicators where lower means more need the scale is reversed.

| Indicator (`need_defs.csv`) | Value | Source | More need when |
|---|---|---|---|
| tree_cover_stl2018_pct | tree cover, Street Tree Layer 2018 | `treecover/treecover_by_neighbourhood.csv` `ua_stl2018_pct` | lower |
| canopy_deficit_m2 | max(0, area x target% - canopy), target from `_global.canopy_target_pct` | `capacity/capacity_by_neighbourhood.csv` `canopy_deficit_to_10pct_m2` | higher |
| residents, residents_65plus, residents_0_14 | persons | `raw/population/population_by_neighbourhood.csv` `pop_total`, `pop_65plus`, `pop_0_14` | higher |
| pop_density_per_km2 | persons per km2 | same file | higher |
| low_canopy_sites_n | schools + nurseries + playgrounds + elderly clubs with canopy_pct_150m < 5 | capacity `sites_all4_canopy150m_lt5pct_n` (counted from `streets/sites_with_plantings.csv`) | higher |
| low_canopy_sites_share | low_canopy_sites_n / sites_all4_n (missing if no site) | capacity | higher |
| low_canopy_schools_playgrounds_n | schools + playgrounds with canopy < 5% | capacity | higher |
| new_trees_per_1000_residents | trees planted 2024-2026 / pop_total x 1000 | `athenstrees/plantings_by_neighbourhood.csv`, population file | lower |
| night_temp_c | summer night temperature, only where a sensor exists | `neighbourhoods.csv` `heat_night` | higher (used by cool surface and elderly only; no longer by trees or roofs) |
| pm25_community_est | PM2.5 estimate of the Municipal Community (row "ΔΚ n") | `research/health/burden/pm25_burden_by_group.csv` | CONTEXT ONLY: trees do not change it; never used in any score |
| surface_temp_lst_c | satellite land-SURFACE temperature (ground and roofs, not air), summer day, 2016-2020; area-weighted mean of the City of Athens GIS layer angLST_Athens_UrbanAtlas (EXTREMA / ARTi); exists for all 144 | `treecover/treecover_by_neighbourhood.csv` `city_lst_summer_day_2016_2020_c` | higher (roofs only) |

## Step 2: eligibility and quantity (`rules.csv`)

Eligibility is a list of `field op number` conditions joined with `;` (all must hold). A missing value never satisfies a condition.

| Intervention | Eligible if | Quantity (low / central / high) | Capacity figure | People concerned |
|---|---|---|---|---|
| trees_pavement | canopy_deficit_m2 > 0 | trees for +1 percentage point of canopy (`canopy_increment_pp_package`), capped at the deficit: add_m2 = min(area_m2 x pp/100, deficit_m2); trees = ceil(add_m2 / (crown_area x survival)). central uses central crown and survival; low uses the optimistic (high crown, high survival); high the pessimistic. Flag `capacity_unverified`. Options +3 pp and +5 pp shown in `quantity_options`. | trees to close the whole deficit with the same parameters | pop_total (all residents) |
| roof_cool_or_green_municipal | roof_municipal_m2 > 0 | roof_municipal_m2 = schools_roof_area_m2 + municipal_other_roof_area_m2 (matched building footprint; flat/usable share unknown). As an AREA it is an upper bound of what can be treated (not all footprint is flat or usable); as a count of BUILDINGS it is a lower bound (not every municipal building is matched) | the same figure | none: occupants unknown, field empty |
| cool_surface_schoolyard_playground | low_canopy_schools_playgrounds_n > 0 | number of schools and playgrounds with canopy_pct_150m < 5. Area per site unknown (no default exists) | schools + playgrounds in the neighbourhood | pop_0_14 (upper proxy) |
| school_street | sites_schools_n > 0 | number of schools (one scheme each; upper bound) | the same | pop_0_14 (upper proxy) |
| elderly_heat_support | pop_65plus > 0 and canopy_deficit_m2 > 0 | residents 65+ (ceiling of people who could be covered); elderly clubs reported in `quantity_note` | the same | pop_65plus |

## Step 3: cost (EMPTY when a unit price is missing)

cost_level = quantity_level x unit_cost_level. Unit prices: trees = (1 - s) x cost(existing pit) + s x cost(new small pit), s = `trees_pavement.share_new_small_pits`; both are per PLANTED tree incl. VAT and 2-3 y watering from `research/cost/cost_model.csv` (City contract ADAM 25SYMV018202225); losses are inside the tree count so they are not added again. Roof: matched footprint x `roof_cost_per_m2_eur` (13.5 / 20 / 25 EUR/m2, status ASSUMPTION: low = City of Athens price list 2012, article NAOIK 79.11.02, an elastomeric waterproofing membrane, which is not a cool coating, so a floor proxy in the 2012 price base; central and high = a Greek vendor web page quoting 15-25 EUR/m2, no method, snippet only. `research/cost/roofs_pavements/defaults.csv` itself says no public tender price for a cool-roof coating was found and the City should overwrite it with a quote; it excludes roof preparation). The cost is flagged `cost_area_upper_bound` (whole footprint, not only usable flat roof) and `price_is_assumption`; the buildings are a lower bound (`lower_bound`). Cool surface: price exists only as a central value (single source) and `yard_area_per_site_m2` is missing, so empty. School street: `cost_per_scheme_eur` (London FOI, converted). Elderly: `cost_per_person_covered_eur` missing, so empty. low/high of the cost combine the favourable or unfavourable values of all parameters: a scenario range, not a statistical interval. `recurring_cost_eur_per_year_central` (trees only) = central trees x 23.5 EUR, informational, not in the cost or the budget.

`people_per_1000_eur` = people_concerned / (cost_central / 1000), only where a cost exists.

## Priority score

Changed on 2026-11-21 for trees and roofs, exactly as the audit `engine/validation/VERDICT.md` recommended (trees: its change C, variant `TC_balanced_cover_newtrees_1000`; roofs: its "tree cover + LST", variant `R6_tree_cover_plus_lst`). The other three interventions are unchanged. `rules.csv` says per intervention which need indicators count (`need_indicators`), how they are combined (`score_method`: `mean` or `balanced`) and how ties are broken (`rank_tie_break`).

```
p_k          = percentile 0-100 of need indicator k among the 144 neighbourhoods that have it (100 = most need; Step 1)
need_score   = sum(w_k x p_k) / sum(w_k)        over the need indicators k of the intervention that have a value
people_pct   = percentile rank of people_concerned among the packages of the same intervention

trees (score_method balanced):
  need_score = mean of p(tree_cover_stl2018_pct, lower = more need) and p(new_trees_per_1000_residents, lower = more need)
  need_pct   = percentile rank of need_score among the 124 tree packages
  score      = (weight_need x need_pct + weight_people x people_pct) / (weight_need + weight_people)

roofs (score_method mean, no people figure):
  score      = need_score = mean of p(tree_cover_stl2018_pct, lower = more need) and p(surface_temp_lst_c, higher = more need)

cool surface, school street, elderly (score_method mean, unchanged):
  score      = (weight_need x need_score + weight_people x people_pct) / (weight_need + weight_people)
```

All weights are in `params.csv`, status assumption, default 1 (equal): `weight_need` = `weight_people` = 1, and every `weight_need_indicator_*` = 1. `need_score` in `packages.csv` is the mean of the indicator percentiles; for trees `score_basis` also gives the need percentile among the packages, so the score can be recomputed from the row: score = (need percentile + people_percentile_within_intervention) / 2. Need indicators per intervention (rules.csv): trees: tree cover, new trees per 1000 residents. roofs: tree cover, satellite surface temperature. cool surface: low-canopy schools+playgrounds, low-canopy site share, tree cover, night temp. school street: density. elderly: tree cover, night temp, density. Both trees indicators and both roof indicators exist for every package, so every package of these two tabs is scored on the same set. If people concerned is missing the score is the need part alone (`score_basis` says so). PM2.5 is not in any score. `canopy_deficit_m2` stays an indicator (it is the trees and elderly eligibility rule and it sets the tree quantity) but is in no need list.

**Rank.** `rank_within_intervention` 1 = highest score; ties at the 4 decimals of the csv: roofs by matched roof area (`roof_municipal_m2`, the quantity), larger first, then neighbourhood name; all other interventions by neighbourhood name.

**Why the indicators were reduced** (all numbers measured in `engine/validation/VERDICT.md` on the old formula):
- Trees, population dominated: the people percentile carried 67% of the old score's variance and all population-based terms together (people, density, new trees per 1000) **87%**; tree cover carried 4.4%, the canopy deficit 6.1%, night temperature 2.6%. The score correlated 0.92 with the residents percentile. Cause: an average of 4-5 weakly correlated percentiles is compressed (need-score SD 16.6) next to a raw people percentile (SD about 29), so equal nominal weights were not equal in effect. The balanced combination re-ranks the need score to a percentile first, so need and people have the same spread.
- Trees, population counted two or three times: density correlated 0.53 with residents, and new trees per 1000 0.58 with density. Density was dropped (largest single-indicator effect: 4 of the top 20).
- Trees, **canopy counted twice**: `canopy_deficit_m2` per unit of area is exactly the Meta canopy cover (Spearman -1.00), and as an absolute area it follows neighbourhood size (Spearman 0.53 with area, 0.36 with the tree-cover percentile). Dropped.
- Trees and roofs, night temperature exists only where a sensor exists (57 of 124 tree packages and 49 of 115 roof packages had none), so some packages were scored on fewer indicators. Dropped from both, which gives every package the same indicators; it is kept as an out-of-sample check.
- Roofs, **unrelated to the roofs**: the old score correlated -0.01 with the number of matched buildings, -0.14 with roof m2 and 0.03 with satellite surface temperature; its top 20 had half the average roof area (1,056 against 2,156 m2) and 11 of the 20 had a single building. The low-canopy site share was missing for 7 packages, tied 46 at 1.0 and has no roof logic, and fewer indicators ranked higher (the 5 packages scored on tree cover alone averaged 87.8). Ranks 5-11 were seven neighbourhoods tied at 87.73 in alphabetical order. The share and night temperature were replaced by satellite surface temperature, which exists for all 115 and is the only available measure of daytime surface heat, which roofs are part of.

**What each list means and does NOT mean.**
- Trees («Δρόμοι»), label `list_meaning_trees` «Πολλοί κάτοικοι με λίγη σκιά»: **many residents with little shade** (low street-tree cover, few trees planted since 2024, many residents, half and half). It is NOT a measured heat-risk ranking: on the audit's out-of-sample checks its top 20 has 1.54% canopy on an independent satellite product (all packages 5.14%) and 0.38 degC warmer nights at the sensors (27.48 against 27.10 degC, p = 0.003), but it is not hotter on satellite surface temperature (39.55 against 39.69 degC), and no health outcome was checked.
- Roofs («Κτίρια»), label `list_meaning_roofs` «Δημοτικά κτίρια σε γειτονιές χωρίς πράσινο»: **municipal buildings in bare neighbourhoods** (low street-tree cover and hot surfaces by satellite). It is NOT "which roof first": nothing in it knows occupants, roof condition, insulation, air-conditioning or whether the roof is flat; the number of buildings and the roof area only break ties. Its top 20 has 0.77% street-tree cover (all packages 4.23%), 40.27 against 39.62 degC surface temperature (circular now: LST is in the score) and, out of sample, 0.45 degC warmer nights at the sensors (27.53 against 27.08 degC, p = 0.0008). Caution: LST also flags hot bare hills (ΦΙΛΟΠΑΠΠΟΥ is rank 11). The choice between individual buildings needs the City's own data.

**Weights remain a choice, not a measurement** (sensitivity analysis of the audit, `results.json` `proposed_variants`, 2,000 runs each):
- Trees: under random weights (Dirichlet) 13.9 of the top 20 stay on average (p5-p95 9-18); under a +-30% population error per neighbourhood 15.2 of 20 (13-17), against 13.9 (11-16) with the old formula. Against the old list it keeps 16 of the top 20 (Spearman 0.93): in ΑΓΙΟΣ ΑΘΑΝΑΣΙΟΣ, ΑΓΙΟΣ ΠΑΝΤΕΛΕΗΜΩΝ, ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ, ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ ΣΕΠΟΛΙΩΝ; out ΑΓΙΟΣ ΑΡΤΕΜΗΣ, ΠΡΟΦΗΤΗΣ ΗΛΙΑΣ, ΠΕΔΙΟ ΑΡΕΩΣ Ι, ΦΩΚΙΩΝΟΣ ΝΕΓΡΗ. The top 20 holds 21.2% of the residents (old 22.1%, a random 20 about 14.5%).
- Roofs: under random weights 12.8 of the top 20 stay (8-19), Spearman 0.86 (0.69-1.00); the old roof list looked more stable (18.0) only because many packages were tied or scored on one indicator. Against the old list it keeps 9 of the top 20 (Spearman 0.64). No population figure enters the roof score.
- The weight between need and people (trees) and between tree cover and surface temperature (roofs) should be stated as policy.

## Budget mode

**Default (`--rank-by per_tab`), team decision σημείωμα ομάδας.** Each tab of the screen has its OWN budget: «Δρόμοι» = `trees_pavement`, «Κτίρια» = `roof_cool_or_green_municipal`. `--budget N` gives N euro to the trees AND, separately, N euro to the roofs; the two are never added together or compared (no common unit of impact). Rule, deterministic: the packages of the intervention that have a central cost are walked in `rank_within_intervention` order (1 first, the same order as the map colour); a package is indivisible; it is taken if its central cost fits in what is left, otherwise it is skipped and the next one is tried, down to the end of the list (so a smaller package further down can still be bought). Quantities are the package quantities, which never exceed the capacity figure. `budget_250k.md`, `budget_1m.md`, `budget_5m.md` are this mode (written on every run; `--budget N` prints the same text and writes it to `budget_<N>.md` in `--out`). Each tab section gives packages, euros spent and left over, the scenario cost range of the same selection, the first package that did not fit and the selected packages. Trees: trees, neighbourhoods and residents of those neighbourhoods (one tree package per neighbourhood, so nobody is counted twice). Roofs: m2 of matched footprint (upper bound of the area), neighbourhoods and matched buildings (lower bound); the price per m2 is an ASSUMPTION and no people figure exists.

**Non-default comparison (`--rank-by people_per_eur`)**, printed only: one list across interventions; candidates are packages with a computed central cost and a people-concerned figure, sorted by people concerned per euro (central cost) descending; ties: more people, then neighbourhood name, then intervention id; same greedy rule. The roofs stay out because they have no people figure (the output says so). The output lists the overlap warning (sum of people over packages vs residents of the neighbourhoods touched, each counted once), what was left out and what did not fit. The former `--rank-by need` (need scores of different interventions in one list) was removed: decision 1528 rejects comparing percentiles of different interventions.

## Impact statements

Always "up to", with metric, low/central/high where they exist, status and source, taken from `params.csv`.
- trees: pavement surface 60 degC in sun vs 30 degC under shade (City thermal camera, measured_athens); street air 0.5-1.6 degC lower, up to 2.2 (Tsiros 2010, measured_athens); felt temperature 3-7 degC; neighbourhood-mean air 0.1-0.2 degC for a few points of cover (published_elsewhere). No health outcome.
- roof: three items, the two measured in Athens first (one school in Kaisariani, 410 m2, uninsulated, not air-conditioned; EU "Cool Roofs in Europe" project; source code `cool_roofs_kaisariani`): classroom air in summer 1.5-2 degC lower (`classroom_air_temp_summer`), roof surface up to 25 degC lower (`roof_surface_temp`); then the simulated building cooling load 6-49% lower (one Athens nursery school; inside the building). Values are read from `params.csv` at run time. No street-level, health or euro figure is claimed; the cost rests on an assumed unit price.
- cool surface: surface up to 12 degC lower; local air up to 1.9 degC lower (simulated); single source.
- school street: NO2 at the gate up to 23% lower; no health outcome.
- elderly: up to 30% (8-46%) fewer heatwave excess deaths among those covered (Rome). Illustrative ceiling per neighbourhood = pop_65plus x heat_death_rate_65plus_per_10000_per_year / 10000 x `coverage_share_for_ceiling` x reduction%, with the municipal baseline an ASSUMPTION scaled from greater Athens (`research/interventions/FUNCTION.md`). It is a ceiling, not a forecast.

## Columns of `packages.csv` and where each number comes from

| Column | Source / formula |
|---|---|
| package_id, neighbourhood, community, intervention_id | key = intervention + neighbourhood name; names and community from the capacity file |
| eligibility_trigger | the rule that fired, with the value |
| quantity_unit, quantity_low/central/high | Step 2 |
| capacity_low/central/high | Step 2 capacity figure (capacity file, or the same parameters applied to the whole deficit) |
| quantity_note, quantity_options | text of the formula with the numbers used; alternative +3/+5 pp for trees |
| cost_low/central/high_eur, cost_status, cost_basis | Step 3; cost_status says NOT COMPUTED and which price is missing |
| recurring_cost_eur_per_year_central | maintenance 23.5 EUR/tree/year (city_contract, approximate) |
| people_concerned, people_basis | population file (`pop_total`, `pop_0_14`, `pop_65plus`); basis text from rules.csv |
| population_caveat | `_global.population_error_single_neighbourhood_pct` |
| people_per_1000_eur | see Step 3 |
| impact_up_to, impact_baseline | params (see Impact statements) |
| time_to_effect | `time_to_effect_years` of the intervention |
| evidence_status | rules.csv (catalogue evidence; trees: cooling.md and finding 1400) |
| why_here | eligibility trigger + every need indicator of the intervention with value and percentile (or "missing (not imputed)") |
| data_gaps | rules.csv gaps + every `missing` parameter of the intervention + missing prices |
| flags | capacity_unverified, lower_bound, usable_flat_share_unknown, cost_area_upper_bound, price_is_assumption, single_source_price, yard_area_unknown, upper_bound, london_prices, ceiling, cost_missing, people_missing, target_capped_by_deficit |
| param_statuses_used | the statuses of all parameters behind the row |
| context_pm25_community_ugm3 | PM2.5 estimate of the community (context only) |
| need_score, people_percentile_within_intervention, priority_score, score_basis | Priority score |
| sources | every parameter row (file :: reference [status]) plus the data files and evidence files; at least one per row |
| rank_within_intervention (new, last column) | 1 = highest `priority_score` among the packages of the same intervention; ties at the 4 decimals of the csv: first by the `rank_tie_break` field of rules.csv if any (roofs: matched roof area `roof_municipal_m2`, larger first), then by neighbourhood name (Unicode order); a package without a score ranks after all scored ones. A permutation of 1..n per intervention (tested). |
| sites_n (new, last column) | Number of sites behind the package, from the capacity file. Roofs: matched school + other municipal BUILDINGS (`schools_buildings_n` + `municipal_other_buildings_n`, unique building polygons). School street: `sites_schools_n`. Elderly: `sites_elderly_clubs_n` (clubs, not residents). Cool surface: schools + playgrounds with canopy < 5% within 150 m (equals the quantity). Trees: schools, nurseries, playgrounds and clubs with canopy < 5% (`sites_all4_canopy150m_lt5pct_n`). Information only: it does not enter the score, `people_concerned` or the budget selection (the roof budget reports it as the number of buildings). |

## Parameters with status = assumption (all of them, change in params.csv)

- `_global.canopy_target_pct` (10): benchmark of the team's capacity analysis.
- `_global.weight_need`, `_global.weight_people`, `_global.weight_need_indicator_tree_cover_stl2018_pct`, `_global.weight_need_indicator_canopy_deficit_m2`, `_global.weight_need_indicator_pop_density_per_km2`, `_global.weight_need_indicator_new_trees_per_1000_residents`, `_global.weight_need_indicator_night_temp_c`, `_global.weight_need_indicator_low_canopy_sites_share`, `_global.weight_need_indicator_low_canopy_schools_playgrounds_n`, `_global.weight_need_indicator_surface_temp_lst_c`: all 1 (equal). In use since 2026-11-21: trees use tree cover and new trees per 1000 (plus weight_need and weight_people, balanced); roofs use tree cover and surface temperature; `canopy_deficit_m2` is in no need list, so its weight is unused (kept so it can be switched back on).
- `_global.fx_gbp_eur` (1.15): documentation of the conversion behind the school street prices.
- `trees_pavement.crown_area_at_20y_m2` (20 / 35 / 50): team scenario; central equals the published 20-year large-tree value.
- `trees_pavement.survival_to_maturity_fraction` (0.35 / 0.50 / 0.79): team scenario between published figures; Athens survival unmeasured.
- `trees_pavement.share_new_small_pits` (0.5): mix of existing and new pits.
- `trees_pavement.canopy_increment_pp_package` (1), `trees_pavement.canopy_increment_pp_option_b` (3), `trees_pavement.canopy_increment_pp_option_c` (5).
- `roof_cool_or_green_municipal.roof_cost_per_m2_eur` (13.5 / 20 / 25 EUR/m2): low from the City of Athens 2012 price list (waterproofing membrane, floor proxy), central/high from a vendor web page (snippet only). The City should overwrite it with a quote.
- `roof_cool_or_green_municipal.time_to_effect_years`, `cool_surface_schoolyard_playground.time_to_effect_years`, `school_street.time_to_effect_years`, `elderly_heat_support.time_to_effect_years`: read from the catalogue wording ("immediate", "first summer").
- `elderly_heat_support.heat_death_rate_65plus_per_10000_per_year` (2.1 / 3.8 / 5.4): municipal baseline scaled from greater Athens; not published.
- `elderly_heat_support.coverage_share_for_ceiling` (1): the ceiling assumes everyone 65+ is covered.

Parameters with status `missing` (left empty on purpose): `trees_pavement.plantable_pit_count`, `roof_cool_or_green_municipal.usable_flat_roof_share`, `roof_cool_or_green_municipal.occupants_per_building`, `cool_surface_schoolyard_playground.yard_area_per_site_m2`, `school_street.pupils_per_school`, `elderly_heat_support.cost_per_person_covered_eur`.

## `packages.json` and `labels_el.csv` (for the web UI)

`packages.json` is a compact export (UTF-8, no spaces, one trailing newline, fixed key order, written by `generate_packages.py`): `generated_from` (file names), `interventions` {id: label_code, unit, has_cost}, `packages` (same order as `packages.csv`), `sources` {source_code: ref, file}. A package has: neighbourhood, community, intervention, quantity {central, low, high, unit}, capacity (central), cost_eur {central, low, high} or null, people_concerned or null, people_basis_code, priority_score, rank_within_intervention, sites_n, time_to_effect_years {low, high}, evidence_code, impacts, why_here, data_gaps, flags. Every number is the value written to `packages.csv` (same rounding); an empty csv cell is `null`. There are no English sentences in it: only short snake_case codes. `impacts`: metric_code, direction (always `down`: the value goes down), value_up_to (the largest of low/central/high; for the pavement surface the difference sun minus shade), low, high, unit, status, source_code. Trees carry temperature metrics only. `why_here`: the eligibility field and the need indicators of the package with value, unit and need percentile (integer, as in the csv text; `null` for fields that are not part of the score). `data_gaps` codes come from `rules.csv` (`data_gap_codes`, in the same order as `data_gaps`), `missing_<parameter>` for every missing parameter and `no_cost_<parameter>` for a missing price. `evidence_code` and `people_basis_code` come from `rules.csv` as well.

`labels_el.csv` has one row per code (code, kind, label_el, long_el). kind is intervention, indicator, metric, status, evidence, gap, flag, people_basis, source, unit or list_meaning. Codes are unique across kinds. Plain Greek, no middle dot, only periods and commas as punctuation; impact labels start with Έως (up to); status labels read μετρημένο στην Αθήνα, δημοσιευμένο σε άλλη πόλη, από τη σύμβαση του Δήμου, υπόθεση, λείπει. The test fails if a code of `packages.json` has no label. When a new code appears in the json, add its row by hand. The two `list_meaning` rows (`list_meaning_trees`, `list_meaning_roofs`) are not in `packages.json`: they are the sentence the screen can show for what each tab's order means (see Priority score).

## What this calculation does NOT claim

- No deaths avoided from trees. Trees are shown with temperature effects only; they do not change PM2.5, and no mortality figure is attached to them. School streets show NO2 at the gate only.
- Impacts are upper bounds ("up to") transferred from other cities (Rome, London, Paris, Flisvos, Istanbul, Sacramento) except where status = measured_athens (pavement surface under shade; street air, Tsiros 2010). The elderly ceiling rests on an assumed baseline and on a programme that covered isolated 80+ only.
- Packages are not additive: they concern the same residents and the same streets. The budget output shows both the overlapping sum and the residents of the neighbourhoods touched, each counted once.
- Single-neighbourhood population is uncertain by about +-25-30%; totals are reliable. People concerned is a modelled estimate, not a count of those who benefit.
- Quantities are arithmetic on capacity data, not plans: no tree-pit register, roof footprint is not usable roof, closable school streets are not assessed, the canopy data is from ~2018-2020 and does not see trees planted since.
- A missing price gives an empty cost, never an estimate. Packages without a cost cannot enter the budget ranking. The roof cost is the one exception by design: its price is a labelled ASSUMPTION (status `assumption`, flag `price_is_assumption`), not a measured or contracted price. Cool surfaces and elderly support still have no price and no cost.
- Roof costs are an upper bound of area and a lower bound of buildings at once; they are not a bill of quantities and exclude roof preparation.
- Neighbourhood-mean air temperature barely moves (0.1-0.2 degC for a few points of cover); the benefit is local and arrives after 10-20 years.
- Night temperature is a sensor value where a sensor exists (correlation, not proof of cause; placement unknown). It is no longer in the trees or roofs score (only cool surface and elderly use it). The daily maximum is not used.
- `surface_temp_lst_c` is satellite SURFACE temperature (ground and roofs) on summer days 2016-2020, not air temperature and not a heat-risk measure; it barely follows tree cover in Athens (Spearman -0.09) and also flags hot bare hills.
- Neither tab's order is a measured heat-risk or "which roof first" ranking (see Priority score, What each list means).
