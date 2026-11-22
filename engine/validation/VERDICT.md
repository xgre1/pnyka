# Verdict: is the priority ranking based on data or arbitrary?

Every number below comes from `validation.py` (run it again to check) and is stored in `results.json`. The engine was reproduced exactly before anything else: trees 124/124 packages, roofs 115/115, max |Δ priority_score| 0.00005 (the 4-decimal rounding of the csv), 0 rank mismatches.

**Short answer.**
- **Trees («Δρόμοι»)** are not random. The list is reproducible and built from real data. Its top 20 is measurably bare, warmer at night and populous, and this was checked on data the formula does not use. But the weights are a choice that moves about 6 of the top 20. In practice the score ranks *population* far more than *tree cover*, and that inherits the ±30% population error. Three or four small changes make it defensible.
- **Roofs («Κτίρια»)** are built from data, but the data answer a different question. The list ranks "bare neighbourhoods", which is close to "least street-tree cover first" (Spearman 0.88). Nothing in it measures roofs, roof heat or building use. The top places are decided by ties and by how many indicators happen to exist: ranks 1 and 2 are scored on one indicator, for a neighbourhood with one building each. As a "which roof first" ranking it is not defensible without changes.

---

## Trees (`trees_pavement`, 124 packages)

### (i) What the data support
- **Low canopy, on an independent product.** In `wc2021_tree_pct` the top 20 has 2.33% canopy, against 5.14% for all packages and 8.99% for the bottom 20. A random 20 has p5-p95 3.50-7.16%, and the permutation p = 0.0007.
- **Warmer nights, out of sample.** The score was recomputed without `night_temp_c` and compared with `heat_night` at the 67 packages that have a sensor. The top 20 average 27.40 °C, the bottom 20 26.96 °C, all sensor packages 27.10 °C (p = 0.017, Spearman 0.21). The in-sample version would be circular and was not used.
- **People.** The top 20 holds 22.1% of the municipality's residents (random pick 14.5%, p5-p95 12.4-16.6%), 21.6% of residents 65+ (random 14.4%) and 26.1% of the low-canopy schools (random 16.1%, p = 0.0098). The top 30 holds 32.3%, 31.5% and 40.2%. The residents figure is partly built in, because residents are half of the score. The 65+ and school figures are not.
- **Not supported: daytime surface heat.** On satellite LST the top 20 is slightly *cooler*: 39.45 °C against 39.69 °C for all packages (p for "hotter" = 0.94). Spearman between score and LST is −0.17 (n=124), or −0.05 on an extended n=144 score. This cannot be blamed on the score alone, because LST barely follows tree cover anywhere in Athens (Spearman −0.09, n=144). Do not claim that the list targets the hottest surfaces.

### (ii) What is arbitrary, and how much the result depends on it
| Choice | Top 20 kept (mean, p5-p95) | Spearman vs baseline |
|---|---|---|
| 2,000 random weights: need indicators + need vs people (Dirichlet) | 14.1 (10-18) | 0.91 (0.69-0.99) |
| need-indicator weights only | 16.8 (13-19) | 0.98 |
| need vs people weight only | 15.2 (11-19) | 0.94 |
| moderate weights (each ½× to 2×) | 17.6 (15-19) | 0.99 |
| population ±30% per neighbourhood (2,000 runs) | 13.9 (11-16) | 0.92 (0.90-0.93) |
| min-max instead of percentiles / z-scores | 17 / 16 | 0.97 / 0.97 |

- Top 10 under random weights: 7.2 of 10 kept (5-9). Top 30: 23.7 of 30 (18-28).
- Robust core (in the top 20 in at least 90% of the weight runs): ΑΓΙΑΣ ΖΩΝΗΣ, ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ, ΧΑΜΟΣΤΕΡΝΑ, ΑΡΙΣΤΟΤΕΛΟΥΣ, ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ.
- Only **2** survive both the weight and the population runs: ΑΓΙΑΣ ΖΩΝΗΣ and ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ.
- 1M EUR budget: the baseline buys 24 neighbourhoods. 67% of that selection stays under random weights (46-92%), and 67% under population error (54-79%).

### (iii) Defects, ranked by how much they change the ranking
1. **Population dominates, and "equal weights" are not equal in effect.** The people percentile carries **67%** of the score variance. All the population-based terms together (people, density, new trees per 1000) carry **87%**. Tree cover carries **4.4%**, the canopy deficit 6.1% and night temperature 2.6%.
   - Spearman between the score and the residents percentile is 0.92.
   - Dropping tree cover changes 1 of the top 20. Dropping the people part changes 8.
   - The cause: an average of 4-5 weakly correlated percentiles is compressed (need-score SD 16.6 with 5 indicators, 18.4 with 4) next to a raw percentile (SD ≈ 29).
   - The consequence: the ±30% population error moves 6 of the top 20 on average.
2. **Population counted two or three times.** Density correlates with residents at 0.53. New trees per 1000 correlates with density at 0.58, because population is its denominator. Dropping density alone changes 4 of the top 20, the largest single-indicator effect.
3. **Area effect and double counting in `canopy_deficit_m2`.** It is an absolute area: Spearman with neighbourhood area 0.53, but only 0.36 with the tree-cover percentile. Per unit of area it is exactly the Meta CHM cover (Spearman −1.00), so it is a second tree-cover measure. Dropping it changes 3 of the top 20; making it per area changes 2.
4. **Missing indicator.** 57 of 124 packages have no `night_temp_c`. No systematic bias was found:
   - The top 20 has 11 no-sensor neighbourhoods against 9.2 expected (p = 0.46).
   - Mean scores are 52.2 with the indicator missing and 52.9 with it present.
   - Adding night temperature changes 2 of the top 20 (mean |rank change| 2.4).
   It is still an inconsistency (4 indicators for some neighbourhoods, 5 for others), but a minor one.

### (iv) The smallest set of changes that makes it defensible (measured; the engine was not edited)
| Change | Top 20 kept | Spearman | wc2021 top 20 | Night, out of sample (top 20) | Residents in top 20 |
|---|---|---|---|---|---|
| current | 20 | 1 | 2.33% | (circular) | 22.1% |
| A. drop density and canopy_deficit_m2 | 17 | 0.97 | 1.58% | (circular) | 21.2% |
| B. A + drop night_temp_c (same indicators for every neighbourhood) | 16 | 0.96 | 1.57% | 27.43 °C, p=0.010 | 21.3% |
| **C. B + balance need vs people** (need re-ranked to a percentile, then ½ need + ½ people) | **16** | **0.93** | **1.54%** | **27.48 °C, p=0.003** | **21.2%** |
| D. simplest: ½ pct(low tree cover) + ½ pct(residents) | 11 | 0.88 | 1.18% | 27.52 °C, p=0.001 | 20.4% |

- **C is the recommended minimum.** It keeps 16 of the 20 and is more robust to population error: 15.2 of 20 kept (13-17), against 13.9 (11-16) today. It brings in ΑΓΙΟΣ ΑΘΑΝΑΣΙΟΣ, ΑΓΙΟΣ ΠΑΝΤΕΛΕΗΜΩΝ, ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ and ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ ΣΕΠΟΛΙΩΝ. It drops ΑΓΙΟΣ ΑΡΤΕΜΗΣ, ΠΡΟΦΗΤΗΣ ΗΛΙΑΣ, ΠΕΔΙΟ ΑΡΕΩΣ Ι and ΦΩΚΙΩΝΟΣ ΝΕΓΡΗ.
- D is the most transparent option. It leaves one explicit policy weight (bare streets vs many residents), and population robustness is 16.0 of 20 (14-18).
- In both C and D the weights remain a choice: about 14 of 20 stay under random weights. That choice should be stated as policy, not presented as data.

**Is the composite better than a naive rule?**
- "Least tree cover first" gives a different list: 3 of 20 in common, Spearman 0.30. It targets canopy (0.83%) and night heat (27.49 °C, p=0.003) better, but reaches only 13.6% of residents, no better than a random pick (14.5%). Also, 13 packages tie at 0% cover, so its own order is partly alphabetical.
- The composite is closest to "most residents first" (Spearman 0.92). It is **not measurably better** than the two-term rule D: D has better canopy and night targeting, and 1.7 points fewer residents.

### (v) What to tell a judge who asks "why this formula?"
"The street-tree list combines two things measured for every neighbourhood: how many people live there, and how little shade they have (tree cover, canopy gap, recent planting, and night temperature where a sensor exists). Each is a percentile rank, averaged with equal weights, and every input is in a public file. We checked the result against data the formula does not use. Its top 20 has 2.3% canopy on an independent satellite product, against 5.1% on average. With night temperature removed from the score, its sensor neighbourhoods are 0.3 °C warmer at night than average (p = 0.02). It holds 22% of the city's residents and 26% of its low-canopy schools in 20 of 124 neighbourhoods, where a random pick would hold about 15%. The equal weights are a choice, not a measurement. Under 2,000 random weightings, on average 14 of the 20 stay, and Αγίας Ζώνης and Πλατεία Κανάρη stay under every weighting and every population error we tested. The list mostly follows where people live, so we present it as 'many residents with little shade', not as a measured heat-risk ranking. Daytime satellite surface temperature does not single these neighbourhoods out."

---

## Roofs (`roof_cool_or_green_municipal`, 115 packages; score = need only, no people part)

### (i) What the data support
- **Bare neighbourhoods.** On `wc2021_tree_pct` the top 20 has 1.19% canopy, against 6.76% for all packages (p = 0.0001).
- **Warmer nights, out of sample.** With the score recomputed without night temperature, the top 20 sensor neighbourhoods average 27.62 °C, against 27.08 °C for all 66 sensor packages and 26.56 °C for the bottom 20 (p = 0.0001, Spearman 0.53). Tree cover does track night heat: Spearman −0.45 with heat_night across the 77 sensors.
- That is all. The list identifies **hot-at-night, bare neighbourhoods**. It does not identify roofs.

**Not supported:**
- **Roof or surface heat.** The score's Spearman with satellite LST is 0.03. The top 20 averages 39.56 °C, all packages 39.62 °C (p for "hotter" = 0.64).
- **Building stock.** The top 20 has fewer buildings: 2.45 on average against 3.22 for all packages (p for "more" = 0.97). It has half the roof area, 1,056 m2 against 2,156 m2 (p = 0.998), and fewer schools + nurseries + clubs, 2.9 against 4.3. 11 of the top 20 have a single matched building. The score's Spearman with buildings is −0.01 and with roof m2 −0.14.
- Per euro this does not hurt by accident: because the top roofs are small, 1M EUR treats 108 buildings in 37 neighbourhoods. Ranking by buildings first would treat 71. This is a side effect, not a design.

### (ii) What is arbitrary, and how much the result depends on it
- **Random weights.** 18.0 of the top 20 kept (16-20). Spearman 0.965 (0.92-0.996). Top 10: 8.0 kept (4-10). The 1M selection keeps 89% (84-97%).
- **Robust core.** 13 neighbourhoods. Population error has no effect, because no population figure enters the roof score.
- **Normalisation.** Min-max keeps 15 of 20 and z-scores keep 16, but z-scores keep only **2 of the top 10**.
- **Leave-one-out.** Without tree cover: 10 of 20 kept, **1 of the top 10**. Without night temperature: 16. Without the low-canopy share: 18.
- **This robustness is an artefact, not evidence.** 5 packages are scored on a single indicator, so weights cannot move them. 46 packages tie at share = 1.0. A stable list is not a valid list.

### (iii) Defects, ranked by how much they change the ranking
1. **The indicators have no logical link to "cool this roof first".**
   - Street-tree cover does not shade the roof of a multi-storey school.
   - The share of sites with less than 5% canopy within 150 m describes shade at ground level around the site, not roof heat. It is a share, so one bare site scores the maximum.
   - Night temperature exists at 66 of the 115 packages, and schools are used by day.
   - Replacing the indicators with heat exposure plus number of buildings keeps only 3-4 of the current top 20 (Spearman 0.04-0.48).
   - The current list is close to "least street-tree cover first": 16 of 20 in common, Spearman 0.88. Tree cover carries 56% of the score variance.
2. **The number of indicators differs between packages, and fewer indicators rank higher.** The 5 packages scored on 1 indicator (tree cover alone; no sites, no sensor) have a mean score of 87.8, and 4 are in the top 20, at ranks 1, 2, 4 and 13. The 46 two-indicator packages have 11 places in the top 20; the 64 three-indicator packages have 5. No-sensor neighbourhoods take 14 places in the top 20 against 8.5 expected (p = 0.011).
3. **Ties decide the order.** 46 packages have share = 1.0, 16 of them with only 1-2 sites. The top 20 has only 13 distinct scores. Ranks 5-11 are seven neighbourhoods tied at 87.73 and ordered alphabetically, and ranks 1-2 are tied as well.

### (iv) The smallest set of changes that makes it defensible (measured)
| Change | Top 20 kept | Spearman | Night, out of sample (top 20) | Buildings, top 20 mean | 1M EUR buys |
|---|---|---|---|---|---|
| current | 20 | 1 | (circular) | 2.45 | 108 buildings / 37 nbhds |
| drop night_temp_c (same set for all; share still missing for 7) | 16 | 0.96 | 27.62 °C, p=0.0001 | 2.70 | 107 / 38 |
| LST instead of night_temp_c | 10 | 0.84 | 27.47 °C, p=0.003 | 2.90 | 90 / 31 |
| **tree cover + LST** (both exist for all 115; share dropped) | **9** | **0.64** | **27.53 °C, p=0.0008** | **3.20** | **86 / 27** |
| tree cover + LST + buildings | 4 | 0.48 | 27.41 °C, p=0.009 | 5.75 | 93 / 19 |

- **Recommended minimum: "tree cover + LST".** It needs two changes:
  - Drop the low-canopy share: it is missing for 7 packages, ties 46 of them, and has no roof logic.
  - Replace sensor-only night temperature with satellite surface temperature, which exists for every package. It is the only available measure of daytime surface heat, which roofs are part of.
- It keeps 9 of the current top 20.
- LST is then inside the score, so the LST check becomes circular. The out-of-sample night check still holds (p = 0.0008).
- Caution: LST also flags hot bare hills. ΦΙΛΟΠΑΠΠΟΥ enters this top 20.
- Adding a use term (buildings) is logical, but the three terms then disagree, so the weights matter: 12.6 of 20 kept under random weights (8-18), against 18.0 today. The weight would have to be stated as policy.
- None of these variants knows occupants, roof condition, insulation or air-conditioning. The City holds that data, and it should decide between individual buildings.

### (v) What to tell a judge who asks "why this formula?"
"The building list ranks neighbourhoods by how bare their surroundings are: street-tree cover, the share of schools, nurseries, playgrounds and clubs with almost no canopy nearby, and night temperature where a sensor exists. That part checks out against data the formula does not use. Its top 20 has 1.2% canopy on an independent satellite product, against 6.8% on average, and its nights are 0.5 °C warmer than average at the sensors (p < 0.001). It does not tell you which roof to cool first. It is unrelated to satellite surface temperature, and to how many municipal buildings or square metres of roof a neighbourhood has. Its top 20 has fewer buildings than average, and the cost per m2 is an assumption. We show it as 'municipal buildings in bare, hot-at-night neighbourhoods'. The choice between individual roofs needs the City's own data on occupancy and roof condition."
