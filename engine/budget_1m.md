# What a budget of 1,000,000 EUR buys in each tab (reference calculation)

Default mode (`--rank-by per_tab`), following the team decision σημείωμα ομάδας: each tab has its OWN budget of 1,000,000 EUR. The two tabs are not added together and not compared with each other: there is no common unit of impact. Rule: the packages of the intervention that have a central cost are walked in `rank_within_intervention` order (1 first, the same order as the colour of the map). A package is indivisible: it is taken if its central cost fits in what is left, otherwise it is skipped and the next one is tried, down to the end of the list. Greedy, not optimal, deterministic. Costs are central values; low-high is the scenario range of the same selection.

## Δρόμοι: street trees (`trees_pavement`)

- What the order means: "many residents with little shade" (need = low street-tree cover and few trees planted since 2024, balanced half and half with the number of residents; README, Priority score). It is NOT a measured heat-risk ranking.
- Packages selected: 24 of 124 with a price (124 packages in the tab)
- Spent: 996,544 EUR (scenario range of the same selection 328,546-4,514,704 EUR); left over: 3,456 EUR
- Trees: 2,943 (central; low 1,309, high 7,338)
- Neighbourhoods: 24
- Residents of these neighbourhoods (people concerned; one tree package per neighbourhood, so nobody is counted twice): 158,398 (modelled estimate, +-25-30% per neighbourhood; not a count of those who benefit)
- Did not fit in what was left: 100 packages (total central cost 4,890,955 EUR); the first one was rank 25, ΑΓΙΟΣ ΑΡΤΕΜΗΣ (44,359 EUR)

| rank | neighbourhood | community | quantity (central) | cost central EUR (low-high) | people concerned |
|---|---|---|---|---|---|
| 1 | ΑΓΙΑΣ ΖΩΝΗΣ | 6η ΔΚ | 165 trees | 55,871 (18,322-252,868) | 11,109 |
| 2 | ΧΑΜΟΣΤΕΡΝΑ | 3η ΔΚ | 126 trees | 42,665 (14,055-192,573) | 6,641 |
| 3 | ΑΡΙΣΤΟΤΕΛΟΥΣ | 6η ΔΚ | 104 trees | 35,216 (11,546-158,734) | 7,081 |
| 4 | ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ | 4η ΔΚ | 151 trees | 51,131 (16,816-231,949) | 6,804 |
| 5 | ΚΑΤΩ ΠΑΤΗΣΙΑ II | 4η ΔΚ | 276 trees | 93,458 (30,872-424,522) | 10,654 |
| 6 | ΑΜΕΡΙΚΗΣ | 6η ΔΚ | 140 trees | 47,406 (15,812-215,338) | 8,502 |
| 7 | ΑΓΙΟΣ ΝΙΚΟΛΑΟΣ | 6η ΔΚ | 113 trees | 38,263 (12,550-173,500) | 6,988 |
| 8 | ΑΓΙΟΣ ΑΘΑΝΑΣΙΟΣ | 6η ΔΚ | 144 trees | 48,761 (16,063-220,875) | 6,082 |
| 9 | ΠΛΑΤΕΙΑ ΚΑΝΑΡΗ | 6η ΔΚ | 115 trees | 38,941 (12,800-177,192) | 7,498 |
| 10 | ΠΟΛΥΓΩΝΟ | 6η ΔΚ | 99 trees | 33,523 (11,044-151,967) | 6,004 |
| 11 | ΑΓΙΟΣ ΓΕΩΡΓΙΟΣ ΚΥΨΕΛΗΣ | 6η ΔΚ | 104 trees | 35,216 (11,546-159,965) | 6,293 |
| 12 | ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ-ΝΙΡΒΑΝΑ | 4η ΔΚ | 98 trees | 33,184 (11,044-150,736) | 5,984 |
| 13 | ΑΓΙΟΣ ΠΑΝΤΕΛΕΗΜΩΝ | 6η ΔΚ | 89 trees | 30,137 (10,040-135,970) | 5,628 |
| 14 | ΑΓΙΑ ΠΑΡΑΣΚΕΥΗ | 5η ΔΚ | 117 trees | 39,618 (13,051-179,653) | 6,030 |
| 15 | ΚΑΤΩ ΠΑΤΗΣΙΑ I | 5η ΔΚ | 76 trees | 25,735 (8,534-116,282) | 5,915 |
| 16 | ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ | 6η ΔΚ | 90 trees | 30,475 (10,040-138,431) | 4,814 |
| 17 | ΚΟΛΩΝΟΣ | 4η ΔΚ | 193 trees | 65,353 (21,585-296,550) | 7,437 |
| 18 | ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ ΣΕΠΟΛΙΩΝ | 4η ΔΚ | 84 trees | 28,444 (9,287-127,972) | 4,753 |
| 19 | ΚΟΛΙΑΤΣΟΥ I | 6η ΔΚ | 100 trees | 33,862 (11,295-153,812) | 6,242 |
| 20 | ΛΟΦΟΣ ΣΚΟΥΖΕ | 4η ΔΚ | 118 trees | 39,957 (13,051-180,268) | 6,353 |
| 21 | ΚΑΤΩ ΕΡΥΘΡΟΣ | 7η ΔΚ | 128 trees | 43,343 (14,306-196,265) | 4,795 |
| 22 | ΠΑΓΚΡΑΤΙ ΙΙ | 2η ΔΚ | 91 trees | 30,814 (10,040-139,046) | 4,872 |
| 23 | ΚΟΛΙΑΤΣΟΥ II | 5η ΔΚ | 82 trees | 27,766 (9,287-126,126) | 5,974 |
| 24 | ΙΟΥΛΙΑΝΟΥ-ΦΙΛΑΔΕΛΦΕΙΑΣ | 1η ΔΚ | 140 trees | 47,406 (15,561-214,107) | 5,945 |

## Κτίρια: cool roofs on municipal buildings (`roof_cool_or_green_municipal`)

- What the order means: "municipal buildings in bare neighbourhoods" (need = low street-tree cover and hot satellite surface temperature; README, Priority score). It does NOT say which roof to treat first: that needs the City's data on occupants and roof condition.
- The price per m2 is an ASSUMPTION: 13.5 / 20 / 25 EUR/m2 (`params.csv` roof_cool_or_green_municipal.roof_cost_per_m2_eur, status assumption), applied to the whole matched footprint and excluding roof preparation. The City should replace it with a quote.
- No people figure exists for roofs (occupants per building are missing), so this tab counts buildings and m2, not people.
- Packages selected: 27 of 115 with a price (115 packages in the tab)
- Spent: 998,834 EUR (scenario range of the same selection 674,213-1,248,542 EUR); left over: 1,166 EUR
- Matched roof footprint: 49,942 m2 (an UPPER bound of the roof area that can be treated: the flat and usable share is unknown)
- Neighbourhoods: 27
- Buildings: 86 (matched municipal buildings, a LOWER bound: not every municipal building is matched)
- Did not fit in what was left: 88 packages (total central cost 3,958,866 EUR); the first one was rank 25, ΑΓΙΟΣ ΠΑΝΤΕΛΕΗΜΩΝ (39,423 EUR)

| rank | neighbourhood | community | m2 roof footprint | buildings | cost central EUR (low-high) |
|---|---|---|---|---|---|
| 1 | ΧΑΜΟΣΤΕΡΝΑ | 3η ΔΚ | 1,850 | 5 | 36,999 (24,974-46,249) |
| 2 | ΑΓΙΑΣ ΑΙΚΑΤΕΡΙΝΗΣ | 3η ΔΚ | 2,050 | 5 | 40,999 (27,675-51,249) |
| 3 | ΕΜΠΟΡΙΚΟ ΚΕΝΤΡΟ | 1η ΔΚ | 1,743 | 3 | 34,854 (23,526-43,567) |
| 4 | ΚΕΡΑΜΕΙΚΟΣ | 3η ΔΚ | 792 | 1 | 15,849 (10,698-19,811) |
| 5 | ΚΑΤΩ ΕΡΥΘΡΟΣ | 7η ΔΚ | 225 | 1 | 4,497 (3,036-5,622) |
| 6 | ΓΚΑΖΟΧΩΡΙ | 3η ΔΚ | 8,294 | 5 | 165,887 (111,974-207,358) |
| 7 | ΝΕΟΣ ΚΟΣΜΟΣ | 2η ΔΚ | 247 | 1 | 4,936 (3,332-6,170) |
| 8 | ΑΓ.ΚΩΝ/ΝΟΣ-ΠΛ.ΒΑΘΗΣ | 1η ΔΚ | 359 | 1 | 7,179 (4,846-8,973) |
| 9 | ΒΕΪΚΟΥ | 1η ΔΚ | 2,094 | 3 | 41,884 (28,272-52,355) |
| 10 | ΑΓΙΟΥ ΜΕΛΕΤΙΟΥ | 6η ΔΚ | 569 | 1 | 11,375 (7,678-14,218) |
| 11 | ΦΙΛΟΠΑΠΠΟΥ | 1η ΔΚ | 722 | 1 | 14,432 (9,742-18,041) |
| 12 | ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ-ΝΙΡΒΑΝΑ | 4η ΔΚ | 1,259 | 2 | 25,188 (17,002-31,485) |
| 13 | ΑΓΙΟΣ ΙΩΑΝΝΗΣ | 2η ΔΚ | 1,484 | 4 | 29,674 (20,030-37,092) |
| 14 | ΚΑΤΩ ΠΑΤΗΣΙΑ II | 4η ΔΚ | 4,100 | 9 | 82,004 (55,353-102,505) |
| 15 | ΑΓΙΟΣ ΓΕΩΡΓΙΟΣ ΚΥΨΕΛΗΣ | 6η ΔΚ | 242 | 1 | 4,840 (3,267-6,050) |
| 16 | ΙΟΥΛΙΑΝΟΥ-ΦΙΛΑΔΕΛΦΕΙΑΣ | 1η ΔΚ | 2,683 | 7 | 53,658 (36,219-67,072) |
| 17 | ΜΕΤΑΞΟΥΡΓΕΙΟ | 3η ΔΚ | 3,700 | 3 | 73,993 (49,945-92,491) |
| 18 | ΠΛΑΤΕΙΑ ΑΤΤΙΚΗΣ | 4η ΔΚ | 936 | 2 | 18,724 (12,639-23,406) |
| 19 | ΨΥΡΡΗ-ΚΟΥΜΟΥΝΔΟΥΡΟΥ | 1η ΔΚ | 826 | 2 | 16,518 (11,150-20,648) |
| 20 | ΘΥΜΑΡΑΚΙΑ | 4η ΔΚ | 3,720 | 7 | 74,397 (50,218-92,996) |
| 21 | ΚΟΛΩΝΟΣ | 4η ΔΚ | 2,767 | 6 | 55,345 (37,358-69,181) |
| 22 | ΤΡΕΙΣ ΓΕΦΥΡΕΣ | 5η ΔΚ | 2,145 | 3 | 42,905 (28,961-53,631) |
| 23 | ΚΟΛΟΚΥΝΘΟΥ | 4η ΔΚ | 5,678 | 8 | 113,562 (76,654-141,952) |
| 24 | ΚΟΥΚΑΚΙ | 1η ΔΚ | 502 | 1 | 10,036 (6,774-12,545) |
| 26 | ΑΚΑΔΗΜΙΑ ΠΛΑΤΩΝΟΣ ΙΙ | 4η ΔΚ | 562 | 1 | 11,244 (7,590-14,055) |
| 34 | ΑΜΠΕΛΟΚΗΠΟΙ Ι | 7η ΔΚ | 155 | 1 | 3,100 (2,093-3,875) |
| 37 | ΛΟΦΟΣ ΣΚΟΥΖΕ | 4η ΔΚ | 238 | 2 | 4,756 (3,210-5,945) |

Nothing here is a recommendation: it is the arithmetic of the data and the cited prices. Impacts are upper bounds transferred from other cities except where status=measured_athens (see README). The non-default comparison across interventions is `--rank-by people_per_eur`.
