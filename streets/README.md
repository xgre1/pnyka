# Street / site canopy for the Municipality of Athens

STATUS: **sites done; streets NOT done.** The OpenStreetMap download was blocked (see Failures), so `streets.geojson`, `streets.csv` and `streets_by_name.csv` do not exist. `scripts/streets.py` is written and was smoke-tested only on one synthetic street; it has never run on real OSM data.

## Files
- `sites.csv`, `sites.geojson`: 583 sites inside the 144 neighbourhood polygons (397 schools, 72 nurseries, 89 playgrounds, 25 Λέσχες Φιλίας). Fields: site_type, name, category, address, dk, neighbourhood, lat, lon, canopy_pct_150m, canopy_pct_50m, est_trees_50m. 4 of 401 school points fall outside all polygons and are excluded (matches neighbourhoods.csv: 397).
- `scripts/`: common.py (parameters, raster helpers), sites.py, validate_trees_neighbourhoods.py, sensitivity_natgarden.py, streets.py (untested on real data), overpass_query.txt (the queries to run once Overpass is reachable: `python streets.py ways.json trees.json`).

## Method
- Raster: Meta canopy height model `meta_chm_athens.tif`, uint8 metres, EPSG:3857, 1.194 m pixel (about 0.94 m on the ground at 38N), 0 = no canopy, max 41. Canopy = pixel height >= 3 m. Pixel-centre rule.
- Buffers are true metric circles (built in EPSG:2100, then reprojected to 3857), so the 3857 scale distortion is handled.
- Site coordinates: City of Athens layers in `/tmp/athens_prep/layers` (EPSG:2100) reprojected to WGS84 with pyproj. Neighbourhood = smallest containing polygon. Per-neighbourhood counts match neighbourhoods.csv exactly (0 mismatches in all four layers).
- est_trees: local maxima of the Gaussian-smoothed CHM (sigma 0.5 px), 5x5 pixel window (about 4.7 m), height >= 3 m, counted within the buffer. It is an ESTIMATE: touching crowns merge, trees in adjacent private yards inside the buffer are counted, understorey trees are invisible, and integer-metre plateaus can create spurious maxima.
- Street plan (not executed): OSM named highways (primary, secondary, tertiary, residential, living_street, pedestrian, unclassified, trunk), clipped to polygons, 12 m buffer each side, same canopy/tree metrics, plus mapped OSM natural=tree / tree_row points inside the buffer.

## Validation
- Neighbourhood canopy from my own raster pass vs `metachm_ge3m_pct` in treecover_by_neighbourhood.csv: n=144, correlation 1.0000, mean absolute difference 0.0002 percentage points (max 0.0005). Same method, so this checks the pipeline, not the model.
- Tree counts vs National Garden inventory (cityg_dendra, 6,354 points: 4,622 Existing, 1,722 New, 10 Cut), over the convex hull of the points (16.8 ha, 76.6% canopy):
  - sigma 0.5, window 5 px (used): 4,022 maxima = 0.87 of Existing, 0.63 of all points.
  - Window sensitivity at sigma 0.5: 3 px 5,408; 5 px 4,022; 7 px 3,213; 9 px 2,673.
  - Smoothing sensitivity (5 px window): sigma 0 31,780 (noise); 0.5 4,022; 1.0 340 (0.07 of Existing); 2.0 199.
  - CAVEAT: sigma 0.5 was chosen because it is the lightest smoothing that gives sane results, and it matches this garden reasonably well, but the choice was informed by this one test site, so 0.87 is not independent. The National Garden is a dense multi-layer park (about 275 trees/ha, much of it under canopy), unlike open street trees. Treat est_trees as an order-of-magnitude index; the ratio could be different on streets. Tree-lined versus bare street sanity checks were NOT done (no OSM).
- Percentages all within 0-100; site coordinates lat 37.951-38.032, lon 23.700-23.777 (inside the bbox).

## Caveats
- Meta/WRI 1 m canopy height model derives from satellite imagery of roughly 2018-2020 (my recollection of their documentation; I could not verify the exact acquisition years in this session). Newer or removed trees are not reflected.
- Buffers include private gardens, courtyards and parks adjacent to the site/street, not only public street trees.
- Narrow streets shaded by buildings, and tall buildings in the imagery, can degrade the model (omitted trees, or building edges mistaken for canopy).
- Canopy cover in the city is low (median school: 4.0% within 150 m), so small absolute differences matter.

## Failures
- Overpass API: all four hosts (overpass-api.de, overpass.kumi.systems, overpass.private.coffee, maps.mail.ru) were refused by the shell tool before any request was sent ("needs the operator's OK, host not on the web allowlist"; no HTTP status because no connection was made). Not retried via other tools, to avoid bypassing the allowlist. To finish streets: allow one host, download with overpass_query.txt, run streets.py.

## Streets: run on real OSM data (21 Nov 2026) and what the result is worth

Source: OpenStreetMap via Overpass API (overpass-api.de), 20,983 named street ways and 3,980 mapped trees in the Athens bbox, © OpenStreetMap contributors, ODbL. Raw responses are in `osm/`.

Result: 3,074 street names, 925.9 km of centreline inside the 144 neighbourhoods.

**Do not use `est_trees` or `trees_per_100m` as tree counts.** The method finds 14,121 trees along all streets. The City reports 93,891 street trees (CNN Greece, 8 Feb 2026). The method therefore detects roughly 15% of them. Small street trees (narrow crowns, under or near 3 m) are not resolved by the 1.2 m canopy model, and the 0.87 ratio at the National Garden does not transfer to streets.

**`canopy_pct_12m` is usable only as a relative index, and is biased low on wide avenues.** The buffer is 12 m either side of the OSM centreline. On divided or very wide avenues (Μεσογείων, Κηφισίας, Συγγρού, Βασιλίσσης Σοφίας, Πατησίων) the pavement trees fall outside or at the edge of the buffer, and each carriageway is a separate OSM way, so length is roughly doubled. Rankings among ordinary residential streets look plausible (Ηρώδου Αττικού 24.8%, Διονυσίου Αρεοπαγίτου 24.9%, Φωκίωνος Νέγρη 14.4%, Αθηνάς 0.3%).

Streets sharing a name in different parts of the city are merged in `streets_by_name.csv`; use `streets.csv` (name within neighbourhood) to keep them apart.

OSM has 3,980 mapped trees for the whole bbox, so it cannot serve as an inventory either.
