# What a budget of 250,000 EUR buys in each tab (reference calculation)

Default mode (`--rank-by per_tab`), following the team decision σημείωμα ομάδας: each tab has its OWN budget of 250,000 EUR. The two tabs are not added together and not compared with each other: there is no common unit of impact. Rule: the packages of the intervention that have a central cost are walked in `rank_within_intervention` order (1 first, the same order as the colour of the map). A package is indivisible: it is taken if its central cost fits in what is left, otherwise it is skipped and the next one is tried, down to the end of the list. Greedy, not optimal, deterministic. Costs are central values; low-high is the scenario range of the same selection.

## Δρόμοι: street trees (`trees_pavement`)

- What the order means: "many residents with little shade" (need = low street-tree cover and few trees planted since 2024, balanced half and half with the number of residents; README, Priority score). It is NOT a measured heat-risk ranking.
- Packages selected: 7 of 124 with a price (124 packages in the tab)
- Spent: 247,528 EUR (scenario range of the same selection 81,823-1,119,755 EUR); left over: 2,472 EUR
- Trees: 731 (central; low 326, high 1,820)
- Neighbourhoods: 7
- Residents of these neighbourhoods (people concerned; one tree package per neighbourhood, so nobody is counted twice): 40,923 (modelled estimate, +-25-30% per neighbourhood; not a count of those who benefit)
- Did not fit in what was left: 117 packages (total central cost 5,639,971 EUR); the first one was rank 5, ΚΑΤΩ ΠΑΤΗΣΙΑ II (93,458 EUR)

| rank | neighbourhood | community | quantity (central) | cost central EUR (low-high) | people concerned |
|---|---|---|---|---|---|
| 1 | ΑΓΙΑΣ ΖΩΝΗΣ | 6η ΔΚ | 165 trees | 55,871 (18,322-252,868) | 11,109 |
| 2 | ΧΑΜΟΣΤΕΡΝΑ | 3η ΔΚ | 126 trees | 42,665 (14,055-192,573) | 6,641 |
| 3 | ΑΡΙΣΤΟΤΕΛΟΥΣ | 6η ΔΚ | 104 trees | 35,216 (11,546-158,734) | 7,081 |
| 4 | ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ | 4η ΔΚ | 151 trees | 51,131 (16,816-231,949) | 6,804 |
| 6 | ΑΜΕΡΙΚΗΣ | 6η ΔΚ | 140 trees | 47,406 (15,812-215,338) | 8,502 |
| 65 | ΤΟΥΡΚΟΒΟΥΝΙΑ ΙΙ | 7η ΔΚ | 26 trees | 8,804 (3,012-39,991) | 670 |
| 116 | ΒΟΥΛΗ | 1η ΔΚ | 19 trees | 6,434 (2,259-28,302) | 117 |

## Κτίρια: cool roofs on municipal buildings (`roof_cool_or_green_municipal`)

- What the order means: "municipal buildings in bare neighbourhoods" (need = low street-tree cover and hot satellite surface temperature; README, Priority score). It does NOT say which roof to treat first: that needs the City's data on occupants and roof condition.
- The price per m2 is an ASSUMPTION: 13.5 / 20 / 25 EUR/m2 (`params.csv` roof_cool_or_green_municipal.roof_cost_per_m2_eur, status assumption), applied to the whole matched footprint and excluding roof preparation. The City should replace it with a quote.
- No people figure exists for roofs (occupants per building are missing), so this tab counts buildings and m2, not people.
- Packages selected: 14 of 115 with a price (115 packages in the tab)
- Spent: 249,832 EUR (scenario range of the same selection 168,637-312,290 EUR); left over: 168 EUR
- Matched roof footprint: 12,492 m2 (an UPPER bound of the roof area that can be treated: the flat and usable share is unknown)
- Neighbourhoods: 14
- Buildings: 27 (matched municipal buildings, a LOWER bound: not every municipal building is matched)
- Did not fit in what was left: 101 packages (total central cost 4,707,868 EUR); the first one was rank 6, ΓΚΑΖΟΧΩΡΙ (165,887 EUR)

| rank | neighbourhood | community | m2 roof footprint | buildings | cost central EUR (low-high) |
|---|---|---|---|---|---|
| 1 | ΧΑΜΟΣΤΕΡΝΑ | 3η ΔΚ | 1,850 | 5 | 36,999 (24,974-46,249) |
| 2 | ΑΓΙΑΣ ΑΙΚΑΤΕΡΙΝΗΣ | 3η ΔΚ | 2,050 | 5 | 40,999 (27,675-51,249) |
| 3 | ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ | 1η ΔΚ | 1,743 | 3 | 34,854 (23,526-43,567) |
| 4 | ΚΕΡΑΜΕΙΚΟΣ | 3η ΔΚ | 792 | 1 | 15,849 (10,698-19,811) |
| 5 | ΚΑΤΩ ΕΡΥΘΡΟΣ | 7η ΔΚ | 225 | 1 | 4,497 (3,036-5,622) |
| 7 | ΝΕΟΣ ΚΟΣΜΟΣ | 2η ΔΚ | 247 | 1 | 4,936 (3,332-6,170) |
| 8 | ΑΓ.ΚΩΝ/ΝΟΣ-ΠΛ.ΒΑΘΗΣ | 1η ΔΚ | 359 | 1 | 7,179 (4,846-8,973) |
| 9 | ΒΕΪΚΟΥ | 1η ΔΚ | 2,094 | 3 | 41,884 (28,272-52,355) |
| 10 | ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ | 6η ΔΚ | 569 | 1 | 11,375 (7,678-14,218) |
| 11 | ΦΙΛΟΠΑΠΠΟΥ | 1η ΔΚ | 722 | 1 | 14,432 (9,742-18,041) |
| 12 | ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ-ΝΙΡΒΑΝΑ | 4η ΔΚ | 1,259 | 2 | 25,188 (17,002-31,485) |
| 15 | ΑΓΙΟΣ ΓΕΩΡΓΙΟΣ ΚΥΨΕΛΗΣ | 6η ΔΚ | 242 | 1 | 4,840 (3,267-6,050) |
| 34 | ΑΜΠΕΛΟΚΗΠΟΙ Ι | 7η ΔΚ | 155 | 1 | 3,100 (2,093-3,875) |
| 64 | ΑΓΙΑΣ ΖΩΝΗΣ | 6η ΔΚ | 185 | 1 | 3,700 (2,497-4,625) |

Nothing here is a recommendation: it is the arithmetic of the data and the cited prices. Impacts are upper bounds transferred from other cities except where status=measured_athens (see README). The non-default comparison across interventions is `--rank-by people_per_eur`.
