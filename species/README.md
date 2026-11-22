# Athens street-tree reference data (sourced)

Compiled 2026-11-21. Data only, no app. All files in this folder.

| File | What it is |
|---|---|
| species.csv | 24 taxa. One row per species. Each attribute has a `<attribute>` column and a `<attribute>_source` column (URL plus, where available, the quote the value is based on). Empty cell = no fetched source stated it. |
| planting_rules.md | Hard rules from the City Green Regulation (articles and pages, Greek quotes), the City 2020 planting study, the ΕΛΟΤ planting spec, and City officials' statements. |
| alternatives.md | Evidence on hedges, green walls and trees in street canyons (Abhijith 2017, GLA 2019, Surrey toolkit and press release) with numbers and conditions. |

## How it was compiled

1. Downloaded each document and extracted the full text (pdftotext, or HTML-to-text for web pages). Page images were read where the PDF text layer was garbled (ΕΛΟΤ spec).
2. City of Athens documents were given priority. Where a City document states an attribute (e.g. height, drought tolerance, shade, pit size in the 2020 study), the City value is used and sourced to it.
3. Remaining attributes were collected by three research passes using NC State Extension Plant Toolbox, RHS, Oregon State, Wikipedia (last resort, marked), Cariñanos & Marinangeli 2021 (allergenicity, Urban Forestry & Urban Greening), EPPO (Robinia in Greece), a Stagira plant list (Cercis, Olea). Their fetch tool returns summarised page text, so quotes can be paraphrased. I re-fetched every cited URL and checked that the quote text occurs in the raw page: 153 of 172 quotes matched; the remaining 19 are listed per row in column `quotes_not_machine_verified` (mostly table-row transcriptions or "Drought (listed under Resistance To Challenges)" style notes, not necessarily wrong). Treat those as lower confidence. A match shows the quote exists on the page, not that unit conversions (ft to m) were re-checked.
4. English and Greek common names are labels. Greek names are taken from the City documents as written (e.g. «νεραντζιά», «ροβίνια»). Scientific names for City-named common names (e.g. Morus sp., "πεύκα", "άριες", "ιβίσκοι", "πλατάνια") are an identification step: the City documents do not name the species, and each such row says so in `city_of_athens_status`.
5. Species list = species the City names as planted/present (CNN Feb 2026, Athens Voice 2022, SKAI 2022, iefimerida 2024, CNN 2023, in.gr 2026, 2020 study) plus Celtis australis (no City source; row has `has_city_source = no`). "How many rows have a City source": 23 of 24.

## Sources and access

Access date for everything: 2026-11-21. READ = full text opened and read. HTTP codes are those returned by curl/WebFetch.

| Source | URL | Status |
|---|---|---|
| City of Athens Green Regulation 2024 (44 pp) | https://www.cityofathens.gr/wp-content/uploads/2024/06/kanonismos-gia-to-dimotiko-prasino.pdf | 200, READ in full. Note blank ratification number "ΑΔΣ ……/2024" |
| CNN Greece 2026-02-08 | https://www.cnn.gr/ellada/story/518561/athina-pos-epilegontai-ta-dentra-stis-nees-fyteyseis-giati-xanontai-xiliades | 200, READ in full |
| City phytotechnical study, Plateia Theatrou, Dec 2020 | https://www.cityofathens.gr/wp-content/uploads/2021/10/2.-20201214_fytotexnika.pdf | 200, READ in full |
| Athens Voice 2022-12-07, interview with Green Dept head | https://www.athensvoice.gr/life/life-in-athens/781659/ti-dedra-theloume-stin-athina/app/ | 200, READ (text extract of the article) |
| iefimerida 2024-10-04 (Doukas, Apostolopoulos) | https://www.iefimerida.gr/ellada/h-doykas-prasinizoyme-tin-athina | 200, READ (extract lost some link text) |
| SKAI 2022-07-04 | https://www.skai.gr/news/environment/athina-fyteytikan-apo-3700-dentra-mesa-se-25-xronia | 200, READ (the in-text species list appears in the page) |
| CNN 2023-11-08 (Metro transplants) | https://www.cnn.gr/politiki/story/390604/dimos-athinaion-promitheyetai-2-975-nea-dentra-sto-plaisio-tis-synergasias-gia-to-metro | 200, READ (extract; some lines lost) |
| CNN 2025-07-10 (planting actions) | https://www.cnn.gr/ellada/story/485979/nees-dendrofyteyseis-kai-symmetoxikes-draseis-ston-dimo-athinaion | 200, READ; shrubs only (bougainvillea, myrtle, rosemary), no tree species used |
| in.gr 2026-02-20 (Alsos Ilision) | https://www.in.gr/2026/02/20/politics/aftodioikisi/dimos-athinaion-500-nea-dentra-sto-alsos-ilision/ | 200, READ; the text says "Απ’ την αρχή του 2024", so the real date is uncertain |
| ΕΛΟΤ ΤΠ 1501-10-05-01-00:2009 | https://sate.gr/html/pdfDocuments/10-05-01-00.pdf | 200; pages 8-9 READ as images (text layer garbled); other pages not read |
| ΕΛΟΤ ΤΠ 1501-10-05-09-00 (staking), 05-08-00 (transplanting) | https://sate.gr/html/pdfDocuments/10-05-09-00.pdf, .../10-05-08-00.pdf | 200, downloaded, NOT used (garbled text, not read) |
| ΕΛΟΤ 1501-10-05-02-00 | https://sate.gr/html/pdfDocuments/10-05-02-00.pdf | 404 |
| Athens trees tracker | https://athenstrees.cityofathens.gr/ | 200, JavaScript shell only, no data |
| Abhijith et al. 2017, accepted manuscript | https://researchrepository.ucd.ie/rest/bitstreams/26234/retrieve | 200, READ in full |
| Abhijith et al. 2017, publisher | https://www.sciencedirect.com/science/article/pii/S1352231017304855 | 403 |
| GLA 2019 | https://www.london.gov.uk/sites/default/files/green_infrastruture_air_pollution_may_19.pdf | 200, READ in full (other guessed URLs 404; core.ac.uk copies 403) |
| Surrey Urban Greening toolkit (air pollution) | https://www.surrey.ac.uk/sites/default/files/2025-12/Urban-Greening-How-To-Digital-Toolkit-AIR-POLLUTION.pdf | 200, READ in full |
| Surrey press release on hedge field study | https://www.surrey.ac.uk/news/hedges-reduce-pollution-breathing-height-shallow-street-canyons-study-confirms | 200, READ |
| Species attribute pages (NC State, RHS, Oregon State, Wikipedia, Cariñanos 2021, EPPO, EUFORGEN, Stagira list, VT, UConn etc.) | URLs are in each `_source` cell | Fetched by sub-team; quotes re-checked against raw pages (see step 3) |
| Failed for species attributes | POWO/Kew (403), Missouri Botanical Garden (403 / certificate error), SelecTree (JS only, empty), UF/IFAS (redirect loop), floraofgreece.upatras.gr (DNS failure), cybertaxonomy Flora of Greece / Euro+Med (bot block), NC State pages for P. halepensis, Q. ilex, C. australis (404/403), JRC and Hellenic Plant Protection Journal PDFs (unreadable) | not used |

Search-engine snippets only (NOT read in the source document, not used for any value): iefimerida headline (later READ), a claim in a search summary that "κουτσουπιά" is Celtis (wrong: it is Cercis; ignored), Surrey press releases other than the hedge one, Tomson 2021 and Kumar 2022 paper abstracts, the ΕΤΕΠ Chalandri/Patras/Larissa municipal tender specs (not opened).

## Gaps (explicit)

- **No species list in the Regulation.** The Green Regulation names no approved, recommended or forbidden species. No pit size, spacing, or distances to buildings/utilities for new planting either. "City plants/recommends/avoids" comes only from officials' statements, press releases and one City design study, not from a rule. The only "avoid" signals found: olives not planted on sidewalks (fruit slip, Athens Voice 2022), mulberry pest problem (not an avoid), palms (designers' opinion, not the City).
- **Tree registry:** Regulation Art. 17 only states that a "Ειδικό Μητρώο Δέντρων" is established. No fields, deadline or data located. CNN Feb 2026: still "planned" ("σχεδιάζει"). The athenstrees site could not be read.
- **Sidewalk minimum:** sources conflict (Regulation 1.00/1.50 m thresholds for replanting; Green Dept head quoted at 2.20 m in 2022 and 1.50 m free path in 2026). The underlying code articles were not retrieved.
- **ΕΛΟΤ/ΕΤΕΠ:** only pit-size section read. Spacing, distances, soil volume not found. ΕΛΟΤ 05-09/05-08 not read.
- **Species attributes, empty for all or nearly all rows:** shade quality (only Morus, Albizia from the City study), heat tolerance, water need after establishment, suitability for narrow streets, suitability under overhead wires (only Acer campestre), most canopy widths for species other than those in NC State, and any Greek-source (university/ELGO/Forest Service) data. No Greek university or ELGO-Dimitra source with attributes was found in the fetches that worked.
- **Pests named in the brief not sourced:** Ceratocystis platani on plane (only generic canker noted for P. x acerifolia), red palm weevil, pine processionary: no fetched page supported these for the relevant species, so cells are empty or generic. Confirm before showing.
- **Allergenicity:** from Cariñanos & Marinangeli 2021 (VPA scale) for 8 rows plus OPALS for Acer campestre (Wikipedia). Other rows empty. OPALS not used elsewhere.
- **Native status:** mostly Wikipedia or generic regional statements; no Euro+Med or Flora of Greece page could be fetched. For Pinus pinea the native range is "highly debated" per Wikipedia.
- **Species identity:** Platanus (orientalis vs x acerifolia), Pinus (halepensis vs pinea), Morus (alba?), Hibiscus (syriacus?), Phoenix/Washingtonia, Quercus ilex ("άριες"), Tamarix species are not specified by the City. Rows for these are candidates, not confirmed City species.
- **Athens Climate Adaptation / Resilience documents and Gewponiko/ΑΠΘ/ΕΛΓΟ publications:** not found or not opened in this session.
- **Hedge/green-wall evidence** is from London, Guildford, Shanghai and modelling studies; none from Athens or the Mediterranean.
