#!/usr/bin/env python
"""Community / municipality / low-tree-group aggregation, summary.md and metrics_dictionary.csv.
Run after 01_compute_capacity.py (reads /tmp/athens_capacity/nb.pkl and capacity/validation.json)."""
import json, re
import numpy as np, pandas as pd

OUT = '.'
nb = pd.read_pickle('/tmp/athens_capacity/nb.pkl')
V = json.load(open(OUT + 'validation.json'))

RATIO = {  # recomputed after summing
    'roof_share_of_area_pct': lambda d: 100 * d.roof_area_m2 / d.area_m2,
    'roof_solar_usable_share_pct': lambda d: 100 * d.roof_solar_usable_m2 / d.roof_area_bldg_assigned_m2,
    'street_area_est_share_pct': lambda d: 100 * d.street_area_est_m2 / d.area_m2,
    'street_density_km_per_km2': lambda d: d.street_len_total_m / 1000 / d.area_km2,
    'chm_ge3m_pct': lambda d: 100 * d.canopy_chm_ge3m_m2 / d.area_m2,
    'stl2018_pct': lambda d: 100 * d.stl2018_canopy_m2 / d.area_m2,
}
skip = {'name', 'community', 'community_id', 'area_km2_source', 'chm_valid_pixel_pct', 'residual_negative_flag',
        'low_tree_group_stl_lt2pct', 'chm_csv', 'stl_csv'}
sumcols = [c for c in nb.columns if c not in skip and c not in RATIO and pd.api.types.is_numeric_dtype(nb[c])]


def agg(d, label, rtype):
    r = {'row_type': rtype, 'unit': label, 'n_neighbourhoods': len(d)}
    for c in sumcols: r[c] = d[c].sum()
    t = pd.DataFrame([r])
    for c, f in RATIO.items(): r[c] = float(f(t).iloc[0])
    r['n_residual_negative_neighbourhoods'] = int(d.residual_negative_flag.sum())
    return r


rows = [agg(nb[nb.community_id == k], f'{k}η ΔΚ', 'community') for k in sorted(nb.community_id.unique())]
rows.append(agg(nb, 'MUNICIPALITY OF ATHENS', 'municipality'))
low = nb[nb.low_tree_group_stl_lt2pct]
rows.append(agg(low, 'GROUP stl2018 tree cover <2% (62 neighbourhoods)', 'group_low_tree'))
rows.append(agg(nb[~nb.low_tree_group_stl_lt2pct], 'REST (stl2018 >=2%)', 'group_rest'))
C = pd.DataFrame(rows)
front = ['row_type', 'unit', 'n_neighbourhoods']
C = C[front + [c for c in C.columns if c not in front]]
C.to_csv(OUT + 'capacity_by_community.csv', index=False, float_format='%.3f')
M = C[C.row_type == 'municipality'].iloc[0]; L = C[C.row_type == 'group_low_tree'].iloc[0]

# deficit netted at municipality level (for contrast with the sum of per-neighbourhood floors)
net = {t: max(0, M.area_m2 * t / 100 - M.canopy_chm_ge3m_m2) for t in (5, 10, 15, 30)}


def f0(x): return f'{x:,.0f}'


def tbl(r):
    L_ = []
    def a(k, lab, u, v): L_.append(f'| {lab} | {v} | {u} |')
    a(0, 'Area', 'km2', f'{r.area_km2:,.2f}')
    a(0, 'Neighbourhoods', 'n', int(r.n_neighbourhoods))
    a(0, 'Population (pop_total)', 'persons', f0(r.pop_total))
    a(0, 'Buildings (solar-map polygons, rep. point inside)', 'n', f0(r.buildings_n))
    a(0, 'Roof footprint (geometry, clipped)', 'm2', f0(r.roof_area_m2))
    a(0, 'Roof share of area', '%', f'{r.roof_share_of_area_pct:.1f}')
    a(0, 'Solar-usable roof area (City model USAB_AREA)', 'm2', f0(r.roof_solar_usable_m2))
    a(0, 'Solar-usable share of roof footprint', '%', f'{r.roof_solar_usable_share_pct:.1f}')
    a(0, 'School roof (matched buildings, lower bound)', 'm2', f0(r.schools_roof_area_m2))
    a(0, 'Municipal non-school facility roof (matched, lower bound)', 'm2', f0(r.municipal_other_roof_area_m2))
    a(0, 'Street length (OSM named streets)', 'km', f'{r.street_len_total_m/1000:,.1f}')
    a(0, ' of which pedestrian + living_street', 'km', f'{r.street_len_pedestrian_and_living_m/1000:,.1f}')
    a(0, 'Street surface ESTIMATE (carriageway+pavement)', 'm2', f'{f0(r.street_area_est_m2)} (range {f0(r.street_area_est_low_m2)} to {f0(r.street_area_est_high_m2)})')
    a(0, 'Green/open union net of roofs (zoning + UA2012 green/sport/natural)', 'm2', f0(r.green_open_union_net_of_roofs_m2))
    a(0, ' zoned green (City zoning, union)', 'm2', f0(r.green_zoning_m2))
    a(0, ' UA2012 green urban areas', 'm2', f0(r.ua2012_green_urban_m2))
    a(0, ' UA2012 sports & leisure', 'm2', f0(r.ua2012_sports_leisure_m2))
    a(0, 'Residual (not roof, not green, not est. street) - raw', 'm2', f0(r.residual_unclassified_raw_m2))
    a(0, 'Residual floored at 0 per neighbourhood, summed', 'm2', f0(r.residual_open_m2))
    a(0, 'Canopy, Meta CHM >=3 m', 'm2 / %', f'{f0(r.canopy_chm_ge3m_m2)} / {r.chm_ge3m_pct:.1f}')
    a(0, 'Tree canopy, Street Tree Layer 2018', 'm2 / %', f'{f0(r.stl2018_canopy_m2)} / {r.stl2018_pct:.1f}')
    for t in (5, 10, 15, 30):
        a(0, f'Canopy deficit to {t}% (sum of per-neighbourhood floors)', 'm2', f0(r[f'canopy_deficit_to_{t}pct_m2']))
    for t in (10, 30):
        a(0, f'Illustrative trees for {t}% target, crown 4/6/8 m', 'trees', ' / '.join(f0(r[f'illustr_trees_{t}pct_crown{d}m']) for d in (4, 6, 8)))
    a(0, 'Trees planted since 2024 (num_trees; rows)', 'trees', f'{f0(r.plantings_since_2024_trees)} ({f0(r.plantings_since_2024_rows)} rows)')
    for k, lab in [('schools', 'Schools'), ('nurseries', 'Nurseries'), ('playgrounds', 'Playgrounds'), ('elderly_clubs', 'Elderly clubs (Λέσχες Φιλίας)')]:
        a(0, f'{lab}: total / with canopy_pct_150m < 5', 'n', f'{int(r[f"sites_{k}_n"])} / {int(r[f"sites_{k}_canopy150m_lt5pct_n"])}')
    return '| Quantity | Value | Unit |\n|---|---|---|\n' + '\n'.join(L_)


def top(col, n=15, extra=()):
    d = nb.sort_values(col, ascending=False).head(n)
    cols = ['name', 'community', 'area_km2', col] + list(extra)
    return d[cols].to_markdown(index=False, floatfmt=',.0f') if hasattr(d, 'to_markdown') else d[cols].to_string(index=False)


try:
    import tabulate  # noqa
except Exception:
    pd.DataFrame.to_markdown = lambda self, index=False, floatfmt='': (
        '| ' + ' | '.join(self.columns) + ' |\n|' + '---|' * len(self.columns) + '\n' +
        '\n'.join('| ' + ' | '.join(((f'{v:,.2f}' if abs(v) < 100 else f'{v:,.0f}') if isinstance(v, float) else str(v)) for v in row) + ' |' for row in self.itertuples(index=False)))

ms, mo = V['match_schools'], V['match_municipal_other']
spot = [nb.sort_values('roof_area_m2').iloc[-1].name, nb[nb.low_tree_group_stl_lt2pct].sort_values('area_m2').iloc[-1].name,
        nb[~nb.low_tree_group_stl_lt2pct].sort_values('area_m2').iloc[len(nb[~nb.low_tree_group_stl_lt2pct]) // 2].name]
spotcols = ['name', 'community', 'area_km2', 'buildings_n', 'roof_area_m2', 'roof_share_of_area_pct', 'roof_solar_usable_m2', 'schools_roof_area_m2',
            'street_len_total_m', 'street_area_est_m2', 'green_open_union_net_of_roofs_m2', 'residual_unclassified_raw_m2', 'canopy_chm_ge3m_m2',
            'chm_ge3m_pct', 'stl2018_pct', 'canopy_deficit_to_10pct_m2', 'illustr_trees_10pct_crown6m', 'sites_all4_n', 'sites_all4_canopy150m_lt5pct_n']
sp = nb.loc[spot, spotcols].copy()
for c in sp.columns:
    if sp[c].dtype == float: sp[c] = sp[c].round(1)
sptxt = '\n'.join(f'- **{r["name"]}** ({r["community"]}): ' + '; '.join(f'{k}={r[k]}' for k in spotcols[2:]) for _, r in sp.iterrows())

md = f"""# Capacity summary - Municipality of Athens

All areas in m2 (EPSG:2100), lengths in m. Quantities are MEASURED footprints/lengths/areas from City and open layers; they are NOT usable/installable capacity. See README.md for method and caveats. Computed 2026-11-21 by `scripts/01_compute_capacity.py`.

## Municipality totals

{tbl(M)}

Canopy deficit netted at municipality level (area x target - existing, one number) for contrast: 5% = {f0(net[5])}, 10% = {f0(net[10])}, 15% = {f0(net[15])}, 30% = {f0(net[30])} m2. The per-neighbourhood sums above are larger because a neighbourhood already above target does not offset another.

Facility matching (points to solar-map building polygons; contained, else nearest within 30 m):

| Group | Points (in municipality) | Contained | Nearest <=30 m | Unmatched | Unique buildings | Roof m2 (matched, lower bound) | Roof m2 (all buildings within 30 m, upper bound) |
|---|---|---|---|---|---|---|---|
| Schools | {ms['points']} | {ms['contained']} | {ms['nearest30']} | {ms['unmatched']} | {ms['unique_buildings']} | {f0(ms['roof_area_matched_m2'])} | {f0(ms['roof_area_upper_bound_all_bldgs_within_30m_m2'])} |
| Municipal non-school (nurseries, clubs, clinics, admin, services) | {mo['points']} | {mo['contained']} | {mo['nearest30']} | {mo['unmatched']} | {mo['unique_buildings']} | {f0(mo['roof_area_matched_m2'])} | {f0(mo['roof_area_upper_bound_all_bldgs_within_30m_m2'])} |

Match rate (contained or within 30 m): schools {100*(ms['points']-ms['unmatched'])/ms['points']:.1f}% (contained only {100*ms['contained']/ms['points']:.1f}%), municipal non-school {100*(mo['points']-mo['unmatched'])/mo['points']:.1f}% (contained only {100*mo['contained']/mo['points']:.1f}%). Ambiguity: {ms['points_with_gt1_bldg_within_30m']} of {ms['points']} school points and {mo['points_with_gt1_bldg_within_30m']} of {mo['points']} municipal points have more than one building within 30 m; {ms['points_sharing_building']} school points share a building with another school point (co-located schools), so unique buildings < points. A school is usually several buildings, so matched area is a lower bound and the within-30 m area an upper bound (it includes neighbours). The City has no full municipal-building register on disk or on the WFS; "municipal non-school" is built from facility point layers only.

## Group: neighbourhoods with Street Tree Layer 2018 cover <2% ({int(L.n_neighbourhoods)} neighbourhoods)

{tbl(L)}

## Top 15 neighbourhoods by roof footprint (m2)

{top('roof_area_m2', 15, ('roof_share_of_area_pct', 'schools_roof_area_m2'))}

## Top 15 neighbourhoods by canopy deficit to 10% (m2, Meta CHM >=3 m)

{top('canopy_deficit_to_10pct_m2', 15, ('chm_ge3m_pct', 'illustr_trees_10pct_crown6m'))}

(illustr_trees_10pct_crown6m = illustrative arithmetic: deficit / crown area of a 6 m crown, not a planting plan.)

## Validation

- Sum of neighbourhood areas: {V['sum_area_km2_geometry']:.3f} km2 from geometry ({V['sum_area_km2_source_attr']:.3f} km2 from the `area_km2` attribute); overlap between polygons {V['neighbourhood_overlap_km2']:.1e} km2. Target ~38.0: OK.
- Roof footprint {f0(M.roof_area_m2)} m2 = {M.roof_share_of_area_pct:.1f}% of the municipality area (maximum neighbourhood {V['max_roof_share_pct']:.1f}%; {V['n_roof_share_gt100']} neighbourhoods >100%). Reported as computed. Streets are separately ~{M.street_area_est_share_pct:.0f}% (estimate) and green/open net of roofs ~{100*M.green_open_union_net_of_roofs_m2/M.area_m2:.0f}%.
- Solar-map polygon area: geometry sum {V['solar_sum_geom_area_m2_all']:,.0f} m2 vs layer attribute `Area` {V['solar_sum_attr_Area_m2_all']:,.0f} m2 (median ratio {V['solar_attr_Area_over_geom_median']:.6f}): the attribute is just the planimetric footprint.
- Building count: layer has {V['solar_features']:,} features; {V['solar_features_intersecting_municipality']:,} intersect the municipality, {V['solar_features_repoint_inside_municipality']:,} have their representative point inside (= sum of buildings_n {V['buildings_n_sum']:,}); {V['solar_features_repoint_outside']:,} lie outside the municipal polygons. The {V['solar_features_intersecting_municipality']-V['solar_features_repoint_inside_municipality']} straddling buildings are the difference. Roof area by clipped geometry vs whole-building assignment differs by {V['roof_bldg_assigned_vs_clipped_diff_m2']:.0f} m2 in total.
- Overlapping solar-map polygons: sum minus union = {V['buildings_overlap_m2']:,.0f} m2 ({100*V['buildings_overlap_m2']/V['solar_sum_geom_area_m2_all']:.2f}% of area) - negligible double counting.
- Canopy: recomputed CHM % and STL % differ from `treecover/treecover_by_neighbourhood.csv` by at most {V['chm_pct_max_abs_diff_vs_treecover_csv']:.4f} and {V['stl_pct_max_abs_diff_vs_treecover_csv']:.4f} percentage points (rounding). Low-tree group size {V['n_low_tree_group']} (expected 62).
- Community assignment: municipal_district_id agrees with the City community polygon layer for {V['community_id_agrees_with_dk_polygon_layer']} neighbourhoods (centroid test; the one difference is a boundary case).
- Sites: {V['sites_rows']} sites, all inside; csv neighbourhood field vs point-in-polygon mismatches: {V['sites_neighbourhood_field_mismatch_vs_point_in_polygon']}. Plantings: {V['plantings_rows_since_2024']:,} rows / {V['plantings_trees_since_2024']:,} trees dated 2024-01-01 or later (file spans {V['plantings_date_min']} to {V['plantings_date_max']}); {V['plantings_rows_outside_municipality']} rows fall outside the neighbourhood polygons and are not counted per neighbourhood.
- Street residual: {V['n_residual_negative']} neighbourhoods have a negative raw residual (roof + green + street estimate > area), i.e. the street-width defaults overshoot there; they are floored at 0 in `residual_open_m2` and flagged.
- Urban Atlas road cross-check NOT possible for 2012: the downloaded UA2012 has no road class (the 133 km2 "Other roads" polygon failed to download) and covers only {V['ua2012_coverage_of_municipality_pct']:.0f}% of the municipality. UA2010 (City-hosted, covers {V['ua2010_coverage_of_municipality_pct']:.0f}%) has {V['ua2010_road_polygons']} road polygons totalling {f0(M.ua2010_road_land_m2)} m2 = {100*M.ua2010_road_land_m2/M.area_m2:.0f}% of the area, versus {M.street_area_est_share_pct:.0f}% ({f0(M.street_area_est_m2)} m2) from the OSM width estimate. The UA2010 figure lies inside the estimate's +-30% band ({f0(M.street_area_est_low_m2)} to {f0(M.street_area_est_high_m2)} m2), which is mild support for the estimate's order of magnitude only: different definition (UA 'other roads and associated land' polygons with a 0.25 ha minimum unit, includes verges/interchanges), different year (2010), and not available per neighbourhood in a comparable form.
- OSM: {V['osm_ways']:,} named ways, {V['osm_total_length_m']/1000:,.0f} km in the extract of which {V['osm_length_outside_municipality_m']/1000:,.0f} km lie outside the municipality (metropolitan extract); {(V['osm_total_length_m']-V['osm_length_outside_municipality_m'])/1000:,.0f} km inside. Width tag on {V['osm_length_share_width_tag_pct']:.1f}% and lanes tag on {V['osm_length_share_lanes_tag_pct']:.1f}% of length.

### Spot checks

{sptxt}
"""
open(OUT + 'capacity_summary.md', 'w').write(md)

# ------------------------------------------------------------ metrics dictionary
SRC = {
    'solar': 'City of Athens Solar Map layer cityg_c40solarmap (66,661 building polygons; raw/treecover/dl/cityg_c40solarmap.json.gz). Layer date not stated in the data; downloaded 2026-11-21',
    'osm': 'OpenStreetMap named street ways, Overpass snapshot 2026-11-21 (streets/osm/osm_named_streets_athens.json.gz)',
    'zon': 'City zoning layer xriseis (GPS FEK 80D/88 + amendments), green classes only (registry/gis/xriseis_green_only.geojson); layer date not stated',
    'ua12': 'Copernicus Urban Atlas 2012 land use, prod_date 2020-11 (raw/treecover/dl/ua2012.geojson); 83% of municipality covered, no road class',
    'ua10': 'Urban Atlas 2010 hosted by City (raw/treecover/dl/cityg_angLST_Athens_UrbanAtlas.json), 2010',
    'stl': 'Copernicus Urban Atlas Street Tree Layer 2018 (raw/treecover/dl/stl2018.geojson.gz), 2018',
    'chm': 'Meta/WRI canopy height model, 1.19 m, EPSG:3857, imagery ~2018-2020 (raw/treecover/dl/meta_chm_athens.tif)',
    'pts': 'City facility point layers (raw/gis/layers schools, nurseries, friendship, clinics; WFS geonode:kt_dioikisis and geonode:pois_yperesies_da fetched 2026-11-21); layer dates mostly not stated (nurseries update field 2018-12-24)',
    'plant': 'athenstrees/plantings_points.csv (dates 2001-03-02 to 2026-11-19; filtered planting_date >= 2024-01-01)',
    'sites': 'streets/sites_with_plantings.csv (canopy_pct_150m from Meta CHM >=3 m, see streets/README.md)',
    'pop': 'raw/population/population_by_neighbourhood.csv (pop_total, modelled/estimated; see raw/population/README.md)',
    'nbg': 'neighbourhoods.geojson (City Municipal Neighbourhoods polygons) projected to EPSG:2100',
}
D = {}
def d(col, unit, src, method, err): D[col] = (unit, SRC.get(src, src), method, err)
d('name', 'text', 'nbg', 'neighbourhood name', 'n/a')
d('community', 'text', 'nbg', 'municipal_district_id + "η ΔΚ" (Municipal Community 1-7)', 'agrees with City community polygon layer for 143/144 (1 boundary case)')
d('community_id', 'int', 'nbg', 'municipal_district_id', 'n/a')
d('area_km2_source', 'km2', 'nbg', 'area_km2 attribute of the source file', 'rounded to 4 decimals')
d('area_m2', 'm2', 'nbg', 'polygon area in EPSG:2100', 'planimetric; < 0.1% vs attribute')
d('area_km2', 'km2', 'nbg', 'area_m2 / 1e6', 'as above')
d('roof_area_m2', 'm2', 'solar', 'sum of building polygon area clipped to the neighbourhood, EPSG:2100', 'footprint, not usable roof; polygons overlap by 0.1% of area; includes non-roof structures; polygon geometry positional error unknown (about +-1-2% area assumed, unverified)')
d('buildings_n', 'count', 'solar', 'buildings whose representative point lies in the neighbourhood', 'includes sheds/annexes (see buildings_lt_50m2_n); splits of one building into several polygons inflate the count')
d('roof_area_bldg_assigned_m2', 'm2', 'solar', 'whole-building polygon area assigned by representative point (base of the usable share)', 'differs from roof_area_m2 by 519 m2 in total')
d('roof_area_attr_Area_m2', 'm2', 'solar', 'sum of layer attribute Area, assigned by representative point', 'equals geometry area (ratio 1.000000)')
d('roof_solar_usable_m2', 'm2', 'solar', 'sum of layer attribute USAB_AREA ("usable area" in the City solar model), assigned by representative point', 'definition (irradiation threshold, tilt assumptions) not documented in the layer; it is a solar-PV notion, NOT flat/paintable/green-roof-suitable area; pitched vs flat unknown')
d('solar_kwp', 'kWp', 'solar', 'sum of attribute KWP', 'City model output, not validated here')
d('solar_kwh_year', 'kWh/year', 'solar', 'sum of attribute KWH_YEAR', 'City model output, not validated here')
d('buildings_lt_50m2_n', 'count', 'solar', 'buildings with polygon area < 50 m2', 'indicator of small structures')
d('roof_share_of_area_pct', '%', 'solar', '100 x roof_area_m2 / area_m2', 'footprint share only')
d('roof_solar_usable_share_pct', '%', 'solar', '100 x roof_solar_usable_m2 / roof_area_bldg_assigned_m2', 'see roof_solar_usable_m2')
for g, lab in [('schools', 'school points (layer schools.geojson)'), ('municipal_other', 'nurseries + Lesches Filias + clinics + admin buildings + municipal services points')]:
    d(f'{g}_points_n', 'count', 'pts', f'{lab} inside the neighbourhood', 'point layers are incomplete/dated; 4 school points and 2 service points lie outside the municipality and are excluded')
    d(f'{g}_points_matched_n', 'count', 'pts', 'points matched to a building polygon (contained, else nearest within 30 m)', 'a point may fall in a courtyard or on a neighbouring building; see facility_to_building_matches.csv')
    d(f'{g}_buildings_n', 'count', 'pts', 'unique matched building polygons (points sharing a building counted once)', 'one facility is often several buildings, so this is a lower bound')
    d(f'{g}_roof_area_m2', 'm2', 'pts', 'footprint area of unique matched buildings, assigned to the neighbourhood of the building', 'LOWER bound (main building only); within-30 m upper bound is 3.1x for schools and 5.1x for municipal other at municipality level; matches to neighbours possible')
for h in ['trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential', 'living_street', 'pedestrian']:
    d(f'street_len_{h}_m', 'm', 'osm', f'length of OSM ways highway={h}, split at 10 m and assigned by segment midpoint', 'named streets only (unnamed service roads, footways, steps, cycleways missing); dual carriageways drawn as two ways both counted; completeness of OSM not audited')
d('street_len_total_m', 'm', 'osm', 'sum of the eight classes', 'as above')
d('street_len_pedestrian_and_living_m', 'm', 'osm', 'pedestrian + living_street', 'as above')
d('street_area_est_m2', 'm2', 'osm', 'length x width; width = width tag if numeric (2-40 m, taken as carriageway), else lanes x 3.0 m, else class default; + sidewalks 2x2.0 m (2.0 m for the one-way halves of a dual carriageway); pedestrian/living_street 6 m total unless width tag. Defaults in README.md', 'ESTIMATE, assume +-30%; not measured; sidewalk width is the largest unknown')
d('street_area_est_low_m2', 'm2', 'osm', '0.7 x street_area_est_m2', 'assumed error band, not a statistical interval')
d('street_area_est_high_m2', 'm2', 'osm', '1.3 x street_area_est_m2', 'assumed error band')
d('street_area_defaults_only_m2', 'm2', 'osm', 'same but ignoring width/lanes tags (class defaults only)', 'sensitivity; compare with street_area_est_m2')
d('street_area_est_share_pct', '%', 'osm', '100 x street_area_est_m2 / area_m2', 'as street_area_est_m2')
d('street_density_km_per_km2', 'km/km2', 'osm', 'street_len_total_m / 1000 / area_km2', 'as length')
d('green_zoning_m2', 'm2', 'zon', 'area of union of zoning polygons for green/free-space classes, clipped', 'zoning designation, not actual vegetation; some zoned green is built or paved')
d('ua2012_green_urban_m2', 'm2', 'ua12', 'UA code 14100 clipped', 'reference year 2012; 83% coverage of municipality; minimum mapping unit 0.25 ha')
d('ua2012_sports_leisure_m2', 'm2', 'ua12', 'UA code 14200 clipped', 'as above')
d('ua2012_natural_forest_grass_m2', 'm2', 'ua12', 'UA codes 31000 + 32000 clipped', 'as above')
d('ua2012_vacant_land_m2', 'm2', 'ua12', 'UA code 13400 (land without current use) clipped; NOT included in green_open_union', 'as above')
d('green_open_union_gross_m2', 'm2', 'zon', 'union of zoning green + UA14100 + UA14200 + UA31000/32000, clipped (no double counting)', 'mixes planning and land-cover sources of different years')
d('green_open_union_net_of_roofs_m2', 'm2', 'zon', 'green_open_union_gross minus building footprints', 'as above; mixed sources')
d('ua2010_road_land_m2', 'm2', 'ua10', 'UA2010 codes 12210/12220 clipped', 'only 10 large polygons in 2010; coarse orientation only (municipality total 6.46 km2 vs OSM estimate 8.10 km2); no UA2012 road class available; not reliable per neighbourhood')
d('residual_unclassified_raw_m2', 'm2', 'derived', 'area - roof_area - green_open_union_net_of_roofs - street_area_est', 'RESIDUAL: carries all errors of the three terms; can be negative')
d('residual_open_m2', 'm2', 'derived', 'max(0, residual_unclassified_raw_m2). Courtyards, plots, paved squares, rail, unzoned open land - not verified to be unsealed', 'RESIDUAL, as above; do not read as plantable ground')
d('residual_negative_flag', 'bool', 'derived', 'raw residual < 0', 'indicates over-estimated street width or over-counted green')
d('stl2018_canopy_m2', 'm2', 'stl', 'area of union of STL polygons clipped', 'STL covers only street trees in 2018 imagery of urban fabric; under-represents parks and private trees')
d('stl2018_pct', '%', 'stl', '100 x stl2018_canopy_m2 / area_m2 (matches treecover csv ua_stl2018_pct within 0.0005)', 'as above')
d('canopy_chm_ge3m_m2', 'm2', 'chm', 'share of CHM pixels with height 3-100 m inside the polygon (pixel-centre rule, EPSG:3857) x polygon area in EPSG:2100', 'model ~2018-2020, 8 years old by 2026; includes tall buildings/artefacts under 3-5 m misclassification and excludes young trees; roughly +-20% relative (assumed)')
d('chm_ge3m_pct', '%', 'chm', '100 x canopy_chm_ge3m_m2 / area_m2 (matches treecover csv within 0.0005)', 'as above')
d('chm_valid_pixel_pct', '%', 'chm', 'share of pixels inside polygon with a value 0-100 (coverage check)', 'min 100')
for t in (5, 10, 15, 30):
    d(f'canopy_deficit_to_{t}pct_m2', 'm2', 'chm', f'max(0, area_m2 x {t}% - canopy_chm_ge3m_m2)', 'arithmetic on a dated model; says nothing about whether the space exists')
for dd in (4, 6, 8):
    for t in (5, 10, 15, 30):
        d(f'illustr_trees_{t}pct_crown{dd}m', 'trees', 'chm', f'ceil(canopy_deficit_to_{t}pct_m2 / (pi x {dd}^2 / 4)); crown diameter {dd} m at maturity', 'ILLUSTRATIVE ARITHMETIC, not a planting plan: ignores crown overlap, space, utilities, mortality, time to maturity')
d('plantings_since_2024_rows', 'count', 'plant', 'planting records with planting_date >= 2024-01-01 inside the neighbourhood', '23 records outside municipality not counted; location precision unknown')
d('plantings_since_2024_trees', 'trees', 'plant', 'sum num_trees of those records', 'as above')
for typ, lab in [('schools', 'schools'), ('nurseries', 'nurseries'), ('playgrounds', 'playgrounds'), ('elderly_clubs', 'elderly clubs (Lesches Filias)')]:
    d(f'sites_{typ}_n', 'count', 'sites', f'{lab} in sites_with_plantings.csv by point-in-polygon', 'layers 2018-2023 vintage; schools layer has 401 points of which 397 inside')
    d(f'sites_{typ}_canopy150m_lt5pct_n', 'count', 'sites', f'{lab} with canopy_pct_150m < 5', 'canopy from the dated CHM; 150 m buffer')
d('sites_all4_n', 'count', 'sites', 'sum of the four site types', 'as above')
d('sites_all4_canopy150m_lt5pct_n', 'count', 'sites', 'sum of the four with canopy_pct_150m < 5', 'as above')
d('pop_total', 'persons', 'pop', 'pop_total per neighbourhood', 'modelled estimate')
d('low_tree_group_stl_lt2pct', 'bool', 'stl', 'ua_stl2018_pct < 2 in treecover/treecover_by_neighbourhood.csv (62 neighbourhoods)', 'threshold on a street-tree-layer metric')
out = nb.drop(columns=['chm_csv', 'stl_csv'])
miss = [c for c in out.columns if c not in D]
assert not miss, miss
pd.DataFrame([(c,) + D[c] for c in out.columns], columns=['column', 'unit', 'source_layer_and_date', 'method', 'known_error']).to_csv(OUT + 'metrics_dictionary.csv', index=False)
print('report done; columns', len(out.columns), 'spot', spot)
