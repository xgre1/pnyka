#!/usr/bin/env python3
"""Reference calculation: intervention packages per neighbourhood, from data.

Python standard library only. No network, no LLM. Deterministic.

Run:
    python3 engine/generate_packages.py                   # writes all outputs into engine/
    python3 engine/generate_packages.py --budget 1000000  # what 1M buys in EACH tab (trees, roofs), separately;
                                                          # printed and written to engine/budget_1m.md
    python3 engine/generate_packages.py --budget 1000000 --rank-by people_per_eur   # non-default comparison

Every coefficient comes from engine/params.csv (status + source per row).
Every rule comes from engine/rules.csv and engine/need_defs.csv.
Where a number does not exist the output stays EMPTY and says so.
See engine/README.md for every formula.
"""
import argparse
import bisect
import csv
import json
import math
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SRC = {
    'capacity': 'capacity/capacity_by_neighbourhood.csv',
    'population': 'raw/population/population_by_neighbourhood.csv',
    'sites': 'streets/sites_with_plantings.csv',
    'treecover': 'treecover/treecover_by_neighbourhood.csv',
    'neigh': 'neighbourhoods.csv',
    'pm25': 'research/health/burden/pm25_burden_by_group.csv',
    'plantings': 'athenstrees/plantings_by_neighbourhood.csv',
    'cost_model': 'research/cost/cost_model.csv',
}
DEFAULTS_REL = 'research/cost/roofs_pavements/defaults.csv'
PARAM_COLS = ['intervention_id', 'parameter', 'unit', 'low', 'central', 'high',
              'source_file', 'source_ref', 'status', 'note']
STATUSES = {'measured_athens', 'published_elsewhere', 'city_contract', 'assumption', 'missing'}
LV = ('low', 'central', 'high')
BUDGETS = [(250000, '250k'), (1000000, '1m'), (5000000, '5m')]
# budget modes: per_tab (default, team decision σημείωμα ομάδας)
# = a separate budget per tab spent in rank_within_intervention order; people_per_eur = old cross-intervention
# comparison, kept as a non-default option.
RANK_BY = ('per_tab', 'people_per_eur')
# the two tabs of the screen: (intervention id, tab name in Greek, tab name in English)
BUDGET_TABS = [('trees_pavement', 'Δρόμοι', 'street trees'),
               ('roof_cool_or_green_municipal', 'Κτίρια', 'cool roofs on municipal buildings')]
SCORE_METHODS = ('mean', 'balanced')

# stable short codes for packages.json (labels in labels_el.csv)
UNIT_CODE = {'qty_trees_pavement': 'trees', 'qty_roof_municipal': 'm2_roof_footprint',
             'qty_cool_surface': 'sites', 'qty_school_street': 'schemes', 'qty_elderly_support': 'persons_65plus'}
UNIT_CODE_DEF = {'% of area': 'percent_of_area', 'm2': 'm2', 'persons': 'persons', 'persons per km2': 'persons_per_km2',
                 'count': 'count', 'share 0-1': 'share_0_1', 'trees per 1000': 'trees_per_1000_residents',
                 'degC': 'degC', 'ug/m3': 'ug_m3'}
# fields of the eligibility rules: (indicator code, unit code)
ELIG_FIELD = {'canopy_deficit_m2': ('canopy_deficit_m2', 'm2'),
              'roof_municipal_m2': ('roof_municipal_m2', 'm2'),
              'low_canopy_schools_playgrounds_n': ('low_canopy_schools_playgrounds_n', 'count'),
              'sites_schools_n': ('sites_schools_n', 'count'),
              'pop_65plus': ('residents_65plus', 'persons')}
# number of sites behind a package (column sites_n), from the capacity data
SITES_FN = {
    'roof_cool_or_green_municipal': lambda r: int(round((r.get('schools_buildings_n') or 0) + (r.get('municipal_other_buildings_n') or 0))),
    'school_street': lambda r: int(round(r['sites_schools_n'])),
    'elderly_heat_support': lambda r: int(round(r.get('sites_elderly_clubs_n') or 0)),
    'cool_surface_schoolyard_playground': lambda r: int(round(r['low_canopy_schools_playgrounds_n'])),
    'trees_pavement': lambda r: int(round(r.get('sites_all4_canopy150m_lt5pct_n') or 0)),
}
# impact metrics of packages.json: (metric_code, parameter, unit code, source code)
IMPACT_META = {
    'trees_pavement': [
        ('pavement_surface_temp_under_shade', 'pavement_surface_temp_sun_c', 'degC', 'city_thermal_camera_2025'),
        ('street_air_temp_shaded_street', 'street_air_temp_reduction_shaded_street_c', 'degC', 'tsiros_2010'),
        ('street_air_temp_very_shaded_street', 'street_air_temp_reduction_max_reported_c', 'degC', 'tsiros_2010'),
        ('felt_temp_under_tree', 'felt_temp_reduction_under_tree_c', 'degC', 'sari_2025_istanbul'),
        ('neighbourhood_mean_air_temp', 'neighbourhood_mean_air_temp_effect_few_pp_c', 'degC', 'iungman_ziter'),
    ],
    'roof_cool_or_green_municipal': [
        # measured in Athens first, the simulated item last
        ('classroom_air_temp_summer', 'classroom_air_temp_reduction_summer_degc', 'degC', 'cool_roofs_kaisariani'),
        ('roof_surface_temp', 'roof_surface_temp_reduction_degc', 'degC', 'cool_roofs_kaisariani'),
        ('building_cooling_load', 'building_cooling_load_reduction_pct', 'percent', 'santamouris_2007'),
    ],
    'cool_surface_schoolyard_playground': [
        ('surface_temp_cool_surface', 'surface_temp_reduction_c', 'degC', 'santamouris_2012'),
        ('local_air_temp_cool_surface', 'air_temp_reduction_local_c', 'degC', 'santamouris_2012'),
    ],
    'school_street': [
        ('no2_at_school_gate', 'no2_reduction_at_gate_pct', 'percent', 'gla_2021'),
    ],
    'elderly_heat_support': [
        ('heatwave_excess_deaths_covered', 'heatwave_excess_death_reduction_covered_pct', 'percent', 'orlando_2021'),
    ],
}


# ----------------------------------------------------------------- helpers
def norm(s):
    return ' '.join(unicodedata.normalize('NFC', str(s)).split())


def num(s):
    if s is None:
        return None
    s = str(s).strip()
    if s == '' or s.lower() in ('nan', 'none', 'null'):
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if math.isnan(v):
        return None
    return v


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def cell(x):
    """Format a value for CSV output. None -> empty (never a guess)."""
    if x is None:
        return ''
    if isinstance(x, bool):
        return 'True' if x else 'False'
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        s = '{:.4f}'.format(x).rstrip('0').rstrip('.')
        return '0' if s in ('', '-0') else s
    return str(x)


def g(x):
    """Short number for human-readable text."""
    if x is None:
        return 'missing'
    if abs(x) >= 100:
        return '{:,.0f}'.format(x)
    return '{:.3g}'.format(x)


def eur(x):
    return '{:,.0f}'.format(x)


# -------------------------------------------------------------- parameters
class Params(object):
    def __init__(self, rows):
        self.rows = rows
        self.idx = {}
        for r in rows:
            key = (r['intervention_id'], r['parameter'])
            if key in self.idx:
                raise ValueError('duplicate parameter %s.%s' % key)
            if r['status'] not in STATUSES:
                raise ValueError('bad status %r for %s.%s' % (r['status'], key[0], key[1]))
            self.idx[key] = r

    def row(self, i, p):
        try:
            return self.idx[(i, p)]
        except KeyError:
            raise KeyError('parameter %s.%s is not in params.csv' % (i, p))

    def val(self, i, p, level):
        return num(self.row(i, p)[level])

    def of(self, i):
        return [r for r in self.rows if r['intervention_id'] == i]


def load_params(path=None, root=ROOT):
    path = path or os.path.join(HERE, 'params.csv')
    rows = read_csv(path)
    notes = []
    dpath = os.path.join(root, DEFAULTS_REL)
    if os.path.exists(dpath):
        drows = read_csv(dpath)
        if drows and 'intervention_id' in drows[0] and 'parameter' in drows[0]:
            have = dict(((r['intervention_id'], r['parameter']), r) for r in rows)
            for d in drows:
                new = dict((c, (d.get(c) or '').strip()) for c in PARAM_COLS)
                if not new['source_file']:
                    new['source_file'] = DEFAULTS_REL
                if not new['status']:
                    new['status'] = 'assumption'
                key = (new['intervention_id'], new['parameter'])
                if key in have:
                    old = have[key]
                    if all(num(old[l]) is None for l in LV):
                        for c in PARAM_COLS:
                            old[c] = new[c] if new[c] != '' else old[c]
                        notes.append('defaults.csv filled %s.%s' % key)
                    else:
                        notes.append('defaults.csv row %s.%s ignored: params.csv already has a value' % key)
                else:
                    rows.append(new)
                    have[key] = new
                    notes.append('defaults.csv added %s.%s' % key)
        else:
            notes.append('%s has its own layout (no intervention_id column): not read automatically. The cool-roof '
                         'price of its row cool_roof_cost_installed was copied by hand into params.csv '
                         '(roof_cool_or_green_municipal.roof_cost_per_m2_eur, status assumption)' % DEFAULTS_REL)
    else:
        notes.append('%s not present: no additional defaults loaded' % DEFAULTS_REL)
    return Params(rows), notes


# --------------------------------------------------------------- percentiles
def pct_ranks(values, higher_more_need=True):
    """values: dict key -> number or None. Returns key -> 0..100 or None.

    Mid-rank percentile among the keys that HAVE a value (missing stays missing).
    100 = highest need. Ties share the mid-rank.
    """
    present = [(k, v) for k, v in values.items() if v is not None]
    out = dict((k, None) for k in values)
    n = len(present)
    if n == 0:
        return out
    sv = sorted(v for _, v in present)
    for k, v in present:
        less = bisect.bisect_left(sv, v)
        eq = bisect.bisect_right(sv, v) - less
        pos = less + (eq - 1) / 2.0
        if not higher_more_need:
            pos = (n - 1) - pos
        out[k] = 100.0 * pos / (n - 1) if n > 1 else 50.0
    return out


# ------------------------------------------------------------------- data
def load_records(P, root=ROOT):
    """One record per neighbourhood, joined by name. Missing stays None."""
    cap_rows = read_csv(os.path.join(root, SRC['capacity']))
    pop = dict((norm(r['name']), r) for r in read_csv(os.path.join(root, SRC['population'])))
    tre = dict((norm(r['neighbourhood']), r) for r in read_csv(os.path.join(root, SRC['treecover'])))
    nei = dict((norm(r['name']), r) for r in read_csv(os.path.join(root, SRC['neigh'])))
    pla = dict((norm(r['name']), r) for r in read_csv(os.path.join(root, SRC['plantings'])))
    pm = dict((norm(r['group']), num(r['pm25_est'])) for r in read_csv(os.path.join(root, SRC['pm25'])))

    target = P.val('_global', 'canopy_target_pct', 'central')
    if target not in (5.0, 10.0, 15.0, 30.0):
        raise ValueError('canopy_target_pct must be 5, 10, 15 or 30 (columns of the capacity file)')
    defcol = 'canopy_deficit_to_%dpct_m2' % int(target)

    names = [norm(r['name']) for r in cap_rows]
    if len(set(names)) != len(names):
        raise ValueError('duplicate neighbourhood names in capacity file')

    recs = []
    join_gaps = {}
    for row, name in zip(cap_rows, names):
        rec = {}
        for k, v in row.items():
            if k in ('name', 'community'):
                continue
            rec[k] = num(v)
        rec['name'] = name
        rec['community'] = row['community']
        cid = rec.get('community_id')
        rec['community_id'] = int(cid) if cid is not None else None
        rec['pop_total_capacity_file'] = rec.get('pop_total')

        gaps = []
        p = pop.get(name)
        if p is None:
            gaps.append('population')
        for k in ('pop_total', 'pop_0_14', 'pop_65plus', 'pop_density_per_km2'):
            rec[k] = num(p[k]) if p is not None else None
        t = tre.get(name)
        if t is None:
            gaps.append('treecover')
        rec['stl_pct'] = num(t['ua_stl2018_pct']) if t is not None else None
        # satellite land-surface temperature, summer day 2016-2020 (City of Athens GIS layer, EXTREMA): surface, not air
        rec['lst_summer_day_c'] = num(t['city_lst_summer_day_2016_2020_c']) if t is not None else None
        n_ = nei.get(name)
        if n_ is None:
            gaps.append('neighbourhoods.csv')
        rec['heat_night'] = num(n_['heat_night']) if n_ is not None else None
        pl = pla.get(name)
        if pl is None:
            gaps.append('plantings')
        rec['trees_planted'] = num(pl['trees_planted_2024_2026']) if pl is not None else None
        rec['pm25_community'] = pm.get('ΔΚ %d' % rec['community_id']) if rec['community_id'] is not None else None
        if gaps:
            join_gaps[name] = gaps

        # derived fields (formulas documented in README)
        rec['canopy_deficit_m2'] = rec.get(defcol)
        a, b = rec.get('schools_roof_area_m2'), rec.get('municipal_other_roof_area_m2')
        rec['roof_municipal_m2'] = ((a or 0.0) + (b or 0.0)) if (a is not None or b is not None) else None
        tot, lt5 = rec.get('sites_all4_n'), rec.get('sites_all4_canopy150m_lt5pct_n')
        rec['low_canopy_sites_n'] = lt5
        rec['low_canopy_sites_share'] = (lt5 / tot) if (tot and lt5 is not None) else None
        s5, p5 = rec.get('sites_schools_canopy150m_lt5pct_n'), rec.get('sites_playgrounds_canopy150m_lt5pct_n')
        rec['low_canopy_schools_playgrounds_n'] = (s5 + p5) if (s5 is not None and p5 is not None) else None
        sn, pn = rec.get('sites_schools_n'), rec.get('sites_playgrounds_n')
        rec['schools_playgrounds_n'] = (sn + pn) if (sn is not None and pn is not None) else None
        pt = rec['pop_total']
        rec['new_trees_per_1000'] = (rec['trees_planted'] / pt * 1000.0) if (pt and rec['trees_planted'] is not None) else None
        recs.append(rec)
    return recs, join_gaps, defcol


# Indicator id -> value of a record. Direction etc. come from need_defs.csv.
IND_VALUE = {
    'tree_cover_stl2018_pct': lambda r: r['stl_pct'],
    'canopy_deficit_m2': lambda r: r['canopy_deficit_m2'],
    'residents': lambda r: r['pop_total'],
    'residents_65plus': lambda r: r['pop_65plus'],
    'residents_0_14': lambda r: r['pop_0_14'],
    'pop_density_per_km2': lambda r: r['pop_density_per_km2'],
    'low_canopy_sites_n': lambda r: r['low_canopy_sites_n'],
    'low_canopy_sites_share': lambda r: r['low_canopy_sites_share'],
    'low_canopy_schools_playgrounds_n': lambda r: r['low_canopy_schools_playgrounds_n'],
    'new_trees_per_1000_residents': lambda r: r['new_trees_per_1000'],
    'night_temp_c': lambda r: r['heat_night'],
    'pm25_community_est': lambda r: r['pm25_community'],
    'surface_temp_lst_c': lambda r: r['lst_summer_day_c'],
}


# ------------------------------------------------------- quantity functions
def _unit_cost_trees(P, lvl):
    a = P.val('trees_pavement', 'cost_per_planted_tree_existing_pit_incl_vat_eur', lvl)
    b = P.val('trees_pavement', 'cost_per_planted_tree_new_small_pit_incl_vat_eur', lvl)
    s = P.val('trees_pavement', 'share_new_small_pits', 'central')
    if a is None or b is None or s is None:
        return None
    return (1.0 - s) * a + s * b


def _ceil(x):
    return int(math.ceil(round(x, 9)))


def qty_trees_pavement(rec, P):
    """trees = ceil(canopy_to_add_m2 / (crown_area x survival)).

    canopy_to_add = min(area x pp/100, deficit to target).  low = optimistic
    (largest crown, highest survival), high = pessimistic. Capacity = trees to
    close the whole deficit with the same parameters.  Cost = trees x blended
    unit cost of the City contract (per planted tree).
    """
    I = 'trees_pavement'
    crown = dict((l, P.val(I, 'crown_area_at_20y_m2', l)) for l in LV)
    surv = dict((l, P.val(I, 'survival_to_maturity_fraction', l)) for l in LV)
    opt = {'low': 'high', 'central': 'central', 'high': 'low'}   # fewer trees = optimistic
    area, deficit = rec['area_m2'], rec['canopy_deficit_m2']

    def trees_for(m2):
        out = {}
        for l in LV:
            c, s = crown[opt[l]], surv[opt[l]]
            out[l] = _ceil(m2 / (c * s)) if (c and s) else None
        return out

    pp = P.val(I, 'canopy_increment_pp_package', 'central')
    add = min(area * pp / 100.0, deficit)
    q = trees_for(add)
    cap = trees_for(deficit)
    cost = {}
    for l in LV:
        u = _unit_cost_trees(P, l)
        cost[l] = q[l] * u if (q[l] is not None and u is not None) else None
    maint = P.val(I, 'maintenance_eur_per_tree_year', 'central')
    recurring = q['central'] * maint if (q['central'] is not None and maint is not None) else None

    opts = []
    for key in ('canopy_increment_pp_option_b', 'canopy_increment_pp_option_c'):
        ppx = P.val(I, key, 'central')
        if ppx is None:
            continue
        addx = min(area * ppx / 100.0, deficit)
        qx = trees_for(addx)['central']
        u = _unit_cost_trees(P, 'central')
        cx = qx * u if (qx is not None and u is not None) else None
        opts.append('+%g pp: %s trees (central cost %s)' % (
            ppx, g(qx), (eur(cx) + ' EUR') if cx is not None else 'not computed'))
    flags = ['capacity_unverified']
    if area * pp / 100.0 > deficit:
        flags.append('target_capped_by_deficit')
    note = ('canopy to add %s m2 = min(+%g pp of area %s m2, deficit to %d%% = %s m2); '
            'trees = ceil(m2 / (crown area x survival)); central crown %s m2, survival %s; '
            'canopy appears after ~20 years; capacity_unverified: no tree-pit register, plantable spots unknown'
            % (g(add), pp, g(area), int(P.val('_global', 'canopy_target_pct', 'central')), g(deficit),
               g(crown['central']), g(surv['central'])))
    return {'q': q, 'cap': cap, 'unit': 'trees', 'cost': cost, 'recurring': recurring,
            'note': note, 'options': '; '.join(opts), 'flags': flags,
            'cost_basis': 'trees x [(1-s) x cost(existing pit) + s x cost(new small pit)], s = share_new_small_pits; '
                          'City contract prices incl. VAT, per planted tree, includes 2-3 y watering'}


def qty_roof_municipal(rec, P):
    I = 'roof_cool_or_green_municipal'
    area = rec['roof_municipal_m2']
    q = dict((l, area) for l in LV)
    price = dict((l, P.val(I, 'roof_cost_per_m2_eur', l)) for l in LV)
    cost = dict((l, area * price[l] if price[l] is not None else None) for l in LV)
    return {'q': q, 'cap': dict(q), 'unit': 'm2 matched roof footprint (lower bound)', 'cost': cost,
            'recurring': None, 'options': '',
            'note': 'schools_roof_area_m2 + municipal_other_roof_area_m2 (footprint of matched buildings; '
                    'flat/usable share unknown; libraries, sports halls, markets not in the layers). '
                    'The cost is on this whole footprint: an UPPER bound of the roof area that can be treated '
                    '(not all footprint is flat or usable) and a LOWER bound of the buildings (not all municipal '
                    'buildings are matched)',
            'flags': ['lower_bound', 'usable_flat_share_unknown', 'cost_area_upper_bound', 'price_is_assumption'],
            'cost_basis': 'm2 matched roof footprint x roof_cost_per_m2_eur (ASSUMPTION: low = City of Athens 2012 '
                          'price list, elastomeric membrane; central/high = vendor figures; excludes roof preparation; '
                          'the City should overwrite it)'}


def qty_cool_surface(rec, P):
    I = 'cool_surface_schoolyard_playground'
    n = rec['low_canopy_schools_playgrounds_n']
    cap_n = rec['schools_playgrounds_n']
    q = dict((l, n) for l in LV)
    cap = dict((l, cap_n) for l in LV)
    yard = dict((l, P.val(I, 'yard_area_per_site_m2', l)) for l in LV)
    price = dict((l, P.val(I, 'cool_pavement_cost_eur_per_m2', l)) for l in LV)
    cost = {}
    flags = ['single_source_price']
    for l in LV:
        if yard[l] is not None and price[l] is not None:
            cost[l] = n * yard[l] * price[l]
        else:
            cost[l] = None
    if any(v is not None for v in yard.values()):
        flags.append('yard_area_is_assumption')
    else:
        flags.append('yard_area_unknown')
    return {'q': q, 'cap': cap, 'unit': 'sites (schools+playgrounds, canopy <5% within 150 m)', 'cost': cost,
            'recurring': None, 'options': '',
            'note': 'number of schools and playgrounds with canopy_pct_150m < 5; area per site unknown, '
                    'so m2 and cost are computed only if a yard-area parameter exists',
            'flags': flags,
            'cost_basis': 'sites x yard_area_per_site_m2 x cool_pavement_cost_eur_per_m2'}


def qty_school_street(rec, P):
    I = 'school_street'
    n = rec['sites_schools_n']
    q = dict((l, n) for l in LV)
    price = dict((l, P.val(I, 'cost_per_scheme_eur', l)) for l in LV)
    cost = dict((l, n * price[l] if price[l] is not None else None) for l in LV)
    return {'q': q, 'cap': dict(q), 'unit': 'school street schemes (one per school)', 'cost': cost,
            'recurring': None, 'options': '',
            'note': 'number of schools in the neighbourhood (upper bound: assumes every school has a closable street; '
                    'traffic decision and enforcement not assessed)',
            'flags': ['upper_bound', 'london_prices'],
            'cost_basis': 'schools x cost_per_scheme_eur (London FOI, converted)'}


def qty_elderly_support(rec, P):
    I = 'elderly_heat_support'
    n = int(round(rec['pop_65plus']))
    q = dict((l, n) for l in LV)
    price = dict((l, P.val(I, 'cost_per_person_covered_eur', l)) for l in LV)
    cost = dict((l, n * price[l] if price[l] is not None else None) for l in LV)
    clubs = rec.get('sites_elderly_clubs_n')
    return {'q': q, 'cap': dict(q), 'unit': 'residents 65+ (ceiling of people who could be covered)', 'cost': cost,
            'recurring': None, 'options': '',
            'note': 'residents 65+ (modelled, +-25-30%%); elderly clubs (Lesches Filias) in the neighbourhood: %s'
                    % (g(clubs) if clubs is not None else 'missing'),
            'flags': ['ceiling'],
            'cost_basis': 'residents 65+ x cost_per_person_covered_eur'}


QFN = {
    'qty_trees_pavement': qty_trees_pavement,
    'qty_roof_municipal': qty_roof_municipal,
    'qty_cool_surface': qty_cool_surface,
    'qty_school_street': qty_school_street,
    'qty_elderly_support': qty_elderly_support,
}


# --------------------------------------------------------- impact statements
def _up_to(P, I, param, label):
    row = P.row(I, param)
    vals = dict((l, num(row[l])) for l in LV)
    present = [v for v in vals.values() if v is not None]
    if not present:
        return '%s: not available (status %s)' % (label, row['status'])
    rng = ', '.join('%s %s' % (l, g(v)) for l, v in vals.items() if v is not None)
    return '%s: up to %s %s (%s; status %s; %s)' % (label, g(max(present)), row['unit'], rng,
                                                    row['status'], row['source_ref'])


def impact_trees(rec, P):
    I = 'trees_pavement'
    sun = P.val(I, 'pavement_surface_temp_sun_c', 'central')
    shade = P.val(I, 'pavement_surface_temp_tree_shade_c', 'central')
    parts = []
    if sun is not None and shade is not None:
        parts.append('Pavement surface %s degC in sun vs %s degC under tree shade: up to %s degC lower under a mature crown '
                     '(status %s; %s)' % (g(sun), g(shade), g(sun - shade),
                                          P.row(I, 'pavement_surface_temp_sun_c')['status'],
                                          P.row(I, 'pavement_surface_temp_sun_c')['source_ref']))
    parts.append(_up_to(P, I, 'street_air_temp_reduction_shaded_street_c', 'Air in the shaded street at 14:00 in a heatwave'))
    parts.append(_up_to(P, I, 'street_air_temp_reduction_max_reported_c', 'Very shaded street'))
    parts.append(_up_to(P, I, 'felt_temp_reduction_under_tree_c', 'Felt temperature under the tree (daytime)'))
    parts.append(_up_to(P, I, 'neighbourhood_mean_air_temp_effect_few_pp_c',
                        'Neighbourhood-MEAN air temperature for a few points of cover'))
    parts.append('No health outcome (deaths, admissions) is claimed for trees; effect is local and appears after the time to effect')
    return ' | '.join(parts), ''


def impact_roof(rec, P):
    I = 'roof_cool_or_green_municipal'
    return (_up_to(P, I, 'classroom_air_temp_reduction_summer_degc', 'Classroom air temperature in summer (measured, one school)')
            + ' | ' + _up_to(P, I, 'roof_surface_temp_reduction_degc', 'Roof surface temperature (measured, one school)')
            + ' | ' + _up_to(P, I, 'building_cooling_load_reduction_pct', 'Cooling load of the building (simulated, inside the building only)')
            + ' | No street-level or health figure is claimed; no euro saving is claimed (building energy use is missing); '
              'the roof cost is an assumed unit price on the matched footprint'), ''


def impact_cool_surface(rec, P):
    I = 'cool_surface_schoolyard_playground'
    return ' | '.join([
        _up_to(P, I, 'surface_temp_reduction_c', 'Surface temperature'),
        _up_to(P, I, 'air_temp_reduction_local_c', 'Local air temperature (simulated)'),
        'No health outcome is claimed']), ''


def impact_school_street(rec, P):
    I = 'school_street'
    return (_up_to(P, I, 'no2_reduction_at_gate_pct', 'NO2 at the school gate during closure hours')
            + ' | NO2 is not in the PM2.5 mortality function: no health outcome is claimed'), ''


def impact_elderly(rec, P):
    I = 'elderly_heat_support'
    pct = dict((l, P.val(I, 'heatwave_excess_death_reduction_covered_pct', l)) for l in LV)
    rate = dict((l, P.val(I, 'heat_death_rate_65plus_per_10000_per_year', l)) for l in LV)
    cov = P.val(I, 'coverage_share_for_ceiling', 'central')
    pop65 = rec['pop_65plus']
    stmt = _up_to(P, I, 'heatwave_excess_death_reduction_covered_pct', 'Heatwave excess deaths among those COVERED')
    base = ''
    if all(v is not None for v in list(pct.values()) + list(rate.values())) and cov is not None:
        b = dict((l, pop65 * rate[l] / 10000.0) for l in LV)
        c = dict((l, b[l] * cov * pct[l] / 100.0) for l in LV)
        base = ('baseline heat deaths/yr among residents 65+ here: %s (low %s, high %s) [ASSUMPTION: scaled from greater '
                'Athens, not a measured count]' % (g(b['central']), g(b['low']), g(b['high'])))
        stmt += (' | Illustrative CEILING for this neighbourhood if all residents 65+ were covered (coverage %s): up to %s '
                 'heat deaths/yr fewer (low %s, central %s); not a forecast: Rome covered isolated 80+ only, the baseline is an '
                 'assumption, the population has +-25-30%% error'
                 % (g(cov), g(c['high']), g(c['low']), g(c['central'])))
    return stmt, base


IMPACT = {
    'impact_trees': impact_trees,
    'impact_roof': impact_roof,
    'impact_cool_surface': impact_cool_surface,
    'impact_school_street': impact_school_street,
    'impact_elderly': impact_elderly,
}


def split_top(text):
    """Split on ';' outside parentheses (the data_gaps texts of rules.csv contain ';' inside brackets)."""
    out, depth, cur = [], 0, ''
    for ch in text:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ';' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    out.append(cur)
    return [x for x in out if x.strip()]


# ---------------------------------------------------------------- eligibility
COND = re.compile(r'^\s*([A-Za-z0-9_]+)\s*(>=|<=|==|>|<)\s*(-?[0-9.]+)\s*$')


def eligible(rec, text):
    trig = []
    for part in text.split(';'):
        m = COND.match(part)
        if not m:
            raise ValueError('cannot parse eligibility condition %r' % part)
        field, op, thr = m.group(1), m.group(2), float(m.group(3))
        v = rec.get(field)
        if v is None:
            return False, ''          # a missing value never satisfies a rule
        ok = {'>': v > thr, '>=': v >= thr, '<': v < thr, '<=': v <= thr, '==': v == thr}[op]
        if not ok:
            return False, ''
        trig.append('%s=%s (rule %s %g)' % (field, g(v), op, thr))
    return True, '; '.join(trig)


# ---------------------------------------------------------------------- build
def rank_key(p, ru):
    """Sort key of rank_within_intervention: score descending at the 4 decimals of the csv (no score last), then
    the rank_tie_break field of the rule if any (missing value last), then neighbourhood name (Unicode order)."""
    k = [p['score'] is None, -round(p['score'] or 0.0, 4)]
    if ru['_tie_field']:
        v = p['tie_value']
        k += [v is None, -(v or 0.0) if ru['_tie_desc'] else (v or 0.0)]
    k.append(p['neighbourhood'])
    return tuple(k)


def build(params_path=None, root=ROOT):
    P, notes = load_params(params_path, root)
    rules = read_csv(os.path.join(HERE, 'rules.csv'))
    for ru in rules:
        # score_method: mean (need score and people percentile averaged) or balanced (the need score is first
        # re-ranked to a percentile among the packages of the intervention); see README 'Priority score'
        sm = (ru.get('score_method') or '').strip()
        if sm not in SCORE_METHODS:
            raise ValueError('rules.csv: score_method %r for %s must be one of %s' % (sm, ru['intervention_id'], SCORE_METHODS))
        # rank_tie_break: empty (ties by neighbourhood name) or '<record field>:desc|asc' tried before the name
        tb = (ru.get('rank_tie_break') or '').strip()
        field, _, direction = tb.partition(':')
        if tb and (direction not in ('asc', 'desc') or not field):
            raise ValueError('rules.csv: rank_tie_break %r for %s must be <field>:asc or <field>:desc' % (tb, ru['intervention_id']))
        ru['_score_method'], ru['_tie_field'], ru['_tie_desc'] = sm, (field or None), direction == 'desc'
    defs = read_csv(os.path.join(HERE, 'need_defs.csv'))
    recs, join_gaps, defcol = load_records(P, root)

    # --- need indicators: raw value + percentile among neighbourhoods that have it
    ind = {}
    for d in defs:
        iid = d['indicator_id']
        vals = dict((r['name'], IND_VALUE[iid](r)) for r in recs)
        pcts = pct_ranks(vals, higher_more_need=(d['direction'] != 'lower_more_need'))
        ind[iid] = {'def': d, 'value': vals, 'pct': pcts}

    pop_err_lo = P.val('_global', 'population_error_single_neighbourhood_pct', 'low')
    pop_err_hi = P.val('_global', 'population_error_single_neighbourhood_pct', 'high')
    people_caveat = ('single-neighbourhood population error about +-%g-%g%% (sources agree only r=0.43-0.68); '
                     'totals are reliable; not a precise count' % (pop_err_lo, pop_err_hi))

    # --- packages
    packages = []
    for rec in recs:
        for ru in rules:
            I = ru['intervention_id']
            ok, trig = eligible(rec, ru['eligibility'])
            if not ok:
                continue
            Q = QFN[ru['quantity_fn']](rec, P)
            cost = Q['cost']
            ppl_field = ru['people_field']
            people = rec[ppl_field] if ppl_field else None
            stmt, baseline = IMPACT[ru['impact_fn']](rec, P)

            t = dict((l, P.val(I, 'time_to_effect_years', l)) for l in LV)
            tv = [v for v in (t['low'], t['high']) if v is not None]
            tstat = P.row(I, 'time_to_effect_years')['status']
            if not tv:
                tte = 'not available'
            elif min(tv) == max(tv):
                tte = '%s years (status %s)' % (g(tv[0]), tstat)
            else:
                tte = '%s to %s years (status %s)' % (g(min(tv)), g(max(tv)), tstat)

            need_list = [x for x in ru['need_indicators'].split(';') if x]
            why = ['ELIGIBLE: ' + trig]
            for iid in need_list:
                d = ind[iid]['def']
                v, p = ind[iid]['value'][rec['name']], ind[iid]['pct'][rec['name']]
                if v is None:
                    why.append('%s = missing (not imputed)' % d['label'])
                else:
                    why.append('%s = %s %s (need percentile %.0f)' % (d['label'], g(v), d['unit'], p))

            # data gaps: from the rule, from missing params of this intervention, from missing costs
            gaps = [x for x in ru['data_gaps'].split(';') if x]
            gcodes = [x for x in ru['data_gap_codes'].split(';') if x]
            if len(gcodes) != len(split_top(ru['data_gaps'])):
                raise ValueError('rules.csv: data_gaps and data_gap_codes differ in length for %s' % I)
            for r in P.of(I):
                if r['status'] == 'missing':
                    gaps.append('param %s.%s missing' % (I, r['parameter']))
                    gcodes.append('missing_' + r['parameter'])
            cost_params = [x for x in ru['cost_params'].split(';') if x]
            miss_cost = []
            for cp in cost_params:
                ci, cn = cp.split('.', 1)
                if P.val(ci, cn, 'central') is None:
                    miss_cost.append(cp)
            if cost['central'] is None:
                cost_status = 'NOT COMPUTED: missing %s' % (', '.join(miss_cost) if miss_cost else 'a price')
                gaps.append('no cost: ' + (', '.join(miss_cost) if miss_cost else 'price missing'))
                gcodes += ['no_cost_' + cp.split('.', 1)[1] for cp in miss_cost] or ['no_cost_price_missing']
            else:
                cost_status = 'computed'
            seen, gaps_u = set(), []
            for x in gaps:
                if x not in seen:
                    seen.add(x)
                    gaps_u.append(x)
            seen, gcodes_u = set(), []
            for x in gcodes:
                if x not in seen:
                    seen.add(x)
                    gcodes_u.append(x)

            # structured why-here for packages.json: eligibility fields first, then the need indicators
            items = []
            for part in ru['eligibility'].split(';'):
                field = COND.match(part).group(1)
                code, ucode = ELIG_FIELD[field]
                items.append({'indicator_code': code, 'value': rec.get(field), 'unit': ucode, 'percentile': None})
            for iid in need_list:
                d = ind[iid]['def']
                v, pc = ind[iid]['value'][rec['name']], ind[iid]['pct'][rec['name']]
                pcv = int('%.0f' % pc) if pc is not None else None
                hit = [it for it in items if it['indicator_code'] == iid]
                if hit:
                    hit[0]['percentile'] = pcv
                else:
                    items.append({'indicator_code': iid, 'value': v, 'unit': UNIT_CODE_DEF[d['unit']], 'percentile': pcv})

            flags = list(Q['flags'])
            if cost['central'] is None:
                flags.append('cost_missing')
            if people is None:
                flags.append('people_missing')

            srcs, statuses = [], set()
            for r in P.of(I) + [P.row('_global', 'population_error_single_neighbourhood_pct')]:
                srcs.append('%s :: %s [%s]' % (r['source_file'], r['source_ref'], r['status']))
                statuses.add(r['status'])
            for s in ru['data_sources'].split(';'):
                if s.strip():
                    srcs.append(s.strip())
            for s in ru['evidence_source'].split(';'):
                if s.strip():
                    srcs.append(s.strip())
            seen, srcs_u = set(), []
            for x in srcs:
                if x not in seen:
                    seen.add(x)
                    srcs_u.append(x)

            ppk = None
            if people is not None and cost['central']:
                ppk = people / (cost['central'] / 1000.0)

            packages.append({
                'package_id': '%s|%s' % (I, rec['name']),
                'neighbourhood': rec['name'], 'community': rec['community'], 'community_id': rec['community_id'],
                'intervention_id': I, 'name_en': ru['name_en'],
                'eligibility_trigger': trig,
                'q': Q['q'], 'cap': Q['cap'], 'unit': Q['unit'], 'quantity_note': Q['note'],
                'quantity_options': Q['options'],
                'cost': cost, 'cost_status': cost_status, 'cost_basis': Q['cost_basis'],
                'recurring': Q['recurring'],
                'people': people, 'people_basis': ru['people_basis'], 'people_caveat': people_caveat,
                'ppk': ppk,
                'impact': stmt, 'impact_baseline': baseline, 'tte': tte,
                'evidence': ru['evidence_status'],
                'why': ' | '.join(why), 'gaps': ' ; '.join(gaps_u), 'flags': ';'.join(flags),
                'statuses': ';'.join(sorted(statuses)),
                'sources': ' || '.join(srcs_u),
                'pm25': rec['pm25_community'],
                'need_list': need_list,
                'sites_n': SITES_FN[I](rec), 'rank': None, 'gap_codes': gcodes_u, 'why_items': items,
                'evidence_code': ru['evidence_code'], 'people_basis_code': ru['people_basis_code'],
                'unit_code': UNIT_CODE[ru['quantity_fn']], 'tte_years': dict((l, t[l]) for l in ('low', 'high')),
                'need_score': None, 'need_pct': None, 'people_pct': None, 'score': None, 'score_basis': '',
                'tie_value': rec.get(ru['_tie_field']) if ru['_tie_field'] else None,
            })

    # --- priority score (formula in README): only need percentiles and people concerned
    w_need = P.val('_global', 'weight_need', 'central')
    w_people = P.val('_global', 'weight_people', 'central')
    for ru in rules:
        I = ru['intervention_id']
        balanced = ru['_score_method'] == 'balanced'
        mine = [p for p in packages if p['intervention_id'] == I]
        ppct = pct_ranks(dict((p['package_id'], p['people']) for p in mine), True)
        for p in mine:
            num_, den = 0.0, 0.0
            for iid in p['need_list']:
                pc = ind[iid]['pct'][p['neighbourhood']]
                if pc is None:
                    continue
                w = P.val('_global', 'weight_need_indicator_' + iid, 'central')
                num_ += w * pc
                den += w
            p['need_score'] = num_ / den if den > 0 else None
            p['people_pct'] = ppct[p['package_id']]
        # balanced: the need score is re-ranked to a percentile among the packages of the intervention, so that it has
        # the same spread as the people percentile and equal nominal weights are equal effective weights
        # (engine/validation/VERDICT.md, trees defect 1 and change C)
        npct = pct_ranks(dict((p['package_id'], p['need_score']) for p in mine), True) if balanced else None
        for p in mine:
            need = npct[p['package_id']] if balanced else p['need_score']
            pp = p['people_pct']
            p['need_pct'] = need if balanced else None
            if need is not None and pp is not None:
                p['score'] = (w_need * need + w_people * pp) / (w_need + w_people)
                p['score_basis'] = ('need+people balanced (need score re-ranked among the %d packages: need percentile %s)'
                                    % (len(mine), cell(need))) if balanced else 'need+people'
            elif need is not None:
                p['score'], p['score_basis'] = need, 'need_only (people concerned missing)'
            elif pp is not None:
                p['score'], p['score_basis'] = pp, 'people_only (no need indicator available)'
            else:
                p['score_basis'] = 'none'

    # rank within the intervention: 1 = highest priority score. Ties at the 4 decimals of the csv: first by the
    # rank_tie_break field of rules.csv if any (roofs: matched roof area, larger first), then by neighbourhood name
    for ru in rules:
        mine = [p for p in packages if p['intervention_id'] == ru['intervention_id']]
        mine.sort(key=lambda p: rank_key(p, ru))
        for i, p in enumerate(mine, 1):
            p['rank'] = i

    return {'params': P, 'param_notes': notes, 'rules': rules, 'defs': defs, 'recs': recs,
            'ind': ind, 'packages': packages, 'join_gaps': join_gaps, 'defcol': defcol,
            'w': {'need': w_need, 'people': w_people}}


# --------------------------------------------------------------------- budget
def run_budget(packages, budget, rank_by='per_tab'):
    """per_tab (default): run_budget_tabs. people_per_eur: the old cross-intervention comparison."""
    if rank_by not in RANK_BY:
        raise ValueError('rank_by must be one of %s' % (RANK_BY,))
    if rank_by == 'per_tab':
        return run_budget_tabs(packages, budget)
    return run_budget_people_per_eur(packages, budget)


def run_budget_tab(packages, budget, I):
    """One tab = one intervention with its OWN budget (team decision 1528).

    Rule (deterministic): the packages of the intervention that have a central cost are walked in
    rank_within_intervention order (1 first). A package is indivisible: it is taken if its central cost fits in
    what is left, otherwise it is skipped and the next one is tried, down to the end of the list.
    Quantities are the package quantities, which are <= capacity by construction.
    """
    mine = sorted([p for p in packages if p['intervention_id'] == I], key=lambda p: p['rank'])
    cand = [p for p in mine if p['cost']['central'] is not None]
    no_cost = [p for p in mine if p['cost']['central'] is None]
    remaining = float(budget)
    selected, skipped = [], []
    for p in cand:
        if p['cost']['central'] <= remaining + 1e-9:
            selected.append(p)
            remaining -= p['cost']['central']
        else:
            skipped.append(p)
    spent = sum(p['cost']['central'] for p in selected)
    return {'intervention_id': I, 'budget': float(budget), 'selected': selected, 'skipped': skipped,
            'no_cost': no_cost, 'spent': spent, 'remaining': float(budget) - spent, 'n_candidates': len(cand),
            'n_packages': len(mine)}


def run_budget_tabs(packages, budget, tabs=None):
    """The same amount, separately, in each tab of BUDGET_TABS (trees, roofs). The tabs are never added together."""
    tabs = tabs or [t[0] for t in BUDGET_TABS]
    return {'rank_by': 'per_tab', 'budget': float(budget), 'tabs': [run_budget_tab(packages, budget, I) for I in tabs]}


def run_budget_people_per_eur(packages, budget):
    """NON-DEFAULT comparison: one list across interventions. Greedy, indivisible packages.

    Candidates are packages with a central cost AND people concerned, sorted by people per euro; ties: higher
    people, neighbourhood name, intervention id. A package that does not fit is skipped; smaller ones later in
    the order may still fit. Roofs never enter (no people figure).
    """
    cand = [p for p in packages if p['cost']['central'] and p['people'] is not None]
    cand.sort(key=lambda p: (-(p['people'] / p['cost']['central']), -p['people'], p['neighbourhood'], p['intervention_id']))
    remaining = float(budget)
    selected, skipped = [], []
    for p in cand:
        if p['cost']['central'] <= remaining + 1e-9:
            selected.append(p)
            remaining -= p['cost']['central']
        else:
            skipped.append(p)
    no_price = {}
    for p in packages:
        no_cost = p['cost']['central'] is None
        if no_cost or p['people'] is None:
            reason = p['cost_status'] if no_cost else (
                'priced, but no people-concerned figure exists, so it cannot be ranked by people per euro '
                '(it has its own budget in the default per-tab mode)')
            d = no_price.setdefault(p['intervention_id'], {'n': 0, 'people': 0.0, 'reason': reason})
            d['n'] += 1
            d['people'] += p['people'] or 0.0
    return {'rank_by': 'people_per_eur', 'budget': float(budget), 'selected': selected, 'skipped': skipped,
            'spent': float(budget) - remaining, 'remaining': remaining, 'no_price': no_price, 'n_candidates': len(cand)}


def render_budget_md(res, data):
    if res['rank_by'] == 'per_tab':
        return render_budget_tabs_md(res, data)
    return render_budget_people_per_eur_md(res, data)


def _sum_level(sel, key, lvl):
    vals = [p[key][lvl] for p in sel]
    return sum(vals) if all(v is not None for v in vals) else None


def render_budget_tabs_md(res, data):
    P = data['params']
    names = dict((t[0], (t[1], t[2])) for t in BUDGET_TABS)
    roof = P.row('roof_cool_or_green_municipal', 'roof_cost_per_m2_eur')
    L = ['# What a budget of %s EUR buys in each tab (reference calculation)' % eur(res['budget']), '',
         'Default mode (`--rank-by per_tab`), following the team decision '
         'σημείωμα ομάδας: each tab has its OWN budget of %s EUR. '
         'The two tabs are not added together and not compared with each other: there is no common unit of impact. '
         'Rule: the packages of the intervention that have a central cost are walked in `rank_within_intervention` order '
         '(1 first, the same order as the colour of the map). A package is indivisible: it is taken if its central cost '
         'fits in what is left, otherwise it is skipped and the next one is tried, down to the end of the list. Greedy, '
         'not optimal, deterministic. Costs are central values; low-high is the scenario range of the same selection.'
         % eur(res['budget']), '']
    for t in res['tabs']:
        I = t['intervention_id']
        el, en = names.get(I, (I, I))
        sel = t['selected']
        lo, hi = _sum_level(sel, 'cost', 'low'), _sum_level(sel, 'cost', 'high')
        rng = (' (scenario range of the same selection %s-%s EUR)' % (eur(lo), eur(hi))) if (sel and lo is not None and hi is not None) else ''
        nb = len(set(p['neighbourhood'] for p in sel))
        qty = sum(p['q']['central'] for p in sel)
        L += ['## %s: %s (`%s`)' % (el, en, I), '']
        if I == 'trees_pavement':
            L += ['- What the order means: "many residents with little shade" (need = low street-tree cover and few trees '
                  'planted since 2024, balanced half and half with the number of residents; README, Priority score). It is NOT '
                  'a measured heat-risk ranking.']
        elif I == 'roof_cool_or_green_municipal':
            L += ['- What the order means: "municipal buildings in bare neighbourhoods" (need = low street-tree cover and hot '
                  'satellite surface temperature; README, Priority score). It does NOT say which roof to treat first: that '
                  'needs the City\'s data on occupants and roof condition.',
                  '- The price per m2 is an ASSUMPTION: %s / %s / %s EUR/m2 (`params.csv` '
                  'roof_cool_or_green_municipal.roof_cost_per_m2_eur, status %s), applied to the whole matched footprint and '
                  'excluding roof preparation. The City should replace it with a quote.'
                  % (roof['low'], roof['central'], roof['high'], roof['status']),
                  '- No people figure exists for roofs (occupants per building are missing), so this tab counts buildings '
                  'and m2, not people.']
        L += ['- Packages selected: %d of %d with a price (%d packages in the tab)' % (len(sel), t['n_candidates'], t['n_packages']),
              '- Spent: %s EUR%s; left over: %s EUR' % (eur(t['spent']), rng, eur(t['remaining']))]
        if I == 'trees_pavement':
            qlo, qhi = _sum_level(sel, 'q', 'low'), _sum_level(sel, 'q', 'high')
            L += ['- Trees: %s (central; low %s, high %s)' % (eur(qty), eur(qlo or 0), eur(qhi or 0)),
                  '- Neighbourhoods: %d' % nb,
                  '- Residents of these neighbourhoods (people concerned; one tree package per neighbourhood, so nobody is '
                  'counted twice): %s (modelled estimate, +-25-30%% per neighbourhood; not a count of those who benefit)'
                  % eur(sum(p['people'] or 0.0 for p in sel))]
        elif I == 'roof_cool_or_green_municipal':
            L += ['- Matched roof footprint: %s m2 (an UPPER bound of the roof area that can be treated: the flat and usable '
                  'share is unknown)' % eur(qty),
                  '- Neighbourhoods: %d' % nb,
                  '- Buildings: %d (matched municipal buildings, a LOWER bound: not every municipal building is matched)'
                  % sum(p['sites_n'] for p in sel)]
        else:
            L += ['- Quantity: %s %s' % (g(qty), sel[0]['unit'] if sel else ''), '- Neighbourhoods: %d' % nb]
        if t['skipped']:
            f = t['skipped'][0]
            L.append('- Did not fit in what was left: %d packages (total central cost %s EUR); the first one was rank %d, %s '
                     '(%s EUR)' % (len(t['skipped']), eur(sum(p['cost']['central'] for p in t['skipped'])), f['rank'],
                                   f['neighbourhood'], eur(f['cost']['central'])))
        if t['no_cost']:
            L.append('- Left out because no price exists: %d packages' % len(t['no_cost']))
        L.append('')
        if I == 'roof_cool_or_green_municipal':
            L += ['| rank | neighbourhood | community | m2 roof footprint | buildings | cost central EUR (low-high) |',
                  '|---|---|---|---|---|---|']
        else:
            L += ['| rank | neighbourhood | community | quantity (central) | cost central EUR (low-high) | people concerned |',
                  '|---|---|---|---|---|---|']
        for p in sel:
            c = p['cost']
            cr = '%s (%s-%s)' % (eur(c['central']), eur(c['low']), eur(c['high'])) if (c['low'] is not None and c['high'] is not None) \
                else eur(c['central'])
            if I == 'roof_cool_or_green_municipal':
                L.append('| %d | %s | %s | %s | %d | %s |' % (p['rank'], p['neighbourhood'], p['community'], eur(p['q']['central']),
                                                           p['sites_n'], cr))
            else:
                L.append('| %d | %s | %s | %s %s | %s | %s |' % (
                    p['rank'], p['neighbourhood'], p['community'], g(p['q']['central']), p['unit'].split(' (')[0], cr,
                    eur(p['people']) if p['people'] is not None else 'n/a'))
        L.append('')
    L += ['Nothing here is a recommendation: it is the arithmetic of the data and the cited prices. Impacts are upper bounds '
          'transferred from other cities except where status=measured_athens (see README). The non-default comparison '
          'across interventions is `--rank-by people_per_eur`.']
    return '\n'.join(L) + '\n'


def render_budget_people_per_eur_md(res, data):
    recpop = dict((r['name'], r['pop_total']) for r in data['recs'])
    sel = res['selected']
    method = ('Method (--rank-by people_per_eur, a NON-DEFAULT comparison; the default is one budget per tab, see README): '
              'packages with a computed central cost and a people-concerned figure are '
              'ranked by people concerned per euro (central cost), ties by more people, then neighbourhood name, then '
              'intervention id. Packages are indivisible and are taken in that order while they fit. Greedy, not optimal. '
              'Costs are central values incl. VAT from the City contract (or the cited price where stated).')
    lines = ['# What a budget of %s EUR buys (reference calculation, people per euro across interventions)' % eur(res['budget']),
             '', method, '',
             '- Packages selected: %d (of %d with a price and a people figure)' % (len(sel), res['n_candidates']),
             '- Spent: %s EUR; left over: %s EUR' % (eur(res['spent']), eur(res['remaining']))]
    ppl_sum = sum((p['people'] or 0.0) for p in sel)
    uniq = sorted(set(p['neighbourhood'] for p in sel))
    uniq_pop = sum(recpop[n] for n in uniq if recpop[n] is not None)
    lines += ['- Sum of "people concerned" over packages: %s (packages overlap and are NOT additive; the same residents can be '
              'counted in several packages)' % eur(ppl_sum),
              '- Residents of the %d neighbourhoods touched (each counted once): %s (single-neighbourhood error +-25-30%%)'
              % (len(uniq), eur(uniq_pop)), '']
    by = {}
    for p in sel:
        d = by.setdefault(p['intervention_id'], [0, 0.0, 0.0])
        d[0] += 1
        d[1] += p['cost']['central']
        d[2] += p['people'] or 0.0
    lines += ['## By intervention', '', '| intervention | packages | cost EUR | people concerned (overlapping) |', '|---|---|---|---|']
    for iid in sorted(by):
        lines.append('| %s | %d | %s | %s |' % (iid, by[iid][0], eur(by[iid][1]), eur(by[iid][2])))
    lines += ['', '## Selected packages', '',
              '| # | neighbourhood | community | intervention | quantity | cost central EUR (low-high) | people concerned | people per 1000 EUR |',
              '|---|---|---|---|---|---|---|---|']
    for i, p in enumerate(sel, 1):
        c = p['cost']
        rng = ''
        if c['low'] is not None and c['high'] is not None:
            rng = ' (%s-%s)' % (eur(c['low']), eur(c['high']))
        lines.append('| %d | %s | %s | %s | %s %s | %s%s | %s | %s |' % (
            i, p['neighbourhood'], p['community'], p['intervention_id'], g(p['q']['central']), p['unit'].split(' (')[0],
            eur(c['central']), rng, eur(p['people']) if p['people'] is not None else 'n/a',
            ('%.2f' % p['ppk']) if p['ppk'] is not None else 'n/a'))
    lines += ['', '## Left out because they cannot be ranked (no price, or no people-concerned figure)', '']
    if res['no_price']:
        lines += ['| intervention | packages left out | people concerned (overlapping) | why |', '|---|---|---|---|']
        for iid in sorted(res['no_price']):
            d = res['no_price'][iid]
            lines.append('| %s | %d | %s | %s |' % (iid, d['n'], eur(d['people']), d['reason']))
    else:
        lines.append('None.')
    lines += ['', '## Left out because they did not fit in the remaining budget', '',
              '%d priced packages did not fit (total central cost %s EUR).' % (
                  len(res['skipped']), eur(sum(p['cost']['central'] for p in res['skipped']))), '',
              'Nothing here is a recommendation: it is the arithmetic of the data and the cited prices. Impacts are upper bounds '
              'transferred from other cities except where status=measured_athens (see README).']
    return '\n'.join(lines) + '\n'


# --------------------------------------------------------------------- output
PKG_COLS = [
    ('package_id', lambda p: p['package_id']),
    ('neighbourhood', lambda p: p['neighbourhood']),
    ('community', lambda p: p['community']),
    ('intervention_id', lambda p: p['intervention_id']),
    ('eligibility_trigger', lambda p: p['eligibility_trigger']),
    ('quantity_unit', lambda p: p['unit']),
    ('quantity_low', lambda p: p['q']['low']),
    ('quantity_central', lambda p: p['q']['central']),
    ('quantity_high', lambda p: p['q']['high']),
    ('capacity_low', lambda p: p['cap']['low']),
    ('capacity_central', lambda p: p['cap']['central']),
    ('capacity_high', lambda p: p['cap']['high']),
    ('quantity_note', lambda p: p['quantity_note']),
    ('quantity_options', lambda p: p['quantity_options']),
    ('cost_low_eur', lambda p: p['cost']['low']),
    ('cost_central_eur', lambda p: p['cost']['central']),
    ('cost_high_eur', lambda p: p['cost']['high']),
    ('cost_status', lambda p: p['cost_status']),
    ('cost_basis', lambda p: p['cost_basis']),
    ('recurring_cost_eur_per_year_central', lambda p: p['recurring']),
    ('people_concerned', lambda p: p['people']),
    ('people_basis', lambda p: p['people_basis']),
    ('population_caveat', lambda p: p['people_caveat']),
    ('people_per_1000_eur', lambda p: p['ppk']),
    ('impact_up_to', lambda p: p['impact']),
    ('impact_baseline', lambda p: p['impact_baseline']),
    ('time_to_effect', lambda p: p['tte']),
    ('evidence_status', lambda p: p['evidence']),
    ('why_here', lambda p: p['why']),
    ('data_gaps', lambda p: p['gaps']),
    ('flags', lambda p: p['flags']),
    ('param_statuses_used', lambda p: p['statuses']),
    ('context_pm25_community_ugm3', lambda p: p['pm25']),
    ('need_score', lambda p: p['need_score']),
    ('people_percentile_within_intervention', lambda p: p['people_pct']),
    ('priority_score', lambda p: p['score']),
    ('score_basis', lambda p: p['score_basis']),
    ('sources', lambda p: p['sources']),
    ('rank_within_intervention', lambda p: p['rank']),
    ('sites_n', lambda p: p['sites_n']),
]


def jn(x):
    """Number for JSON: exactly the value written to the csv (same rounding), int when whole, None when empty."""
    s = cell(x)
    if s == '':
        return None
    f = float(s)
    return int(f) if f == int(f) else f


def impacts_json(I, P, sources):
    out = []
    for code, param, unit, src in IMPACT_META[I]:
        row = P.row(I, param)
        if code == 'pavement_surface_temp_under_shade':
            sun = P.val(I, param, 'central')
            shade = P.val(I, 'pavement_surface_temp_tree_shade_c', 'central')
            up, lo, hi = sun - shade, None, None
        else:
            lo, c, hi = num(row['low']), num(row['central']), num(row['high'])
            present = [v for v in (lo, c, hi) if v is not None]
            if not present:
                continue
            up = max(present)
        out.append({'metric_code': code, 'direction': 'down', 'value_up_to': jn(up), 'low': jn(lo), 'high': jn(hi),
                    'unit': unit, 'status': row['status'], 'source_code': src})
        sources.setdefault(src, {'ref': row['source_ref'], 'file': row['source_file']})
    return out


def build_json(data):
    """Light structured export for a web UI. Every number is the value written to packages.csv (same rounding)."""
    P = data['params']
    sources = {}
    interventions = {}
    for ru in data['rules']:
        I = ru['intervention_id']
        interventions[I] = {'label_code': I, 'unit': UNIT_CODE[ru['quantity_fn']],
                            'has_cost': any(p['cost']['central'] is not None for p in data['packages']
                                            if p['intervention_id'] == I)}
    pkgs = []
    for p in data['packages']:
        I = p['intervention_id']
        c = p['cost']
        pkgs.append({
            'neighbourhood': p['neighbourhood'], 'community': p['community'], 'intervention': I,
            'quantity': {'central': jn(p['q']['central']), 'low': jn(p['q']['low']), 'high': jn(p['q']['high']),
                         'unit': p['unit_code']},
            'capacity': jn(p['cap']['central']),
            'cost_eur': ({'central': jn(c['central']), 'low': jn(c['low']), 'high': jn(c['high'])}
                         if c['central'] is not None else None),
            'people_concerned': jn(p['people']), 'people_basis_code': p['people_basis_code'],
            'priority_score': jn(p['score']), 'rank_within_intervention': p['rank'], 'sites_n': p['sites_n'],
            'time_to_effect_years': {'low': jn(p['tte_years']['low']), 'high': jn(p['tte_years']['high'])},
            'evidence_code': p['evidence_code'],
            'impacts': impacts_json(I, P, sources),
            'why_here': [{'indicator_code': it['indicator_code'], 'value': jn(it['value']), 'unit': it['unit'],
                          'percentile': it['percentile']} for it in p['why_items']],
            'data_gaps': list(p['gap_codes']),
            'flags': [f for f in p['flags'].split(';') if f],
        })
    return {'generated_from': {'packages': 'engine/packages.csv', 'need_indicators': 'engine/need_indicators.csv',
                               'params': 'engine/params.csv', 'rules': 'engine/rules.csv',
                               'need_defs': 'engine/need_defs.csv', 'labels_el': 'engine/labels_el.csv',
                               'generator': 'engine/generate_packages.py'},
            'interventions': interventions, 'packages': pkgs, 'sources': dict(sorted(sources.items()))}


def write_json(path, doc):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')) + '\n')


def write_csv(path, header, rows):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def packages_rows(data):
    return [[cell(fn(p)) for _, fn in PKG_COLS] for p in data['packages']]


def need_rows(data):
    header = ['neighbourhood', 'community', 'community_id']
    for d in data['defs']:
        header += [d['indicator_id'] + '_value', d['indicator_id'] + '_pct']
    rows = []
    for rec in data['recs']:
        row = [rec['name'], rec['community'], cell(rec['community_id'])]
        for d in data['defs']:
            x = data['ind'][d['indicator_id']]
            row += [cell(x['value'][rec['name']]), cell(x['pct'][rec['name']])]
        rows.append(row)
    return header, rows


def render_package_md(p, rank):
    c = p['cost']
    if c['central'] is not None:
        rng = ''
        if c['low'] is not None and c['high'] is not None:
            rng = ' (low %s, high %s)' % (eur(c['low']), eur(c['high']))
        cost = '%s EUR central%s' % (eur(c['central']), rng)
    else:
        cost = 'NOT COMPUTED (%s)' % p['cost_status']
    L = ['### %d. %s: %s (%s)' % (rank, p['intervention_id'], p['neighbourhood'], p['community']), '',
         '- Priority score: %s (%s; need %s, people percentile %s)' % (
             '%.1f' % p['score'] if p['score'] is not None else 'n/a', p['score_basis'],
             '%.1f' % p['need_score'] if p['need_score'] is not None else 'n/a',
             '%.1f' % p['people_pct'] if p['people_pct'] is not None else 'n/a'),
         '- Quantity: %s (low %s, high %s) %s' % (g(p['q']['central']), g(p['q']['low']), g(p['q']['high']), p['unit']),
         '- Capacity figure: %s %s' % (g(p['cap']['central']), p['unit'].split(' (')[0]),
         '- Cost: %s' % cost,
         '- People concerned: %s (%s)' % (eur(p['people']) if p['people'] is not None else 'not available', p['people_basis']),
         '- People per 1000 EUR: %s' % ('%.2f' % p['ppk'] if p['ppk'] is not None else 'n/a (no cost)'),
         '- Impact (upper bounds): %s' % p['impact']]
    if p['impact_baseline']:
        L.append('- Baseline: %s' % p['impact_baseline'])
    L += ['- Time to effect: %s' % p['tte'],
          '- Evidence: %s' % p['evidence'],
          '- Why here: %s' % p['why'],
          '- Data gaps: %s' % p['gaps'],
          '- Flags: %s' % p['flags'],
          '- Population caveat: %s' % p['people_caveat'],
          '']
    if p['quantity_options']:
        L.insert(5, '- Other options: %s' % p['quantity_options'])
    return '\n'.join(L)


def sort_key_score(p):
    return (p['score'] is None, -(p['score'] or 0.0), -(p['people'] or 0.0), p['neighbourhood'], p['intervention_id'])


def render_top20_md(data):
    pk = data['packages']
    ranked = sorted(pk, key=sort_key_score)
    L = ['# Top 20 packages by priority score (reference calculation)', '',
         'Generated from data by engine/generate_packages.py. This is a proposal for the team, not a decision. '
         'Score per intervention (README, Priority score): trees = (w_need x need percentile among the tree packages + '
         'w_people x people percentile) / (w_need + w_people), the need score being the mean of the percentiles of tree '
         'cover and new trees per 1000 residents; roofs = need score only (tree cover and satellite surface temperature); '
         'the other interventions = (w_need x need_score + w_people x people_percentile) / (w_need + w_people). '
         'Percentiles are within the intervention, so scores of different interventions are not comparable and this mixed '
         'top 20 is an ordering aid only (see README, OPEN_QUESTIONS). The top 3 per intervention follow '
         'rank_within_intervention.', '',
         '## Counts', '', '| intervention | packages | with a cost | without a cost |', '|---|---|---|---|']
    for ru in data['rules']:
        I = ru['intervention_id']
        mine = [p for p in pk if p['intervention_id'] == I]
        withc = sum(1 for p in mine if p['cost']['central'] is not None)
        L.append('| %s | %d | %d | %d |' % (I, len(mine), withc, len(mine) - withc))
    L += ['', '## Top 20', '']
    for i, p in enumerate(ranked[:20], 1):
        L.append(render_package_md(p, i))
    L += ['## Top 3 per intervention', '']
    for ru in data['rules']:
        I = ru['intervention_id']
        mine = sorted([p for p in pk if p['intervention_id'] == I], key=lambda p: p['rank'])[:3]
        L.append('#### %s' % I)
        L.append('')
        for i, p in enumerate(mine, 1):
            L.append(render_package_md(p, i))
    return '\n'.join(L) + '\n'


def write_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    write_csv(os.path.join(outdir, 'packages.csv'), [c for c, _ in PKG_COLS], packages_rows(data))
    h, rows = need_rows(data)
    write_csv(os.path.join(outdir, 'need_indicators.csv'), h, rows)
    write_json(os.path.join(outdir, 'packages.json'), build_json(data))
    with open(os.path.join(outdir, 'packages_top20.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(render_top20_md(data))
    for amount, label in BUDGETS:
        write_budget(data, amount, outdir)


def budget_label(amount):
    for a, label in BUDGETS:
        if float(a) == float(amount):
            return label
    return ('%.2f' % float(amount)).rstrip('0').rstrip('.')


def write_budget(data, amount, outdir):
    """Default mode (one budget per tab): writes <outdir>/budget_<label>.md and returns its text."""
    text = render_budget_md(run_budget(data['packages'], amount, 'per_tab'), data)
    path = os.path.join(outdir, 'budget_%s.md' % budget_label(amount))
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    return text, path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--budget', type=float, default=None,
                    help='EUR; what this budget buys in EACH tab (trees, roofs) separately: printed, and written to '
                         '<out>/budget_<amount>.md; then exit')
    ap.add_argument('--rank-by', choices=RANK_BY, default='per_tab',
                    help='with --budget: per_tab (default, team decision 1528: one budget per tab, packages in '
                         'rank_within_intervention order) or people_per_eur (non-default comparison across '
                         'interventions; printed only)')
    ap.add_argument('--out', default=HERE, help='output directory (default: engine/)')
    args = ap.parse_args(argv)
    data = build()
    for n in data['param_notes']:
        sys.stderr.write('params: %s\n' % n)
    if data['join_gaps']:
        sys.stderr.write('join gaps (value stays missing): %s\n' % data['join_gaps'])
    if args.budget is not None:
        if args.rank_by == 'per_tab':
            os.makedirs(args.out, exist_ok=True)
            text, path = write_budget(data, args.budget, args.out)
            sys.stdout.write(text)
            sys.stderr.write('written: %s\n' % path)
        else:
            sys.stdout.write(render_budget_md(run_budget(data['packages'], args.budget, args.rank_by), data))
        return 0
    write_all(data, args.out)
    pk = data['packages']
    sys.stdout.write('neighbourhoods: %d, packages: %d\n' % (len(data['recs']), len(pk)))
    for ru in data['rules']:
        I = ru['intervention_id']
        mine = [p for p in pk if p['intervention_id'] == I]
        withc = sum(1 for p in mine if p['cost']['central'] is not None)
        sys.stdout.write('  %-36s packages %3d  with cost %3d  without cost %3d\n' % (I, len(mine), withc, len(mine) - withc))
    return 0


if __name__ == '__main__':
    sys.exit(main())
