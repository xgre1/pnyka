#!/usr/bin/env python3
"""Plain-assert tests for the reference calculation. Run: python3 engine/test_engine.py"""
import csv
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_packages as E  # noqa: E402

ROOT = E.ROOT
DATA = E.build()
P = DATA['params']
PK = DATA['packages']
RULES = dict((r['intervention_id'], r) for r in DATA['rules'])
TREES, ROOFS = 'trees_pavement', 'roof_cool_or_green_municipal'
UNTOUCHED = ('cool_surface_schoolyard_playground', 'school_street', 'elderly_heat_support')

# Fingerprints computed from the outputs BEFORE the ranking change of 2026-11-21 (audit engine/validation/VERDICT.md),
# with the same hashing as _fingerprints() below. They pin (1) the three interventions the change must not touch,
# completely, and (2) every column that is not a score column, for all 547 packages (quantities, costs, people,
# impacts, sources, gaps, flags). If one of these fails, something other than the ranking changed.
FP_UNTOUCHED_CSV_ROWS = 'add2d85b64bcf9c1701f01bd1cca53f499aab8efc3d1f52eaaa051820ed1361b'
FP_UNTOUCHED_RANK_ORDER = '07ec1d88f458d96c1dafebdfcc1cdda336bc7937d3375f78458f2c9558ccabed'
FP_UNTOUCHED_JSON = '0460879dbf5cb47133a47be253048bc4ef72d08218e89e784a35b71e7b45e31d'
FP_FROZEN_COLS_ALL_ROWS = '6886589f107684d51dc83dd1091d504efef449e87c37a894a9a84fe52fe15cc8'
FP_FROZEN_JSON_ALL_PACKAGES = 'cb02a8c7c8bfaf9d6197765f835842e21d49512fd615049a1f00425f958cbed3'
SCORE_COLS = ('why_here', 'need_score', 'people_percentile_within_intervention', 'priority_score', 'score_basis',
              'rank_within_intervention')


def rd(rel):
    return E.read_csv(os.path.join(ROOT, rel))


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_shape():
    assert len(DATA['recs']) == 144, len(DATA['recs'])
    assert len(PK) > 0
    ids = set(p['package_id'] for p in PK)
    assert len(ids) == len(PK), 'duplicate package ids'
    assert set(RULES) == {'trees_pavement', 'roof_cool_or_green_municipal', 'cool_surface_schoolyard_playground',
                          'school_street', 'elderly_heat_support'}


def test_no_cost_without_unit_price():
    for I, ru in RULES.items():
        cps = [x.split('.', 1) for x in ru['cost_params'].split(';') if x]
        assert cps, I
        any_central_missing = any(P.val(a, b, 'central') is None for a, b in cps)
        for p in [q for q in PK if q['intervention_id'] == I]:
            if any_central_missing:
                assert p['cost']['central'] is None, (I, 'cost computed although a unit price is missing')
            for lvl in E.LV:
                if p['cost'][lvl] is not None:
                    for a, b in cps:
                        assert P.val(a, b, lvl) is not None, (I, lvl, b)
    # the interventions with a missing price must have empty cost columns in the written file
    with tempfile.TemporaryDirectory() as d:
        E.write_all(DATA, d)
        rows = E.read_csv(os.path.join(d, 'packages.csv'))
    for r in rows:
        if r['intervention_id'] == 'roof_cool_or_green_municipal':
            # the roof now has an (assumed) unit price: cost = matched footprint x price, all three levels
            assert r['cost_status'] == 'computed', r['package_id']
            for lvl in E.LV:
                assert abs(float(r['cost_%s_eur' % lvl]) - float(r['quantity_%s' % lvl]) *
                           P.val('roof_cool_or_green_municipal', 'roof_cost_per_m2_eur', lvl)) < 0.01, r['package_id']
        if r['intervention_id'] == 'elderly_heat_support':
            assert r['cost_low_eur'] == r['cost_central_eur'] == r['cost_high_eur'] == '', r['package_id']
            assert r['people_per_1000_eur'] == ''
            assert r['cost_status'].startswith('NOT COMPUTED')
        if r['intervention_id'] == 'cool_surface_schoolyard_playground' and P.val(
                'cool_surface_schoolyard_playground', 'yard_area_per_site_m2', 'central') is None:
            assert r['cost_central_eur'] == '', r['package_id']


def test_prices_match_cost_model():
    cm = rd('research/cost/cost_model.csv')

    def total(ptype, scen):
        v = [float(r['cost_eur']) for r in cm if r['planting_type'] == ptype and r['scenario'] == scen
             and r['component_id'] == 'TOTAL_incl_VAT']
        assert len(v) == 1, (ptype, scen, v)
        return v[0]

    for lvl in E.LV:
        assert abs(P.val('trees_pavement', 'cost_per_planted_tree_existing_pit_incl_vat_eur', lvl)
                   - total('2_existing_pavement_pit', lvl)) < 0.005, lvl
        assert abs(P.val('trees_pavement', 'cost_per_planted_tree_new_small_pit_incl_vat_eur', lvl)
                   - total('3a_new_pavement_pit_small', lvl)) < 0.005, lvl
    # independent recomputation of a tree package cost from cost_model.csv
    s = P.val('trees_pavement', 'share_new_small_pits', 'central')
    for p in [q for q in PK if q['intervention_id'] == 'trees_pavement'][:20]:
        for lvl in E.LV:
            unit = (1 - s) * total('2_existing_pavement_pit', lvl) + s * total('3a_new_pavement_pit_small', lvl)
            assert abs(p['cost'][lvl] - p['q'][lvl] * unit) < 0.01, (p['package_id'], lvl)
    # catalogue prices
    cat = dict((r['id'], r) for r in rd('research/interventions/catalogue.csv'))
    a3 = cat['A3']
    assert abs(P.val('school_street', 'cost_per_scheme_eur', 'low') - float(a3['cost_per_unit_low_eur'])) < 0.01
    assert abs(P.val('school_street', 'cost_per_scheme_eur', 'central') - float(a3['cost_per_unit_central_eur'])) < 0.01
    assert abs(P.val('school_street', 'cost_per_scheme_eur', 'high') - float(a3['cost_per_unit_high_eur'])) < 0.01
    assert abs(P.val('cool_surface_schoolyard_playground', 'cool_pavement_cost_eur_per_m2', 'central')
               - float(cat['H8']['cost_per_unit_central_eur'])) < 0.001
    assert cat['H10']['cost_per_unit_central_eur'] == ''   # the catalogue has no roof price; the roof price is an assumption
    roof = P.row('roof_cool_or_green_municipal', 'roof_cost_per_m2_eur')
    assert roof['status'] == 'assumption'
    assert [P.val('roof_cool_or_green_municipal', 'roof_cost_per_m2_eur', l) for l in E.LV] == [13.5, 20.0, 25.0]
    dflt = dict((r['parameter'], r) for r in rd('research/cost/roofs_pavements/defaults.csv'))['cool_roof_cost_installed']
    assert [float(dflt[l]) for l in E.LV] == [13.5, 20.0, 25.0]
    assert roof['source_file'] == 'research/cost/roofs_pavements/defaults.csv'


def test_quantities_within_capacity():
    for p in PK:
        for lvl in E.LV:
            q, c = p['q'][lvl], p['cap'][lvl]
            if q is not None and c is not None:
                assert 0 <= q <= c + 1e-9, (p['package_id'], lvl, q, c)
        if p['intervention_id'] == 'trees_pavement':
            assert p['q']['low'] <= p['q']['central'] <= p['q']['high'], p['package_id']
            assert 'capacity_unverified' in p['flags']


OUTPUT_FILES = ('packages.csv', 'packages.json', 'need_indicators.csv', 'packages_top20.md',
                'budget_250k.md', 'budget_1m.md', 'budget_5m.md')


def test_byte_identical_rerun():
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        E.write_all(E.build(), d1)
        E.write_all(E.build(), d2)
        assert sorted(os.listdir(d1)) == sorted(OUTPUT_FILES), sorted(os.listdir(d1))
        for f in sorted(os.listdir(d1)):
            assert sha(os.path.join(d1, f)) == sha(os.path.join(d2, f)), f
        for name in OUTPUT_FILES:
            committed = os.path.join(HERE, name)
            assert os.path.exists(committed), name
            assert sha(committed) == sha(os.path.join(d1, name)), \
                'engine/%s differs from a fresh run (rerun generate_packages.py)' % name
    # the cross-intervention need list contradicted the per-tab default: no longer written
    assert not os.path.exists(os.path.join(HERE, 'budget_1m_by_need.md'))


def test_every_package_has_source():
    for p in PK:
        assert p['sources'].strip(), p['package_id']
        first = p['sources'].split(' || ')[0].split(' :: ')[0]
        assert os.path.exists(os.path.join(ROOT, first)), (p['package_id'], first)
    for r in P.rows:
        assert r['source_file'], (r['intervention_id'], r['parameter'])
        assert os.path.exists(os.path.join(ROOT, r['source_file'])), r['source_file']
        assert r['source_ref'].strip(), (r['intervention_id'], r['parameter'])


def test_missing_params_have_empty_values():
    for r in P.rows:
        if r['status'] == 'missing':
            assert all(E.num(r[l]) is None for l in E.LV), (r['intervention_id'], r['parameter'])
        else:
            assert any(E.num(r[l]) is not None for l in E.LV), (r['intervention_id'], r['parameter'])


def test_assumptions_listed_in_readme():
    with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as fh:
        readme = fh.read()
    for r in P.rows:
        if r['status'] == 'assumption':
            key = '%s.%s' % (r['intervention_id'], r['parameter'])
            assert key in readme, 'assumption not listed in README: ' + key
    # every indicator used by a need list has a weight parameter (assumption)
    for ru in DATA['rules']:
        for iid in [x for x in ru['need_indicators'].split(';') if x]:
            assert P.row('_global', 'weight_need_indicator_' + iid)['status'] == 'assumption', iid


def test_totals_match_population_file():
    pop = rd('raw/population/population_by_neighbourhood.csv')
    total_file = sum(float(r['pop_total']) for r in pop)
    total_recs = sum(r['pop_total'] for r in DATA['recs'])
    assert abs(total_file - total_recs) < 1e-6, (total_file, total_recs)
    assert abs(total_file - 646085) < 1.5, total_file          # primary estimate (census rescaled per 1 km cell)
    assert abs(sum(float(r['es2021_total']) for r in pop) - 643542) < 1.5   # area-weighted census grid, finding 1445
    nd = rd('engine/need_indicators.csv') if os.path.exists(os.path.join(HERE, 'need_indicators.csv')) else None
    if nd is not None:
        assert abs(sum(float(r['residents_value']) for r in nd) - total_file) < 1.0
    cap_total = sum(r['pop_total_capacity_file'] for r in DATA['recs'])
    assert abs(cap_total - total_file) < 1.0, (cap_total, total_file)
    # 65+ and 0-14 totals too
    assert abs(sum(r['pop_65plus'] for r in DATA['recs']) - sum(float(r['pop_65plus']) for r in pop)) < 1e-6
    assert abs(sum(r['pop_0_14'] for r in DATA['recs']) - sum(float(r['pop_0_14']) for r in pop)) < 1e-6


def test_missing_stays_missing():
    nei = dict((E.norm(r['name']), r) for r in rd('neighbourhoods.csv'))
    n_with = 0
    for rec in DATA['recs']:
        raw = nei[rec['name']]['heat_night']
        v = DATA['ind']['night_temp_c']['value'][rec['name']]
        pc = DATA['ind']['night_temp_c']['pct'][rec['name']]
        if raw.strip() == '':
            assert v is None and pc is None, rec['name']
        else:
            n_with += 1
            assert v is not None and pc is not None
    assert 0 < n_with < 144
    for iid, x in DATA['ind'].items():
        for k in x['value']:
            assert (x['value'][k] is None) == (x['pct'][k] is None), (iid, k)
            if x['pct'][k] is not None:
                assert 0.0 <= x['pct'][k] <= 100.0
    # context-only indicator is never in any need list
    for ru in DATA['rules']:
        assert 'pm25_community_est' not in ru['need_indicators'].split(';')


def test_low_canopy_site_counts_match_sites_file():
    rows = rd('streets/sites_with_plantings.csv')
    inside = [r for r in rows if r['neighbourhood'].strip()]
    lt5 = [r for r in inside if E.num(r['canopy_pct_150m']) is not None and E.num(r['canopy_pct_150m']) < 5]
    assert sum(r['sites_all4_n'] for r in DATA['recs']) == len(inside)
    assert sum(r['sites_all4_canopy150m_lt5pct_n'] for r in DATA['recs']) == len(lt5)


def test_scores():
    for p in PK:
        if p['score'] is not None:
            assert 0.0 <= p['score'] <= 100.0, p['package_id']
        if p['people'] is None:
            assert p['score_basis'].startswith('need_only') or p['score_basis'].startswith('none')
        assert p['people_caveat']
    assert DATA['w']['need'] == 1 and DATA['w']['people'] == 1   # defaults equal (assumption rows)
    for ru in DATA['rules']:
        assert ru['score_method'] in E.SCORE_METHODS, ru['intervention_id']


def test_need_lists_after_audit():
    """Trees: tree cover + new trees per 1000 only; roofs: tree cover + satellite surface temperature only."""
    assert RULES[TREES]['need_indicators'].split(';') == ['tree_cover_stl2018_pct', 'new_trees_per_1000_residents']
    assert RULES[ROOFS]['need_indicators'].split(';') == ['tree_cover_stl2018_pct', 'surface_temp_lst_c']
    assert RULES[TREES]['score_method'] == 'balanced' and RULES[TREES]['rank_tie_break'] == ''
    assert RULES[ROOFS]['score_method'] == 'mean' and RULES[ROOFS]['rank_tie_break'] == 'roof_municipal_m2:desc'
    for I in UNTOUCHED:
        assert RULES[I]['score_method'] == 'mean' and RULES[I]['rank_tie_break'] == '', I
    # indicators that other rules still use stay defined
    defs = dict((d['indicator_id'], d) for d in DATA['defs'])
    for ru in DATA['rules']:
        for iid in [x for x in ru['need_indicators'].split(';') if x]:
            assert iid in defs, iid
    for iid in ('canopy_deficit_m2', 'pop_density_per_km2', 'night_temp_c', 'low_canopy_sites_share'):
        assert iid in defs, iid
    # the new indicator: from the treecover file, every neighbourhood has it, higher = more need
    d = defs['surface_temp_lst_c']
    assert d['source_file'] == 'treecover/treecover_by_neighbourhood.csv'
    assert d['source_field'] == 'city_lst_summer_day_2016_2020_c' and d['direction'] == 'higher_more_need'
    assert 'NOT air temperature' in d['note'] and 'EXTREMA' in d['note'] and '2016-2020' in d['note']
    tc = dict((E.norm(r['neighbourhood']), float(r['city_lst_summer_day_2016_2020_c'])) for r in rd(d['source_file']))
    vals = DATA['ind']['surface_temp_lst_c']['value']
    assert len(vals) == 144 and all(vals[n] == tc[n] for n in vals)
    # why_here: only the indicators actually used (plus the eligibility field)
    for p in PK:
        codes = [it['indicator_code'] for it in p['why_items']]
        if p['intervention_id'] == TREES:
            assert codes == ['canopy_deficit_m2', 'tree_cover_stl2018_pct', 'new_trees_per_1000_residents'], codes
            assert p['why_items'][0]['percentile'] is None      # eligibility only, not in the score
        elif p['intervention_id'] == ROOFS:
            assert codes == ['roof_municipal_m2', 'tree_cover_stl2018_pct', 'surface_temp_lst_c'], codes
            assert all(it['percentile'] is not None for it in p['why_items'][1:])
        if p['intervention_id'] in (TREES, ROOFS):
            assert 'night' not in p['why'] and 'density' not in p['why'] and 'share of sites' not in p['why'], p['package_id']


def _audit():
    sys.path.insert(0, os.path.join(HERE, 'validation'))
    import validation as V  # noqa: E402
    return V


def _fresh_rows():
    d = fresh_outputs()
    return dict((r['package_id'], r) for r in E.read_csv(os.path.join(d, 'packages.csv')))


def test_trees_rank_equals_audit_variant():
    """Trees reproduce engine/validation variant TC_balanced_cover_newtrees_1000: every one of the 124 ranks."""
    V = _audit()
    params, rules, defs, recs = V.load()
    w = lambda k: V.num(params[('_global', k)]['central'])
    comp = V.components(recs, V.TREES, ['tree_cover_stl2018_pct', 'new_trees_per_1000_residents'])
    sv = V.combine_balanced(comp, None, w('weight_need'), w('weight_people'))
    order = V.ranking(sv)
    rows = _fresh_rows()
    mine = dict((r['neighbourhood'], r) for r in rows.values() if r['intervention_id'] == V.TREES)
    assert set(mine) == set(sv) and len(sv) == 124
    for i, n in enumerate(order, 1):
        assert int(mine[n]['rank_within_intervention']) == i, (n, i, mine[n]['rank_within_intervention'])
        assert abs(float(mine[n]['priority_score']) - sv[n]) <= 5.1e-5, n
    with open(os.path.join(HERE, 'validation', 'results.json'), encoding='utf-8') as fh:
        res = json.load(fh)
    top20 = res[V.TREES]['proposed_variants']['TC_balanced_cover_newtrees_1000']['top20']
    assert [n for n in sorted(mine, key=lambda k: int(mine[k]['rank_within_intervention']))][:20] == top20
    # the formula: score = mean(need percentile among the packages, people percentile)
    for p in PK:
        if p['intervention_id'] == V.TREES:
            assert abs(p['score'] - (p['need_pct'] + p['people_pct']) / 2.0) < 1e-9
            assert p['score_basis'].startswith('need+people balanced')


def test_roofs_score_equals_audit_variant_ties_by_roof_area():
    """Roofs reproduce variant R6_tree_cover_plus_lst in score; ties: larger matched roof first, then name."""
    V = _audit()
    params, rules, defs, recs = V.load()
    w = lambda k: V.num(params[('_global', k)]['central'])
    comp = V.components(recs, V.ROOFS, ['tree_cover_stl2018_pct', 'lst_summer_day_c'])
    sv = V.combine(comp, None, w('weight_need'), w('weight_people'))
    audit_order = V.ranking(sv)
    rows = _fresh_rows()
    mine = dict((r['neighbourhood'], r) for r in rows.values() if r['intervention_id'] == V.ROOFS)
    assert set(mine) == set(sv) and len(sv) == 115
    for n in sv:
        assert abs(float(mine[n]['priority_score']) - sv[n]) <= 5.1e-5, n
    eng_order = sorted(mine, key=lambda k: int(mine[k]['rank_within_intervention']))
    # same score at every rank position: the orders differ only inside ties
    for a, b in zip(audit_order, eng_order):
        assert round(sv[a], 4) == round(sv[b], 4), (a, b)
    # ties at the 4 csv decimals: roof area descending, then name
    keys = [(-float(mine[n]['priority_score']), -float(mine[n]['quantity_central']), n) for n in eng_order]
    assert keys == sorted(keys)
    ties = sum(1 for a, b in zip(eng_order, eng_order[1:]) if mine[a]['priority_score'] == mine[b]['priority_score'])
    assert ties > 0
    for p in PK:
        if p['intervention_id'] == V.ROOFS:
            assert p['people'] is None and p['score'] == p['need_score']
            assert p['tie_value'] == p['q']['central']
    with open(os.path.join(HERE, 'validation', 'results.json'), encoding='utf-8') as fh:
        res = json.load(fh)
    assert set(eng_order[:20]) == set(res[V.ROOFS]['proposed_variants']['R6_tree_cover_plus_lst']['top20'])


def _fingerprints(d):
    rows = []
    with open(os.path.join(d, 'packages.csv'), encoding='utf-8', newline='') as fh:
        rows = list(csv.DictReader(fh))
    header = list(rows[0])
    with open(os.path.join(d, 'packages.json'), encoding='utf-8') as fh:
        doc = json.load(fh)
    h = lambda lines: hashlib.sha256('\n'.join(lines).encode('utf-8')).hexdigest()
    rk = []
    for I in UNTOUCHED:
        mine = sorted([r for r in rows if r['intervention_id'] == I], key=lambda r: int(r['rank_within_intervention']))
        rk += ['%s|%s|%s' % (r['package_id'], r['rank_within_intervention'], r['priority_score']) for r in mine]
    frozen = [c for c in header if c not in SCORE_COLS]
    strip = lambda p: dict((k, v) for k, v in p.items() if k not in ('priority_score', 'rank_within_intervention', 'why_here'))
    return {
        'untouched_csv_rows': h(['\x1f'.join(r[c] for c in header) for r in rows if r['intervention_id'] in UNTOUCHED]),
        'untouched_rank_order': h(rk),
        'untouched_json': h([json.dumps(p, ensure_ascii=False, separators=(',', ':'))
                             for p in doc['packages'] if p['intervention'] in UNTOUCHED]),
        'frozen_cols_all_rows': h(['\x1f'.join(r[c] for c in frozen) for r in rows]),
        'frozen_json_all_packages': h([json.dumps(strip(p), ensure_ascii=False, separators=(',', ':'))
                                       for p in doc['packages']]),
    }


def test_untouched_interventions_unchanged():
    fp = _fingerprints(fresh_outputs())
    assert fp['untouched_rank_order'] == FP_UNTOUCHED_RANK_ORDER, 'rank order or score of an untouched intervention changed'
    assert fp['untouched_csv_rows'] == FP_UNTOUCHED_CSV_ROWS, 'a csv row of an untouched intervention changed'
    assert fp['untouched_json'] == FP_UNTOUCHED_JSON, 'a json package of an untouched intervention changed'


def test_quantities_costs_impacts_unchanged():
    fp = _fingerprints(fresh_outputs())
    assert fp['frozen_cols_all_rows'] == FP_FROZEN_COLS_ALL_ROWS, 'a non-score column of packages.csv changed'
    assert fp['frozen_json_all_packages'] == FP_FROZEN_JSON_ALL_PACKAGES, 'a non-score key of packages.json changed'


def test_budget_per_tab():
    """Default mode: one budget per tab, rank_within_intervention order, indivisible, skip what does not fit."""
    assert E.RANK_BY[0] == 'per_tab' and 'need' not in E.RANK_BY
    for amount, label in E.BUDGETS:
        r1, r2 = E.run_budget(PK, amount), E.run_budget(PK, amount)
        assert r1['rank_by'] == 'per_tab'
        assert [t['intervention_id'] for t in r1['tabs']] == [TREES, ROOFS]
        for t, t2 in zip(r1['tabs'], r2['tabs']):
            I = t['intervention_id']
            assert [p['package_id'] for p in t['selected']] == [p['package_id'] for p in t2['selected']]
            assert t['spent'] <= amount + 1e-6, (I, amount)
            assert abs(t['spent'] - sum(p['cost']['central'] for p in t['selected'])) < 1e-6
            assert abs(t['spent'] + t['remaining'] - amount) < 1e-6
            assert all(p['intervention_id'] == I for p in t['selected'])
            ranks = [p['rank'] for p in t['selected']]
            assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks), (I, 'not in rank order')
            # independent replay of the rule
            left, want = float(amount), []
            for p in sorted([q for q in PK if q['intervention_id'] == I], key=lambda q: q['rank']):
                if p['cost']['central'] is None:
                    continue
                if p['cost']['central'] <= left + 1e-9:
                    want.append(p['package_id'])
                    left -= p['cost']['central']
            assert want == [p['package_id'] for p in t['selected']], (I, amount)
            # nothing that was skipped would still fit in what is left
            assert all(p['cost']['central'] > t['remaining'] + 1e-9 for p in t['skipped']), (I, amount)
            assert len(t['selected']) > 0, (I, amount)
        text = E.render_budget_md(r1, DATA)
        assert '## Δρόμοι' in text and '## Κτίρια' in text
        assert 'ASSUMPTION' in text and 'No people figure exists for roofs' in text
        assert 'rank_within_intervention' in text
        with open(os.path.join(HERE, 'budget_%s.md' % label), encoding='utf-8') as fh:
            assert fh.read() == text, label
    sizes = [len(E.run_budget(PK, a)['tabs'][0]['selected']) for a, _ in E.BUDGETS]
    assert sizes == sorted(sizes)
    # --budget N writes the same text it prints
    with tempfile.TemporaryDirectory() as d:
        text, path = E.write_budget(DATA, 750000, d)
        assert os.path.basename(path) == 'budget_750000.md'
        with open(path, encoding='utf-8') as fh:
            assert fh.read() == text


def test_budget_people_per_eur_comparison():
    """Non-default comparison across interventions, still available."""
    for amount, _ in E.BUDGETS:
        r1 = E.run_budget(PK, amount, 'people_per_eur')
        r2 = E.run_budget(PK, amount, 'people_per_eur')
        assert [p['package_id'] for p in r1['selected']] == [p['package_id'] for p in r2['selected']]
        assert r1['spent'] <= amount + 1e-6
        assert abs(r1['spent'] + r1['remaining'] - amount) < 1e-6
        for p in r1['selected']:
            assert p['cost']['central'] is not None and p['people'] is not None
        assert 'roof_cool_or_green_municipal' not in set(p['intervention_id'] for p in r1['selected'])
        assert 'elderly_heat_support' not in set(p['intervention_id'] for p in r1['selected'])
        assert 'roof_cool_or_green_municipal' in r1['no_price']      # priced, but no people figure: excluded with a reason
        assert 'people' in r1['no_price']['roof_cool_or_green_municipal']['reason']
    text = E.render_budget_md(E.run_budget(PK, 1000000, 'people_per_eur'), DATA)
    assert '--rank-by people_per_eur' in text and 'NON-DEFAULT' in text and '--rank-by need' not in text
    try:
        E.run_budget(PK, 1000000, 'need')
        raise AssertionError('rank_by need should be gone')
    except ValueError:
        pass


OLD_HEADER = [
    'package_id', 'neighbourhood', 'community', 'intervention_id', 'eligibility_trigger', 'quantity_unit',
    'quantity_low', 'quantity_central', 'quantity_high', 'capacity_low', 'capacity_central', 'capacity_high',
    'quantity_note', 'quantity_options', 'cost_low_eur', 'cost_central_eur', 'cost_high_eur', 'cost_status',
    'cost_basis', 'recurring_cost_eur_per_year_central', 'people_concerned', 'people_basis', 'population_caveat',
    'people_per_1000_eur', 'impact_up_to', 'impact_baseline', 'time_to_effect', 'evidence_status', 'why_here',
    'data_gaps', 'flags', 'param_statuses_used', 'context_pm25_community_ugm3', 'need_score',
    'people_percentile_within_intervention', 'priority_score', 'score_basis', 'sources']
NEW_COLS = ['rank_within_intervention', 'sites_n']
JSON_TOP_KEYS = ['generated_from', 'interventions', 'packages', 'sources']
JSON_PACKAGE_KEYS = ['neighbourhood', 'community', 'intervention', 'quantity', 'capacity', 'cost_eur', 'people_concerned',
                     'people_basis_code', 'priority_score', 'rank_within_intervention', 'sites_n', 'time_to_effect_years',
                     'evidence_code', 'impacts', 'why_here', 'data_gaps', 'flags']


def fresh_outputs():
    d = tempfile.mkdtemp()
    E.write_all(DATA, d)
    return d


def test_old_columns_unchanged_new_ones_at_end():
    d = fresh_outputs()
    with open(os.path.join(d, 'packages.csv'), newline='', encoding='utf-8') as fh:
        header = next(csv.reader(fh))
    assert header[:len(OLD_HEADER)] == OLD_HEADER, 'an existing column was renamed, removed or reordered'
    assert header[len(OLD_HEADER):] == NEW_COLS, header[len(OLD_HEADER):]
    assert [c for c, _ in E.PKG_COLS] == header


def test_json_keys_unchanged():
    d = fresh_outputs()
    with open(os.path.join(d, 'packages.json'), encoding='utf-8') as fh:
        doc = json.load(fh)
    assert list(doc) == JSON_TOP_KEYS
    assert list(doc['generated_from']) == ['packages', 'need_indicators', 'params', 'rules', 'need_defs', 'labels_el',
                                           'generator']
    for v in doc['interventions'].values():
        assert list(v) == ['label_code', 'unit', 'has_cost']
    for p in doc['packages']:
        assert list(p) == JSON_PACKAGE_KEYS, list(p)
        assert list(p['quantity']) == ['central', 'low', 'high', 'unit']
        assert list(p['time_to_effect_years']) == ['low', 'high']
        if p['cost_eur'] is not None:
            assert list(p['cost_eur']) == ['central', 'low', 'high']
        for m in p['impacts']:
            assert list(m) == ['metric_code', 'direction', 'value_up_to', 'low', 'high', 'unit', 'status', 'source_code']
        for w in p['why_here']:
            assert list(w) == ['indicator_code', 'value', 'unit', 'percentile']
    for s in doc['sources'].values():
        assert list(s) == ['ref', 'file']


def test_rank_is_permutation_per_intervention():
    d = fresh_outputs()
    rows = E.read_csv(os.path.join(d, 'packages.csv'))
    for I in RULES:
        mine = [r for r in rows if r['intervention_id'] == I]
        ranks = sorted(int(r['rank_within_intervention']) for r in mine)
        assert ranks == list(range(1, len(mine) + 1)), I
        by_rank = sorted(mine, key=lambda r: int(r['rank_within_intervention']))
        if I == ROOFS:     # ties by matched roof area (= the quantity), larger first, then name
            keys = [(-float(r['priority_score']), -float(r['quantity_central']), r['neighbourhood'])
                    for r in by_rank if r['priority_score'] != '']
        else:
            keys = [(-float(r['priority_score']), r['neighbourhood']) for r in by_rank if r['priority_score'] != '']
        assert keys == sorted(keys), (I, 'rank is not score descending with the tie-break of rules.csv')
    for r in rows:
        assert r['sites_n'] != '' and int(r['sites_n']) >= 0


def test_sites_n_matches_capacity_file():
    cap = dict((E.norm(r['name']), r) for r in rd('capacity/capacity_by_neighbourhood.csv'))
    for p in PK:
        c = cap[p['neighbourhood']]
        I = p['intervention_id']
        f = lambda k: int(float(c[k] or 0))
        want = {'roof_cool_or_green_municipal': f('schools_buildings_n') + f('municipal_other_buildings_n'),
                'school_street': f('sites_schools_n'), 'elderly_heat_support': f('sites_elderly_clubs_n'),
                'cool_surface_schoolyard_playground': f('sites_schools_canopy150m_lt5pct_n') + f('sites_playgrounds_canopy150m_lt5pct_n'),
                'trees_pavement': f('sites_all4_canopy150m_lt5pct_n')}[I]
        assert p['sites_n'] == want, (p['package_id'], p['sites_n'], want)


def _json_and_csv():
    d = fresh_outputs()
    with open(os.path.join(d, 'packages.json'), encoding='utf-8') as fh:
        doc = json.load(fh)
    rows = E.read_csv(os.path.join(d, 'packages.csv'))
    return d, doc, rows


def _same(jv, cv):
    if cv == '':
        return jv is None
    return jv is not None and float(jv) == float(cv)


def test_json_numbers_equal_csv():
    d, doc, rows = _json_and_csv()
    assert list(doc) == ['generated_from', 'interventions', 'packages', 'sources']
    assert len(doc['packages']) == len(rows) == len(PK)
    for j, r in zip(doc['packages'], rows):
        assert (j['neighbourhood'], j['community'], j['intervention']) == (r['neighbourhood'], r['community'], r['intervention_id'])
        q = j['quantity']
        assert _same(q['central'], r['quantity_central']) and _same(q['low'], r['quantity_low']) and _same(q['high'], r['quantity_high'])
        assert _same(j['capacity'], r['capacity_central'])
        if r['cost_central_eur'] == '':
            assert j['cost_eur'] is None
        else:
            c = j['cost_eur']
            assert _same(c['central'], r['cost_central_eur']) and _same(c['low'], r['cost_low_eur']) and _same(c['high'], r['cost_high_eur'])
        assert _same(j['people_concerned'], r['people_concerned'])
        assert _same(j['priority_score'], r['priority_score'])
        assert j['rank_within_intervention'] == int(r['rank_within_intervention'])
        assert j['sites_n'] == int(r['sites_n'])
        assert [f for f in r['flags'].split(';') if f] == j['flags']
        for w in j['why_here']:
            if w['percentile'] is not None:
                assert ('need percentile %d)' % w['percentile']) in r['why_here'], (r['package_id'], w)
        assert j['why_here'][0]['value'] is not None
    for I, v in doc['interventions'].items():
        has = any(r['cost_central_eur'] != '' for r in rows if r['intervention_id'] == I)
        assert v['has_cost'] == has and v['label_code'] == I
    assert doc['interventions']['roof_cool_or_green_municipal']['has_cost'] is True
    assert doc['interventions']['elderly_heat_support']['has_cost'] is False
    # trees: temperature metrics only, never a health outcome
    for j in doc['packages']:
        if j['intervention'] == 'trees_pavement':
            assert all(m['unit'] == 'degC' for m in j['impacts']), j['neighbourhood']
        for m in j['impacts']:
            assert m['value_up_to'] is not None and m['status'] in E.STATUSES and m['source_code'] in doc['sources']


def codes_of(doc):
    k = {}
    add = lambda kind, c: k.setdefault(kind, set()).add(c) if c else None
    for i, v in doc['interventions'].items():
        add('intervention', v['label_code'])
        add('unit', v['unit'])
    for p in doc['packages']:
        add('intervention', p['intervention'])
        add('unit', p['quantity']['unit'])
        add('people_basis', p['people_basis_code'])
        add('evidence', p['evidence_code'])
        for m in p['impacts']:
            add('metric', m['metric_code'])
            add('status', m['status'])
            add('source', m['source_code'])
            add('unit', m['unit'])
        for w in p['why_here']:
            add('indicator', w['indicator_code'])
            add('unit', w['unit'])
        for gcode in p['data_gaps']:
            add('gap', gcode)
        for f in p['flags']:
            add('flag', f)
    for s in doc['sources']:
        add('source', s)
    return k


def test_every_json_code_has_a_greek_label():
    d, doc, rows = _json_and_csv()
    labels = E.read_csv(os.path.join(HERE, 'labels_el.csv'))
    assert list(labels[0]) == ['code', 'kind', 'label_el', 'long_el']
    codes = [r['code'] for r in labels]
    assert len(codes) == len(set(codes)), 'duplicate code in labels_el.csv'
    kinds = dict((r['code'], r['kind']) for r in labels)
    assert set(kinds.values()) <= {'intervention', 'indicator', 'metric', 'status', 'evidence', 'gap', 'flag',
                                   'people_basis', 'source', 'unit', 'list_meaning'}
    for kind, cs in codes_of(doc).items():
        for c in cs:
            assert c in kinds, ('no label for', kind, c)
            assert kinds[c] == kind, (c, kinds[c], kind)
    for r in labels:
        assert r['label_el'].strip(), r['code']
    # every indicator used in a need list has a label, the new one included
    for ru in DATA['rules']:
        for iid in [x for x in ru['need_indicators'].split(';') if x]:
            assert kinds.get(iid) == 'indicator', iid


def test_new_labels():
    lab = dict((r['code'], r) for r in E.read_csv(os.path.join(HERE, 'labels_el.csv')))
    s = lab['surface_temp_lst_c']
    assert s['kind'] == 'indicator' and s['label_el'] == 'Θερμοκρασία επιφάνειας από δορυφόρο'
    assert '2016' in s['long_el'] and '2020' in s['long_el'] and 'αέρα' in s['long_el']
    assert lab['list_meaning_trees']['kind'] == lab['list_meaning_roofs']['kind'] == 'list_meaning'
    assert lab['list_meaning_trees']['label_el'] == 'Πολλοί κάτοικοι με λίγη σκιά'
    assert lab['list_meaning_roofs']['label_el'] == 'Δημοτικά κτίρια σε γειτονιές χωρίς πράσινο'
    for c in ('surface_temp_lst_c', 'list_meaning_trees', 'list_meaning_roofs'):
        for f in ('label_el', 'long_el'):
            assert lab[c][f].strip() and not re.search('[A-Za-z]', lab[c][f]), (c, f, 'Latin letters')
            assert not re.search(r'[^\w\s.,]', lab[c][f]), (c, f, 'only periods and commas as punctuation')


def test_labels_have_no_forbidden_characters():
    labels = E.read_csv(os.path.join(HERE, 'labels_el.csv'))
    for r in labels:
        for field in ('label_el', 'long_el'):
            v = r[field]
            assert '·' not in v and '·' not in v, (r['code'], field, 'middle dot')
            for ch in ';:()/-–—':
                assert ch not in v, (r['code'], field, ch)
    # statuses read as agreed
    st = dict((r['code'], r['label_el']) for r in labels if r['kind'] == 'status')
    assert st['measured_athens'] == 'μετρημένο στην Αθήνα' and st['assumption'] == 'υπόθεση' and st['missing'] == 'λείπει'
    assert st['published_elsewhere'] == 'δημοσιευμένο σε άλλη πόλη' and st['city_contract'] == 'από τη σύμβαση του Δήμου'
    for r in labels:
        if r['kind'] == 'metric':
            assert r['label_el'].startswith('Έως'), r['code']
            assert 'θάνατ' not in r['label_el'] or r['code'] == 'heatwave_excess_deaths_covered'


def test_byte_identical_rerun_csv_and_json():
    a, b = fresh_outputs(), fresh_outputs()
    for name in ('packages.csv', 'packages.json'):
        assert sha(os.path.join(a, name)) == sha(os.path.join(b, name)), name
    with open(os.path.join(a, 'packages.json'), 'rb') as fh:
        raw = fh.read()
    assert b'\r' not in raw and raw.endswith(b'}\n')
    assert raw.decode('utf-8') == json.dumps(json.loads(raw.decode('utf-8')), ensure_ascii=False, separators=(',', ':')) + '\n'


def test_roof_measured_impacts_first():
    d, doc, rows = _json_and_csv()
    I = 'roof_cool_or_green_municipal'
    want = [('classroom_air_temp_summer', 'classroom_air_temp_reduction_summer_degc'),
            ('roof_surface_temp', 'roof_surface_temp_reduction_degc')]
    n = 0
    for j in doc['packages']:
        if j['intervention'] != I:
            continue
        n += 1
        im = j['impacts']
        assert [m['metric_code'] for m in im] == ['classroom_air_temp_summer', 'roof_surface_temp', 'building_cooling_load'], j['neighbourhood']
        for m, (code, param) in zip(im[:2], want):
            row = P.row(I, param)
            vals = [E.num(row[l]) for l in E.LV]
            assert m['status'] == 'measured_athens' and m['source_code'] == 'cool_roofs_kaisariani'
            assert m['direction'] == 'down' and m['unit'] == 'degC'
            assert m['value_up_to'] == max(v for v in vals if v is not None)
            assert _same(m['low'], row['low']) and _same(m['high'], row['high'])
        assert im[2]['status'] == 'published_elsewhere'
    assert n > 0
    assert doc['sources']['cool_roofs_kaisariani']['file'] == P.row(I, 'classroom_air_temp_reduction_summer_degc')['source_file']
    for r in rows:
        if r['intervention_id'] == I:
            t = r['impact_up_to']
            assert t.index('Classroom air temperature') < t.index('Roof surface temperature') < t.index('Cooling load')
            assert 'No street-level or health figure is claimed' in t


if __name__ == '__main__':
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_') and callable(f)]
    for n, f in tests:
        f()
        print('PASS', n)
    print('%d tests passed' % len(tests))
