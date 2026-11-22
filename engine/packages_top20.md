# Top 20 packages by priority score (reference calculation)

Generated from data by engine/generate_packages.py. This is a proposal for the team, not a decision. Score per intervention (README, Priority score): trees = (w_need x need percentile among the tree packages + w_people x people percentile) / (w_need + w_people), the need score being the mean of the percentiles of tree cover and new trees per 1000 residents; roofs = need score only (tree cover and satellite surface temperature); the other interventions = (w_need x need_score + w_people x people_percentile) / (w_need + w_people). Percentiles are within the intervention, so scores of different interventions are not comparable and this mixed top 20 is an ordering aid only (see README, OPEN_QUESTIONS). The top 3 per intervention follow rank_within_intervention.

## Counts

| intervention | packages | with a cost | without a cost |
|---|---|---|---|
| trees_pavement | 124 | 124 | 0 |
| roof_cool_or_green_municipal | 115 | 115 | 0 |
| cool_surface_schoolyard_playground | 86 | 0 | 86 |
| school_street | 98 | 98 | 0 |
| elderly_heat_support | 124 | 0 | 124 |

## Top 20

### 1. roof_cool_or_green_municipal: ΧΑΜΟΣΤΕΡΝΑ (3η ΔΚ)

- Priority score: 96.2 (need_only (people concerned missing); need 96.2, people percentile n/a)
- Quantity: 1,850 (low 1,850, high 1,850) m2 matched roof footprint (lower bound)
- Capacity figure: 1,850 m2 matched roof footprint
- Cost: 36,999 EUR central (low 24,974, high 46,249)
- People concerned: not available (occupants of the matched buildings: unknown (no pupils/staff count in open data), so empty)
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Classroom air temperature in summer (measured, one school): up to 2 degC lower (low 1.5, high 2; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens), 410 m2, uninsulated, not air-conditioned) | Roof surface temperature (measured, one school): up to 25 degC lower (high 25; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens)) | Cooling load of the building (simulated, inside the building only): up to 49 % lower (low 6, high 49; status published_elsewhere; row H10: Santamouris M et al. 2007 Energy 32:1781-1788) | No street-level or health figure is claimed; no euro saving is claimed (building energy use is missing); the roof cost is an assumed unit price on the matched footprint
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H10): simulation calibrated on measurements, one Athens nursery school; effect is inside the building
- Why here: ELIGIBLE: roof_municipal_m2=1,850 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | satellite land-surface temperature, summer day 2016-2020 = 41.1 degC (need percentile 97)
- Data gaps: roof price per m2 is an assumption (low from the City of Athens 2012 price list, central and high from vendor figures), a City quote is needed ; share of the matched roof that is flat and usable ; occupants and energy use of the buildings ; municipal buildings missing from the matched layers (libraries ;  sports halls ;  markets) ; param roof_cool_or_green_municipal.usable_flat_roof_share missing ; param roof_cool_or_green_municipal.occupants_per_building missing
- Flags: lower_bound;usable_flat_share_unknown;cost_area_upper_bound;price_is_assumption;people_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 2. roof_cool_or_green_municipal: ΑΓΙΑΣ ΑΙΚΑΤΕΡΙΝΗΣ (3η ΔΚ)

- Priority score: 95.5 (need_only (people concerned missing); need 95.5, people percentile n/a)
- Quantity: 2,050 (low 2,050, high 2,050) m2 matched roof footprint (lower bound)
- Capacity figure: 2,050 m2 matched roof footprint
- Cost: 40,999 EUR central (low 27,675, high 51,249)
- People concerned: not available (occupants of the matched buildings: unknown (no pupils/staff count in open data), so empty)
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Classroom air temperature in summer (measured, one school): up to 2 degC lower (low 1.5, high 2; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens), 410 m2, uninsulated, not air-conditioned) | Roof surface temperature (measured, one school): up to 25 degC lower (high 25; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens)) | Cooling load of the building (simulated, inside the building only): up to 49 % lower (low 6, high 49; status published_elsewhere; row H10: Santamouris M et al. 2007 Energy 32:1781-1788) | No street-level or health figure is claimed; no euro saving is claimed (building energy use is missing); the roof cost is an assumed unit price on the matched footprint
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H10): simulation calibrated on measurements, one Athens nursery school; effect is inside the building
- Why here: ELIGIBLE: roof_municipal_m2=2,050 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | satellite land-surface temperature, summer day 2016-2020 = 40.9 degC (need percentile 95)
- Data gaps: roof price per m2 is an assumption (low from the City of Athens 2012 price list, central and high from vendor figures), a City quote is needed ; share of the matched roof that is flat and usable ; occupants and energy use of the buildings ; municipal buildings missing from the matched layers (libraries ;  sports halls ;  markets) ; param roof_cool_or_green_municipal.usable_flat_roof_share missing ; param roof_cool_or_green_municipal.occupants_per_building missing
- Flags: lower_bound;usable_flat_share_unknown;cost_area_upper_bound;price_is_assumption;people_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 3. school_street: ΑΜΕΡΙΚΗΣ (6η ΔΚ)

- Priority score: 93.9 (need+people; need 93.0, people percentile 94.8)
- Quantity: 3 (low 3, high 3) school street schemes (one per school)
- Capacity figure: 3 school street schemes
- Cost: 194,400 EUR central (low 62,100, high 517,500)
- People concerned: 848 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 4.36
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=3 (rule > 0) | population density = 34,702 persons per km2 (need percentile 93)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 4. school_street: ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ (6η ΔΚ)

- Priority score: 93.4 (need+people; need 97.2, people percentile 89.7)
- Quantity: 8 (low 8, high 8) school street schemes (one per school)
- Capacity figure: 8 school street schemes
- Cost: 518,400 EUR central (low 165,600, high 1,380,000)
- People concerned: 787 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 1.52
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=8 (rule > 0) | population density = 37,267 persons per km2 (need percentile 97)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 5. elderly_heat_support: ΑΓΙΑΣ ΖΩΝΗΣ (6η ΔΚ)

- Priority score: 92.8 (need+people; need 86.4, people percentile 99.2)
- Quantity: 2,279 (low 2,279, high 2,279) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 2,279 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 2,279 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.566 heat deaths/yr fewer (low 0.0383, central 0.26); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.866 (low 0.479, high 1.23) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=2,279 (rule > 0); canopy_deficit_m2=23,276 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.914 % of area (need percentile 75) | summer night temperature = missing (not imputed) | population density = 38,694 persons per km2 (need percentile 98)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 6. trees_pavement: ΑΓΙΑΣ ΖΩΝΗΣ (6η ΔΚ)

- Priority score: 92.7 (need+people balanced (need score re-ranked among the 124 packages: need percentile 86.1789); need 82.9, people percentile 99.2)
- Quantity: 165 (low 73, high 411) trees
- Capacity figure: 1,331 trees
- Other options: +3 pp: 493 trees (central cost 166,937 EUR); +5 pp: 821 trees (central cost 278,003 EUR)
- Cost: 55,871 EUR central (low 18,322, high 252,868)
- People concerned: 11,109 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 198.83
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=23,276 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.914 % of area (need percentile 75) | new trees since 2024 per 1000 residents = 1.71 trees per 1000 (need percentile 91)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 7. trees_pavement: ΧΑΜΟΣΤΕΡΝΑ (3η ΔΚ)

- Priority score: 92.3 (need+people balanced (need score re-ranked among the 124 packages: need percentile 97.561); need 94.8, people percentile 87.0)
- Quantity: 126 (low 56, high 313) trees
- Capacity figure: 1,115 trees
- Other options: +3 pp: 376 trees (central cost 127,319 EUR); +5 pp: 626 trees (central cost 211,973 EUR)
- Cost: 42,665 EUR central (low 14,055, high 192,573)
- People concerned: 6,641 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 155.65
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=19,502 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | new trees since 2024 per 1000 residents = 1.2 trees per 1000 (need percentile 94)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 8. elderly_heat_support: ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ (6η ΔΚ)

- Priority score: 92.3 (need+people; need 90.2, people percentile 94.3)
- Quantity: 1,643 (low 1,643, high 1,643) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 1,643 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 1,643 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.408 heat deaths/yr fewer (low 0.0276, central 0.187); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.624 (low 0.345, high 0.887) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=1,643 (rule > 0); canopy_deficit_m2=17,085 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.995 % of area (need percentile 73) | summer night temperature = 29.2 degC (need percentile 100) | population density = 37,267 persons per km2 (need percentile 97)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 9. elderly_heat_support: ΑΡΙΣΤΟΤΕΛΟΥΣ (6η ΔΚ)

- Priority score: 91.7 (need+people; need 92.3, people percentile 91.1)
- Quantity: 1,539 (low 1,539, high 1,539) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 1,539 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 1,539 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.382 heat deaths/yr fewer (low 0.0258, central 0.175); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.585 (low 0.323, high 0.831) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=1,539 (rule > 0); canopy_deficit_m2=12,960 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.473 % of area (need percentile 86) | summer night temperature = missing (not imputed) | population density = 39,252 persons per km2 (need percentile 99)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 10. school_street: ΑΡΙΣΤΟΤΕΛΟΥΣ (6η ΔΚ)

- Priority score: 91.6 (need+people; need 98.6, people percentile 84.5)
- Quantity: 4 (low 4, high 4) school street schemes (one per school)
- Capacity figure: 4 school street schemes
- Cost: 259,200 EUR central (low 82,800, high 690,000)
- People concerned: 706 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 2.72
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=4 (rule > 0) | population density = 39,252 persons per km2 (need percentile 99)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 11. school_street: ΑΓΙΟΣ ΝΙΚΟΛΑΟΣ (6η ΔΚ)

- Priority score: 90.3 (need+people; need 95.1, people percentile 85.6)
- Quantity: 8 (low 8, high 8) school street schemes (one per school)
- Capacity figure: 8 school street schemes
- Cost: 518,400 EUR central (low 165,600, high 1,380,000)
- People concerned: 728 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 1.40
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=8 (rule > 0) | population density = 35,452 persons per km2 (need percentile 95)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 12. trees_pavement: ΑΡΙΣΤΟΤΕΛΟΥΣ (6η ΔΚ)

- Priority score: 89.8 (need+people balanced (need score re-ranked among the 124 packages: need percentile 87.8049); need 85.3, people percentile 91.9)
- Quantity: 104 (low 46, high 258) trees
- Capacity figure: 741 trees
- Other options: +3 pp: 310 trees (central cost 104,971 EUR); +5 pp: 516 trees (central cost 174,725 EUR)
- Cost: 35,216 EUR central (low 11,546, high 158,734)
- People concerned: 7,081 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 201.07
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=12,960 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.473 % of area (need percentile 86) | new trees since 2024 per 1000 residents = 2.82 trees per 1000 (need percentile 85)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 13. cool_surface_schoolyard_playground: ΚΑΤΩ ΠΑΤΗΣΙΑ II (4η ΔΚ)

- Priority score: 89.3 (need+people; need 79.8, people percentile 98.8)
- Quantity: 8 (low 8, high 8) sites (schools+playgrounds, canopy <5% within 150 m)
- Capacity figure: 8 sites
- Cost: NOT COMPUTED (NOT COMPUTED: missing cool_surface_schoolyard_playground.yard_area_per_site_m2)
- People concerned: 1,208 (children 0-14 living in the neighbourhood (upper proxy; pupils per school and playground users are not available))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Surface temperature: up to 12 degC lower (high 12; status published_elsewhere; row H8: Santamouris M et al. 2012 Build Environ (Flisvos Park, Palaio Faliro)) | Local air temperature (simulated): up to 1.9 degC lower (high 1.9; status published_elsewhere; row H8: Santamouris et al. 2012, PHOENICS CFD model) | No health outcome is claimed
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H8): surface temperature measured at Flisvos; air effect only simulated; cost from a single source
- Why here: ELIGIBLE: low_canopy_schools_playgrounds_n=8 (rule > 0) | schools and playgrounds with canopy <5% within 150 m = 8 count (need percentile 97) | share of sites with canopy <5% within 150 m = 1 share 0-1 (need percentile 80) | tree cover (Street Tree Layer 2018) = 0.824 % of area (need percentile 77) | summer night temperature = 27.4 degC (need percentile 66)
- Data gaps: yard or playground area per site (no dataset has it) ; second source for the price per m2 ; param cool_surface_schoolyard_playground.yard_area_per_site_m2 missing ; no cost: cool_surface_schoolyard_playground.yard_area_per_site_m2
- Flags: single_source_price;yard_area_unknown;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 14. trees_pavement: ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ (4η ΔΚ)

- Priority score: 89.0 (need+people balanced (need score re-ranked among the 124 packages: need percentile 88.6179); need 86.0, people percentile 89.4)
- Quantity: 151 (low 67, high 377) trees
- Capacity figure: 1,205 trees
- Other options: +3 pp: 452 trees (central cost 153,054 EUR); +5 pp: 754 trees (central cost 255,316 EUR)
- Cost: 51,131 EUR central (low 16,816, high 231,949)
- People concerned: 6,804 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 133.07
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=21,072 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.535 % of area (need percentile 83) | new trees since 2024 per 1000 residents = 2.2 trees per 1000 (need percentile 90)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 15. elderly_heat_support: ΑΓΙΟΣ ΓΕΩΡΓΙΟΣ ΚΥΨΕΛΗΣ (6η ΔΚ)

- Priority score: 88.9 (need+people; need 94.1, people percentile 83.7)
- Quantity: 1,371 (low 1,371, high 1,371) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 1,371 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 1,371 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.341 heat deaths/yr fewer (low 0.023, central 0.156); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.521 (low 0.288, high 0.74) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=1,371 (rule > 0); canopy_deficit_m2=14,313 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | summer night temperature = missing (not imputed) | population density = 34,636 persons per km2 (need percentile 92)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 16. school_street: ΧΑΜΟΣΤΕΡΝΑ (3η ΔΚ)

- Priority score: 88.5 (need+people; need 85.3, people percentile 91.8)
- Quantity: 3 (low 3, high 3) school street schemes (one per school)
- Capacity figure: 3 school street schemes
- Cost: 194,400 EUR central (low 62,100, high 517,500)
- People concerned: 806 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 4.15
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=3 (rule > 0) | population density = 30,323 persons per km2 (need percentile 85)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 17. trees_pavement: ΚΑΤΩ ΠΑΤΗΣΙΑ II (4η ΔΚ)

- Priority score: 88.2 (need+people balanced (need score re-ranked among the 124 packages: need percentile 78.0488); need 76.9, people percentile 98.4)
- Quantity: 276 (low 123, high 690) trees
- Capacity figure: 1,946 trees
- Other options: +3 pp: 828 trees (central cost 280,373 EUR); +5 pp: 1,380 trees (central cost 467,289 EUR)
- Cost: 93,458 EUR central (low 30,872, high 424,522)
- People concerned: 10,654 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 114.00
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=34,042 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.824 % of area (need percentile 77) | new trees since 2024 per 1000 residents = 4.97 trees per 1000 (need percentile 77)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 18. cool_surface_schoolyard_playground: ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ (6η ΔΚ)

- Priority score: 87.4 (need+people; need 87.8, people percentile 87.1)
- Quantity: 9 (low 9, high 9) sites (schools+playgrounds, canopy <5% within 150 m)
- Capacity figure: 9 sites
- Cost: NOT COMPUTED (NOT COMPUTED: missing cool_surface_schoolyard_playground.yard_area_per_site_m2)
- People concerned: 787 (children 0-14 living in the neighbourhood (upper proxy; pupils per school and playground users are not available))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Surface temperature: up to 12 degC lower (high 12; status published_elsewhere; row H8: Santamouris M et al. 2012 Build Environ (Flisvos Park, Palaio Faliro)) | Local air temperature (simulated): up to 1.9 degC lower (high 1.9; status published_elsewhere; row H8: Santamouris et al. 2012, PHOENICS CFD model) | No health outcome is claimed
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H8): surface temperature measured at Flisvos; air effect only simulated; cost from a single source
- Why here: ELIGIBLE: low_canopy_schools_playgrounds_n=9 (rule > 0) | schools and playgrounds with canopy <5% within 150 m = 9 count (need percentile 98) | share of sites with canopy <5% within 150 m = 1 share 0-1 (need percentile 80) | tree cover (Street Tree Layer 2018) = 0.995 % of area (need percentile 73) | summer night temperature = 29.2 degC (need percentile 100)
- Data gaps: yard or playground area per site (no dataset has it) ; second source for the price per m2 ; param cool_surface_schoolyard_playground.yard_area_per_site_m2 missing ; no cost: cool_surface_schoolyard_playground.yard_area_per_site_m2
- Flags: single_source_price;yard_area_unknown;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 19. school_street: ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ-ΝΙΡΒΑΝΑ (4η ΔΚ)

- Priority score: 87.4 (need+people; need 94.4, people percentile 80.4)
- Quantity: 2 (low 2, high 2) school street schemes (one per school)
- Capacity figure: 2 school street schemes
- Cost: 129,600 EUR central (low 41,400, high 345,000)
- People concerned: 688 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 5.31
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=2 (rule > 0) | population density = 34,915 persons per km2 (need percentile 94)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 20. trees_pavement: ΑΜΕΡΙΚΗΣ (6η ΔΚ)

- Priority score: 87.4 (need+people balanced (need score re-ranked among the 124 packages: need percentile 77.2358); need 74.8, people percentile 97.6)
- Quantity: 140 (low 63, high 350) trees
- Capacity figure: 670 trees
- Other options: +3 pp: 420 trees (central cost 142,218 EUR); +5 pp: 670 trees (central cost 226,872 EUR)
- Cost: 47,406 EUR central (low 15,812, high 215,338)
- People concerned: 8,502 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 179.34
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=11,719 (rule > 0) | tree cover (Street Tree Layer 2018) = 1.28 % of area (need percentile 66) | new trees since 2024 per 1000 residents = 2.94 trees per 1000 (need percentile 83)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

## Top 3 per intervention

#### trees_pavement

### 1. trees_pavement: ΑΓΙΑΣ ΖΩΝΗΣ (6η ΔΚ)

- Priority score: 92.7 (need+people balanced (need score re-ranked among the 124 packages: need percentile 86.1789); need 82.9, people percentile 99.2)
- Quantity: 165 (low 73, high 411) trees
- Capacity figure: 1,331 trees
- Other options: +3 pp: 493 trees (central cost 166,937 EUR); +5 pp: 821 trees (central cost 278,003 EUR)
- Cost: 55,871 EUR central (low 18,322, high 252,868)
- People concerned: 11,109 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 198.83
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=23,276 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.914 % of area (need percentile 75) | new trees since 2024 per 1000 residents = 1.71 trees per 1000 (need percentile 91)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 2. trees_pavement: ΧΑΜΟΣΤΕΡΝΑ (3η ΔΚ)

- Priority score: 92.3 (need+people balanced (need score re-ranked among the 124 packages: need percentile 97.561); need 94.8, people percentile 87.0)
- Quantity: 126 (low 56, high 313) trees
- Capacity figure: 1,115 trees
- Other options: +3 pp: 376 trees (central cost 127,319 EUR); +5 pp: 626 trees (central cost 211,973 EUR)
- Cost: 42,665 EUR central (low 14,055, high 192,573)
- People concerned: 6,641 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 155.65
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=19,502 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | new trees since 2024 per 1000 residents = 1.2 trees per 1000 (need percentile 94)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 3. trees_pavement: ΑΡΙΣΤΟΤΕΛΟΥΣ (6η ΔΚ)

- Priority score: 89.8 (need+people balanced (need score re-ranked among the 124 packages: need percentile 87.8049); need 85.3, people percentile 91.9)
- Quantity: 104 (low 46, high 258) trees
- Capacity figure: 741 trees
- Other options: +3 pp: 310 trees (central cost 104,971 EUR); +5 pp: 516 trees (central cost 174,725 EUR)
- Cost: 35,216 EUR central (low 11,546, high 158,734)
- People concerned: 7,081 (all residents of the neighbourhood (street trees shade people who live in or walk through it; no catchment radius exists at neighbourhood level))
- People per 1000 EUR: 201.07
- Impact (upper bounds): Pavement surface 60 degC in sun vs 30 degC under tree shade: up to 30 degC lower under a mature crown (status measured_athens; City thermal camera, Plateia Argentinis Dimokratias, summer 2025) | Air in the shaded street at 14:00 in a heatwave: up to 1.6 degC lower (low 0.5, high 1.6; status measured_athens; Tsiros 2010, measured in Athens, 14:00 in a heatwave) | Very shaded street: up to 2.2 degC lower (high 2.2; status measured_athens; Tsiros 2010, measured in Athens, very shaded street) | Felt temperature under the tree (daytime): up to 7 degC lower (low 3, high 7; status published_elsewhere; Sari 2025 (Istanbul), daytime) | Neighbourhood-MEAN air temperature for a few points of cover: up to 0.2 degC lower (low 0.1, high 0.2; status published_elsewhere; Iungman et al. Lancet 2023 (about 0.4 degC at 30% cover); Ziter et al. PNAS 2019 (0.1-0.2 or less for a few points of cover)) | No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect
- Time to effect: 10 to 20 years (status published_elsewhere)
- Evidence: Surface and street-air cooling measured in Athens (City thermal camera; Tsiros 2010); neighbourhood-mean air effect small (Iungman 2023, Ziter 2019); no health outcome claimed
- Why here: ELIGIBLE: canopy_deficit_m2=12,960 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.473 % of area (need percentile 86) | new trees since 2024 per 1000 residents = 2.82 trees per 1000 (need percentile 85)
- Data gaps: tree-pit register or list of plantable spots (capacity_unverified) ; survival of Athens plantings (no survival record) ; whether the canopy model of ~2018-2020 misses trees planted since ; param trees_pavement.plantable_pit_count missing
- Flags: capacity_unverified
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

#### roof_cool_or_green_municipal

### 1. roof_cool_or_green_municipal: ΧΑΜΟΣΤΕΡΝΑ (3η ΔΚ)

- Priority score: 96.2 (need_only (people concerned missing); need 96.2, people percentile n/a)
- Quantity: 1,850 (low 1,850, high 1,850) m2 matched roof footprint (lower bound)
- Capacity figure: 1,850 m2 matched roof footprint
- Cost: 36,999 EUR central (low 24,974, high 46,249)
- People concerned: not available (occupants of the matched buildings: unknown (no pupils/staff count in open data), so empty)
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Classroom air temperature in summer (measured, one school): up to 2 degC lower (low 1.5, high 2; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens), 410 m2, uninsulated, not air-conditioned) | Roof surface temperature (measured, one school): up to 25 degC lower (high 25; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens)) | Cooling load of the building (simulated, inside the building only): up to 49 % lower (low 6, high 49; status published_elsewhere; row H10: Santamouris M et al. 2007 Energy 32:1781-1788) | No street-level or health figure is claimed; no euro saving is claimed (building energy use is missing); the roof cost is an assumed unit price on the matched footprint
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H10): simulation calibrated on measurements, one Athens nursery school; effect is inside the building
- Why here: ELIGIBLE: roof_municipal_m2=1,850 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | satellite land-surface temperature, summer day 2016-2020 = 41.1 degC (need percentile 97)
- Data gaps: roof price per m2 is an assumption (low from the City of Athens 2012 price list, central and high from vendor figures), a City quote is needed ; share of the matched roof that is flat and usable ; occupants and energy use of the buildings ; municipal buildings missing from the matched layers (libraries ;  sports halls ;  markets) ; param roof_cool_or_green_municipal.usable_flat_roof_share missing ; param roof_cool_or_green_municipal.occupants_per_building missing
- Flags: lower_bound;usable_flat_share_unknown;cost_area_upper_bound;price_is_assumption;people_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 2. roof_cool_or_green_municipal: ΑΓΙΑΣ ΑΙΚΑΤΕΡΙΝΗΣ (3η ΔΚ)

- Priority score: 95.5 (need_only (people concerned missing); need 95.5, people percentile n/a)
- Quantity: 2,050 (low 2,050, high 2,050) m2 matched roof footprint (lower bound)
- Capacity figure: 2,050 m2 matched roof footprint
- Cost: 40,999 EUR central (low 27,675, high 51,249)
- People concerned: not available (occupants of the matched buildings: unknown (no pupils/staff count in open data), so empty)
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Classroom air temperature in summer (measured, one school): up to 2 degC lower (low 1.5, high 2; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens), 410 m2, uninsulated, not air-conditioned) | Roof surface temperature (measured, one school): up to 25 degC lower (high 25; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens)) | Cooling load of the building (simulated, inside the building only): up to 49 % lower (low 6, high 49; status published_elsewhere; row H10: Santamouris M et al. 2007 Energy 32:1781-1788) | No street-level or health figure is claimed; no euro saving is claimed (building energy use is missing); the roof cost is an assumed unit price on the matched footprint
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H10): simulation calibrated on measurements, one Athens nursery school; effect is inside the building
- Why here: ELIGIBLE: roof_municipal_m2=2,050 (rule > 0) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | satellite land-surface temperature, summer day 2016-2020 = 40.9 degC (need percentile 95)
- Data gaps: roof price per m2 is an assumption (low from the City of Athens 2012 price list, central and high from vendor figures), a City quote is needed ; share of the matched roof that is flat and usable ; occupants and energy use of the buildings ; municipal buildings missing from the matched layers (libraries ;  sports halls ;  markets) ; param roof_cool_or_green_municipal.usable_flat_roof_share missing ; param roof_cool_or_green_municipal.occupants_per_building missing
- Flags: lower_bound;usable_flat_share_unknown;cost_area_upper_bound;price_is_assumption;people_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 3. roof_cool_or_green_municipal: ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ (1η ΔΚ)

- Priority score: 84.6 (need_only (people concerned missing); need 84.6, people percentile n/a)
- Quantity: 1,743 (low 1,743, high 1,743) m2 matched roof footprint (lower bound)
- Capacity figure: 1,743 m2 matched roof footprint
- Cost: 34,854 EUR central (low 23,526, high 43,567)
- People concerned: not available (occupants of the matched buildings: unknown (no pupils/staff count in open data), so empty)
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Classroom air temperature in summer (measured, one school): up to 2 degC lower (low 1.5, high 2; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens), 410 m2, uninsulated, not air-conditioned) | Roof surface temperature (measured, one school): up to 25 degC lower (high 25; status measured_athens; EU 'Cool Roofs in Europe' project, Kaisariani school (Athens)) | Cooling load of the building (simulated, inside the building only): up to 49 % lower (low 6, high 49; status published_elsewhere; row H10: Santamouris M et al. 2007 Energy 32:1781-1788) | No street-level or health figure is claimed; no euro saving is claimed (building energy use is missing); the roof cost is an assumed unit price on the matched footprint
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H10): simulation calibrated on measurements, one Athens nursery school; effect is inside the building
- Why here: ELIGIBLE: roof_municipal_m2=1,743 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.868 % of area (need percentile 76) | satellite land-surface temperature, summer day 2016-2020 = 40.8 degC (need percentile 93)
- Data gaps: roof price per m2 is an assumption (low from the City of Athens 2012 price list, central and high from vendor figures), a City quote is needed ; share of the matched roof that is flat and usable ; occupants and energy use of the buildings ; municipal buildings missing from the matched layers (libraries ;  sports halls ;  markets) ; param roof_cool_or_green_municipal.usable_flat_roof_share missing ; param roof_cool_or_green_municipal.occupants_per_building missing
- Flags: lower_bound;usable_flat_share_unknown;cost_area_upper_bound;price_is_assumption;people_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

#### cool_surface_schoolyard_playground

### 1. cool_surface_schoolyard_playground: ΚΑΤΩ ΠΑΤΗΣΙΑ II (4η ΔΚ)

- Priority score: 89.3 (need+people; need 79.8, people percentile 98.8)
- Quantity: 8 (low 8, high 8) sites (schools+playgrounds, canopy <5% within 150 m)
- Capacity figure: 8 sites
- Cost: NOT COMPUTED (NOT COMPUTED: missing cool_surface_schoolyard_playground.yard_area_per_site_m2)
- People concerned: 1,208 (children 0-14 living in the neighbourhood (upper proxy; pupils per school and playground users are not available))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Surface temperature: up to 12 degC lower (high 12; status published_elsewhere; row H8: Santamouris M et al. 2012 Build Environ (Flisvos Park, Palaio Faliro)) | Local air temperature (simulated): up to 1.9 degC lower (high 1.9; status published_elsewhere; row H8: Santamouris et al. 2012, PHOENICS CFD model) | No health outcome is claimed
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H8): surface temperature measured at Flisvos; air effect only simulated; cost from a single source
- Why here: ELIGIBLE: low_canopy_schools_playgrounds_n=8 (rule > 0) | schools and playgrounds with canopy <5% within 150 m = 8 count (need percentile 97) | share of sites with canopy <5% within 150 m = 1 share 0-1 (need percentile 80) | tree cover (Street Tree Layer 2018) = 0.824 % of area (need percentile 77) | summer night temperature = 27.4 degC (need percentile 66)
- Data gaps: yard or playground area per site (no dataset has it) ; second source for the price per m2 ; param cool_surface_schoolyard_playground.yard_area_per_site_m2 missing ; no cost: cool_surface_schoolyard_playground.yard_area_per_site_m2
- Flags: single_source_price;yard_area_unknown;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 2. cool_surface_schoolyard_playground: ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ (6η ΔΚ)

- Priority score: 87.4 (need+people; need 87.8, people percentile 87.1)
- Quantity: 9 (low 9, high 9) sites (schools+playgrounds, canopy <5% within 150 m)
- Capacity figure: 9 sites
- Cost: NOT COMPUTED (NOT COMPUTED: missing cool_surface_schoolyard_playground.yard_area_per_site_m2)
- People concerned: 787 (children 0-14 living in the neighbourhood (upper proxy; pupils per school and playground users are not available))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Surface temperature: up to 12 degC lower (high 12; status published_elsewhere; row H8: Santamouris M et al. 2012 Build Environ (Flisvos Park, Palaio Faliro)) | Local air temperature (simulated): up to 1.9 degC lower (high 1.9; status published_elsewhere; row H8: Santamouris et al. 2012, PHOENICS CFD model) | No health outcome is claimed
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H8): surface temperature measured at Flisvos; air effect only simulated; cost from a single source
- Why here: ELIGIBLE: low_canopy_schools_playgrounds_n=9 (rule > 0) | schools and playgrounds with canopy <5% within 150 m = 9 count (need percentile 98) | share of sites with canopy <5% within 150 m = 1 share 0-1 (need percentile 80) | tree cover (Street Tree Layer 2018) = 0.995 % of area (need percentile 73) | summer night temperature = 29.2 degC (need percentile 100)
- Data gaps: yard or playground area per site (no dataset has it) ; second source for the price per m2 ; param cool_surface_schoolyard_playground.yard_area_per_site_m2 missing ; no cost: cool_surface_schoolyard_playground.yard_area_per_site_m2
- Flags: single_source_price;yard_area_unknown;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 3. cool_surface_schoolyard_playground: ΧΑΜΟΣΤΕΡΝΑ (3η ΔΚ)

- Priority score: 86.0 (need+people; need 82.5, people percentile 89.4)
- Quantity: 3 (low 3, high 3) sites (schools+playgrounds, canopy <5% within 150 m)
- Capacity figure: 3 sites
- Cost: NOT COMPUTED (NOT COMPUTED: missing cool_surface_schoolyard_playground.yard_area_per_site_m2)
- People concerned: 806 (children 0-14 living in the neighbourhood (upper proxy; pupils per school and playground users are not available))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Surface temperature: up to 12 degC lower (high 12; status published_elsewhere; row H8: Santamouris M et al. 2012 Build Environ (Flisvos Park, Palaio Faliro)) | Local air temperature (simulated): up to 1.9 degC lower (high 1.9; status published_elsewhere; row H8: Santamouris et al. 2012, PHOENICS CFD model) | No health outcome is claimed
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H8): surface temperature measured at Flisvos; air effect only simulated; cost from a single source
- Why here: ELIGIBLE: low_canopy_schools_playgrounds_n=3 (rule > 0) | schools and playgrounds with canopy <5% within 150 m = 3 count (need percentile 72) | share of sites with canopy <5% within 150 m = 1 share 0-1 (need percentile 80) | tree cover (Street Tree Layer 2018) = 0 % of area (need percentile 96) | summer night temperature = missing (not imputed)
- Data gaps: yard or playground area per site (no dataset has it) ; second source for the price per m2 ; param cool_surface_schoolyard_playground.yard_area_per_site_m2 missing ; no cost: cool_surface_schoolyard_playground.yard_area_per_site_m2
- Flags: single_source_price;yard_area_unknown;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

#### school_street

### 1. school_street: ΑΜΕΡΙΚΗΣ (6η ΔΚ)

- Priority score: 93.9 (need+people; need 93.0, people percentile 94.8)
- Quantity: 3 (low 3, high 3) school street schemes (one per school)
- Capacity figure: 3 school street schemes
- Cost: 194,400 EUR central (low 62,100, high 517,500)
- People concerned: 848 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 4.36
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=3 (rule > 0) | population density = 34,702 persons per km2 (need percentile 93)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 2. school_street: ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ (6η ΔΚ)

- Priority score: 93.4 (need+people; need 97.2, people percentile 89.7)
- Quantity: 8 (low 8, high 8) school street schemes (one per school)
- Capacity figure: 8 school street schemes
- Cost: 518,400 EUR central (low 165,600, high 1,380,000)
- People concerned: 787 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 1.52
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=8 (rule > 0) | population density = 37,267 persons per km2 (need percentile 97)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 3. school_street: ΑΡΙΣΤΟΤΕΛΟΥΣ (6η ΔΚ)

- Priority score: 91.6 (need+people; need 98.6, people percentile 84.5)
- Quantity: 4 (low 4, high 4) school street schemes (one per school)
- Capacity figure: 4 school street schemes
- Cost: 259,200 EUR central (low 82,800, high 690,000)
- People concerned: 706 (children 0-14 living in the neighbourhood (upper proxy; pupils per school are not available))
- People per 1000 EUR: 2.72
- Impact (upper bounds): NO2 at the school gate during closure hours: up to 23 % lower (high 23; status published_elsewhere; row A3: GLA 2021 School Streets air quality study (18 schools)) | NO2 is not in the PM2.5 mortality function: no health outcome is claimed
- Time to effect: 0 years (status assumption)
- Evidence: moderate (catalogue A3): GLA 2021 study of 18 London schools; NO2 at the gate only
- Why here: ELIGIBLE: sites_schools_n=4 (rule > 0) | population density = 39,252 persons per km2 (need percentile 99)
- Data gaps: pupils per school ; which streets can legally and practically be closed (traffic decision and enforcement) ; an Athens price per scheme ; param school_street.pupils_per_school missing
- Flags: upper_bound;london_prices
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

#### elderly_heat_support

### 1. elderly_heat_support: ΑΓΙΑΣ ΖΩΝΗΣ (6η ΔΚ)

- Priority score: 92.8 (need+people; need 86.4, people percentile 99.2)
- Quantity: 2,279 (low 2,279, high 2,279) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 2,279 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 2,279 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.566 heat deaths/yr fewer (low 0.0383, central 0.26); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.866 (low 0.479, high 1.23) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=2,279 (rule > 0); canopy_deficit_m2=23,276 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.914 % of area (need percentile 75) | summer night temperature = missing (not imputed) | population density = 38,694 persons per km2 (need percentile 98)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 2. elderly_heat_support: ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ (6η ΔΚ)

- Priority score: 92.3 (need+people; need 90.2, people percentile 94.3)
- Quantity: 1,643 (low 1,643, high 1,643) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 1,643 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 1,643 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.408 heat deaths/yr fewer (low 0.0276, central 0.187); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.624 (low 0.345, high 0.887) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=1,643 (rule > 0); canopy_deficit_m2=17,085 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.995 % of area (need percentile 73) | summer night temperature = 29.2 degC (need percentile 100) | population density = 37,267 persons per km2 (need percentile 97)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

### 3. elderly_heat_support: ΑΡΙΣΤΟΤΕΛΟΥΣ (6η ΔΚ)

- Priority score: 91.7 (need+people; need 92.3, people percentile 91.1)
- Quantity: 1,539 (low 1,539, high 1,539) residents 65+ (ceiling of people who could be covered)
- Capacity figure: 1,539 residents 65+
- Cost: NOT COMPUTED (NOT COMPUTED: missing elderly_heat_support.cost_per_person_covered_eur)
- People concerned: 1,539 (residents aged 65+ (modelled estimate))
- People per 1000 EUR: n/a (no cost)
- Impact (upper bounds): Heatwave excess deaths among those COVERED: up to 46 % fewer (low 8, central 30, high 46; status published_elsewhere; row H5: Orlando S et al. 2021 IJERPH 18:11587 (Rome, 'Long Live the Elderly')) | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage 1): up to 0.382 heat deaths/yr fewer (low 0.0258, central 0.175); not a forecast: Rome covered isolated 80+ only, the baseline is an assumption, the population has +-25-30% error
- Baseline: baseline heat deaths/yr among residents 65+ here: 0.585 (low 0.323, high 0.831) [ASSUMPTION: scaled from greater Athens, not a measured count]
- Time to effect: 0 to 1 years (status assumption)
- Evidence: moderate (catalogue H5): Rome, ecological and non-randomised, isolated 80+; cost not reported
- Why here: ELIGIBLE: pop_65plus=1,539 (rule > 0); canopy_deficit_m2=12,960 (rule > 0) | tree cover (Street Tree Layer 2018) = 0.473 % of area (need percentile 86) | summer night temperature = missing (not imputed) | population density = 39,252 persons per km2 (need percentile 99)
- Data gaps: cost of the programme per person ; number of isolated residents 80+ (the Rome target group ;  the 80+ file column is a model share and is not used) ; municipal heat-death baseline (assumption) ; param elderly_heat_support.cost_per_person_covered_eur missing ; no cost: elderly_heat_support.cost_per_person_covered_eur
- Flags: ceiling;cost_missing
- Population caveat: single-neighbourhood population error about +-25-30% (sources agree only r=0.43-0.68); totals are reliable; not a precise count

