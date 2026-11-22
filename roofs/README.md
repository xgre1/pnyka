# roofs/: is each public roof green, bright or ordinary today?

For each school and municipal building already matched in `capacity/facility_to_building_matches.csv`, this folder measures the roof in Sentinel-2 summer 2025 imagery. It records NDVI and broadband albedo and gives the roof a status: `green` (NDVI >= 0.30), `bright` (albedo in the top 10% of the municipality's measurable roofs, cut 0.325), `ordinary`, or `too_small` (fewer than 4 pixels of 10 m inside the polygon shrunk by 5 m). The results, sensitivity, validation and limits are in `summary.md`.

## Files
- `roof_status.csv`: one row per matched facility point, so a building shared by several facilities appears on several rows.
  - Columns: `layer, name, bldg_idx, roof_m2, n_pixels, ndvi, albedo, status, lat, lon, neighbourhood` (= `bldg_nb`), `neighbourhood_name`.
  - Check columns: `inside_muni, match, point_order_in_layer, min_valid_scenes`, and the same values without the SCL mask (`*_nomask`).
- `summary.md`: the results.
- `work/`: small logs (`buildings_check.txt`, `scenes_used.json`, `thresholds*.json`, `validation_cap2022.csv`) and the shrink-sensitivity tables (`roof_status_shrink2.5.csv`, `roof_status_shrink0.csv`).
- `scripts/`: the scripts, to run in order.

## Rerun (about 5 minutes; the composite download is the slow step)
```
V=<venv with numpy rasterio shapely pyproj pandas tabulate>/bin/python
WK=<scratch dir outside the repo>      # holds the composite .npz (~30 MB) and all_roofs_stats.csv.gz
$V -I roofs/scripts/01_check_buildings.py $PWD          # bldg_idx order check
$V -I roofs/scripts/02_composite.py $PWD $WK            # STAC GET search + median composite
$V -I roofs/scripts/03_roofs.py $PWD $WK                # method (shrink 5 m) -> roof_status.csv
$V -I roofs/scripts/03_roofs.py $PWD $WK 2.5            # sensitivity only
$V -I roofs/scripts/03_roofs.py $PWD $WK 0              # sensitivity only
$V -I roofs/scripts/04_summary.py $PWD $WK              # tables + CAP 2022 validation
```

## Sources
- Buildings: City of Athens solar map `cityg_c40solarmap` (GeoServer `gis.cityofathens.gr`; CKAN «Solar Map»), local copy `raw/treecover/dl/cityg_c40solarmap.json.gz`.
- Imagery: Sentinel-2 L2A COGs, Earth Search v1 STAC (https://earth-search.aws.element84.com/v1), tile 34SGH, 20 scenes from June to August 2025.
- Albedo: Bonafoni & Sekertekin 2020, IEEE GRSL 17(9):1618-1622, doi:10.1109/LGRS.2020.2967085. We read the coefficients in a citation of the paper (Lund University thesis, Table 4.3), not in the paper itself.
- Validation: City of Athens Climate Action Plan 2022, p. 52 (13 school green roofs, 6,475 m2).
- Facility points and matching: `capacity/` (see `capacity/README.md`).
