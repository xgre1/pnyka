#!/usr/bin/env python3
"""Validation of the priority ranking of engine/generate_packages.py (trees and roofs tabs).

Python standard library only. No network. Deterministic (fixed seeds). Reads the engine inputs and
outputs, never writes outside engine/validation/. Run:

    python3 -I engine/validation/validation.py

Writes into engine/validation/: results.json, robust_core_trees.csv, robust_core_roofs.csv,
sensitivity_summary.csv, external_validation.csv, alternatives.csv. See README.md for each check.
"""
import bisect
import csv
import json
import math
import os
import random
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
ROOT = os.path.dirname(ENGINE)

N_RUNS = 2000
N_PERM = 10000
BUDGET = 1000000.0
SEED_WEIGHTS = 20261121
SEED_POP = 20261122
SEED_PERM = 20261123
SEED_MODERATE = 20261124
TREES, ROOFS = 'trees_pavement', 'roof_cool_or_green_municipal'
INTERVENTIONS = [TREES, ROOFS]


# ------------------------------------------------------------------ helpers
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
    return None if math.isnan(v) else v


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def fmt(x):
    if x is None:
        return ''
    if isinstance(x, float):
        return '%.4f' % x
    return x


def write_csv(name, header, rows):
    with open(os.path.join(HERE, name), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(header)
        for r in rows:
            w.writerow([fmt(x) for x in r])


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def dist_summary(xs):
    return {'mean': mean(xs), 'p5': quantile(xs, 0.05), 'p50': quantile(xs, 0.5),
            'p95': quantile(xs, 0.95), 'min': min(xs), 'max': max(xs), 'n': len(xs)}


def avg_ranks(xs):
    idx = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[idx[j + 1]] == xs[idx[i]]:
            j += 1
        a = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[idx[k]] = a
        i = j + 1
    return r


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if sa == 0 or sb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)


def spearman(da, db, keys=None):
    """Spearman over the keys where both dicts have a value. Returns (rho, n)."""
    keys = keys if keys is not None else [k for k in da if k in db]
    ks = [k for k in keys if da.get(k) is not None and db.get(k) is not None]
    if len(ks) < 3:
        return None, len(ks)
    return pearson(avg_ranks([da[k] for k in ks]), avg_ranks([db[k] for k in ks])), len(ks)


# -------------------------------------------------------------- engine logic
def pct_ranks(values, higher_more_need=True):
    """Exactly the engine's percentile: mid-rank among keys that HAVE a value, 0..100, 100 = most need."""
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


def minmax(values, higher):
    present = [v for v in values.values() if v is not None]
    lo, hi = min(present), max(present)
    out = {}
    for k, v in values.items():
        if v is None:
            out[k] = None
            continue
        x = 100.0 * (v - lo) / (hi - lo) if hi > lo else 50.0
        out[k] = x if higher else 100.0 - x
    return out


def zscores(values, higher):
    present = [v for v in values.values() if v is not None]
    m = sum(present) / len(present)
    s = math.sqrt(sum((x - m) ** 2 for x in present) / len(present))
    out = {}
    for k, v in values.items():
        out[k] = None if v is None else ((v - m) / s if s > 0 else 0.0) * (1.0 if higher else -1.0)
    return out


NORMS = {'pct': pct_ranks, 'minmax': minmax, 'z': zscores}


# ------------------------------------------------------------------- data
def load():
    params = dict(((r['intervention_id'], r['parameter']), r) for r in read_csv(os.path.join(ENGINE, 'params.csv')))
    rules = dict((r['intervention_id'], r) for r in read_csv(os.path.join(ENGINE, 'rules.csv')))
    defs = dict((r['indicator_id'], r) for r in read_csv(os.path.join(ENGINE, 'need_defs.csv')))
    cap = read_csv(os.path.join(ROOT, 'capacity/capacity_by_neighbourhood.csv'))
    pop = dict((norm(r['name']), r) for r in read_csv(os.path.join(ROOT, 'raw/population/population_by_neighbourhood.csv')))
    tc = dict((norm(r['neighbourhood']), r) for r in read_csv(os.path.join(ROOT, 'treecover/treecover_by_neighbourhood.csv')))
    nb = dict((norm(r['name']), r) for r in read_csv(os.path.join(ROOT, 'neighbourhoods.csv')))
    pl = dict((norm(r['name']), r) for r in read_csv(os.path.join(ROOT, 'athenstrees/plantings_by_neighbourhood.csv')))
    target = num(params[('_global', 'canopy_target_pct')]['central'])
    defcol = 'canopy_deficit_to_%dpct_m2' % int(target)
    recs = []
    for row in cap:
        name = norm(row['name'])

        def g(k):
            return num(row.get(k))
        p, t, n_, l_ = pop.get(name, {}), tc.get(name, {}), nb.get(name, {}), pl.get(name, {})
        r = {'name': name, 'community': row['community'],
             'area_km2': g('area_km2'), 'area_m2': g('area_m2'),
             'canopy_deficit_m2': g(defcol), 'chm_canopy_m2': g('canopy_chm_ge3m_m2'),
             'pop_total': num(p.get('pop_total')), 'pop_0_14': num(p.get('pop_0_14')),
             'pop_65plus': num(p.get('pop_65plus')), 'pop_density_per_km2': num(p.get('pop_density_per_km2')),
             'stl_pct': num(t.get('ua_stl2018_pct')), 'lst': num(t.get('city_lst_summer_day_2016_2020_c')),
             'wc2021': num(t.get('wc2021_tree_pct')), 'chm3': num(t.get('metachm_ge3m_pct')),
             'heat_night': num(n_.get('heat_night')), 'heat_daily_max': num(n_.get('heat_daily_max')),
             'trees_planted': num(l_.get('trees_planted_2024_2026'))}
        a, b = g('schools_roof_area_m2'), g('municipal_other_roof_area_m2')
        r['roof_municipal_m2'] = ((a or 0.0) + (b or 0.0)) if (a is not None or b is not None) else None
        r['buildings_n'] = (g('schools_buildings_n') or 0.0) + (g('municipal_other_buildings_n') or 0.0)
        tot, lt5 = g('sites_all4_n'), g('sites_all4_canopy150m_lt5pct_n')
        r['sites_all4_n'] = tot
        r['low_canopy_sites_n'] = lt5
        r['low_canopy_sites_share'] = (lt5 / tot) if (tot and lt5 is not None) else None
        r['schools_n'] = g('sites_schools_n')
        r['low_canopy_schools_n'] = g('sites_schools_canopy150m_lt5pct_n')
        r['user_sites_n'] = (g('sites_schools_n') or 0.0) + (g('sites_nurseries_n') or 0.0) + (g('sites_elderly_clubs_n') or 0.0)
        r['has_sensor'] = r['heat_night'] is not None
        recs.append(r)
    return params, rules, defs, recs


def new_trees_per_1000(r):
    pt = r['pop_total']
    return (r['trees_planted'] / pt * 1000.0) if (pt and r['trees_planted'] is not None) else None


# indicator id -> (value function, higher = more need). Engine ones first, then the extra ones of this audit.
IND = {
    'tree_cover_stl2018_pct': (lambda r: r['stl_pct'], False),
    'canopy_deficit_m2': (lambda r: r['canopy_deficit_m2'], True),
    'pop_density_per_km2': (lambda r: r['pop_density_per_km2'], True),
    'new_trees_per_1000_residents': (new_trees_per_1000, False),
    'night_temp_c': (lambda r: r['heat_night'], True),
    'low_canopy_sites_share': (lambda r: r['low_canopy_sites_share'], True),
    # extra (not in the engine)
    'canopy_deficit_pp': (lambda r: (r['canopy_deficit_m2'] / r['area_m2'] * 100.0) if r['area_m2'] else None, True),
    'lst_summer_day_c': (lambda r: r['lst'], True),
    'buildings_n': (lambda r: r['buildings_n'], True),
    'roof_municipal_m2': (lambda r: r['roof_municipal_m2'], True),
    'user_sites_n': (lambda r: r['user_sites_n'], True),
    'low_canopy_sites_n': (lambda r: r['low_canopy_sites_n'], True),
    'new_trees_per_km2': (lambda r: (r['trees_planted'] / r['area_km2']) if (r['area_km2'] and r['trees_planted'] is not None) else None, False),
}

ELIG = {TREES: lambda r: r['canopy_deficit_m2'] is not None and r['canopy_deficit_m2'] > 0,
        ROOFS: lambda r: r['roof_municipal_m2'] is not None and r['roof_municipal_m2'] > 0}
PEOPLE = {TREES: 'pop_total', ROOFS: None}


def components(recs, I, indicators, method='pct', people=True):
    """Normalised indicator values (over all 144, as the engine) + normalised people (over the packages)."""
    elig = [r for r in recs if ELIG[I](r)]
    names = [r['name'] for r in elig]
    f = NORMS[method]
    ind = {}
    for k in indicators:
        fn, higher = IND[k]
        ind[k] = f(dict((r['name'], fn(r)) for r in recs), higher)
    pp = None
    if people and PEOPLE[I]:
        pp = f(dict((r['name'], r[PEOPLE[I]]) for r in elig), True)
    return {'I': I, 'names': names, 'ind': ind, 'indicators': list(indicators), 'pp': pp}


def combine(comp, w_ind=None, w_need=1.0, w_people=1.0, detail=False):
    out, det = {}, {}
    for n in comp['names']:
        num_, den, terms = 0.0, 0.0, {}
        for k in comp['indicators']:
            v = comp['ind'][k][n]
            if v is None:
                continue
            w = w_ind[k] if w_ind else 1.0
            num_ += w * v
            den += w
            terms[k] = w * v
        need = num_ / den if den > 0 else None
        pp = comp['pp'][n] if comp['pp'] is not None else None
        if need is not None and pp is not None:
            s = (w_need * need + w_people * pp) / (w_need + w_people)
            fn_, fp = w_need / (w_need + w_people), w_people / (w_need + w_people)
        elif need is not None:
            s, fn_, fp = need, 1.0, 0.0
        elif pp is not None:
            s, fn_, fp = pp, 0.0, 1.0
        else:
            s, fn_, fp = None, 0.0, 0.0
        out[n] = s
        if detail:
            t = dict((k, fn_ * v / den) for k, v in terms.items()) if den > 0 else {}
            if pp is not None:
                t['people'] = fp * pp
            det[n] = {'need': need, 'pp': pp, 'score': s, 'n_ind': len(terms), 'terms': t}
    return (out, det) if detail else out


def combine_balanced(comp, w_ind=None, w_need=1.0, w_people=1.0):
    """Proposed fix (not in the engine): the need score is re-expressed as a percentile among the packages
    before it is combined with the people percentile, so need and people have the same spread and equal
    nominal weights become equal effective weights. Without a people part the order equals the need order."""
    c2 = dict(comp)
    c2['pp'] = None
    need = combine(c2, w_ind)
    npct = pct_ranks(need, True)
    if comp['pp'] is None:
        return npct
    out = {}
    for n in comp['names']:
        a, b = npct[n], comp['pp'][n]
        if a is not None and b is not None:
            out[n] = (w_need * a + w_people * b) / (w_need + w_people)
        else:
            out[n] = a if a is not None else b
    return out


def ranking(scores):
    return sorted(scores, key=lambda n: (scores[n] is None, -round(scores[n] or 0.0, 4), n))


def rank_by_value(names, val, higher_first):
    """Naive single-variable ranking; ties broken by name as in the engine; missing last."""
    return sorted(names, key=lambda n: (val[n] is None, -(val[n] or 0.0) if higher_first else (val[n] or 0.0), n))


def overlap(a, b, k):
    return len(set(a[:k]) & set(b[:k]))


def budget_select(order, cost, budget=BUDGET):
    rem, sel = budget, []
    for n in order:
        c = cost.get(n)
        if c is None:
            continue
        if c <= rem + 1e-9:
            sel.append(n)
            rem -= c
    return sel


def dirichlet(rng, k):
    g = [rng.gammavariate(1.0, 1.0) for _ in range(k)]
    s = sum(g)
    return [x / s for x in g]


def perturb_population(recs, rng, lo=0.7, hi=1.3):
    out = []
    for r in recs:
        f = rng.uniform(lo, hi)
        q = dict(r)
        for k in ('pop_total', 'pop_0_14', 'pop_65plus', 'pop_density_per_km2'):
            if q[k] is not None:
                q[k] = q[k] * f
        out.append(q)
    return out


# ------------------------------------------------------------------- main
def main():
    params, rules, defs, recs = load()
    byname = dict((r['name'], r) for r in recs)

    def W(p):
        return num(params[('_global', p)]['central'])
    w_need0, w_people0 = W('weight_need'), W('weight_people')
    pk = read_csv(os.path.join(ENGINE, 'packages.csv'))
    R = {'meta': {'n_runs': N_RUNS, 'n_perm': N_PERM, 'budget_eur': BUDGET,
                  'seeds': {'weights': SEED_WEIGHTS, 'population': SEED_POP, 'permutation': SEED_PERM,
                            'moderate_weights': SEED_MODERATE},
                  'population_factor': 'independent uniform(0.7, 1.3) per neighbourhood on pop_total, pop_0_14, '
                                       'pop_65plus, pop_density_per_km2 (so new_trees_per_1000 scales by 1/f)',
                  'weights_random': 'need-indicator weights ~ Dirichlet(1,..,1); (w_need, w_people) ~ Dirichlet(1,1)',
                  'weights_moderate': 'each weight log-uniform in [1/2, 2] (supplementary)',
                  'budget_rule': 'packages taken in rank order within the intervention, central cost from packages.csv, '
                                 'indivisible, skipped if it does not fit (same greedy rule as the engine)'}}
    sens_rows, ext_rows, alt_rows = [], [], []
    muni_pop = sum(r['pop_total'] for r in recs)
    muni_65 = sum(r['pop_65plus'] for r in recs)
    muni_lcs = sum(r['low_canopy_schools_n'] or 0 for r in recs)
    R['meta']['municipal_totals'] = {'residents': muni_pop, 'residents_65plus': muni_65,
                                     'low_canopy_schools': muni_lcs, 'neighbourhoods': len(recs)}
    # how the validation variables relate to each other and to the score inputs (all 144, or the 77 sensors)
    V = R['validators_spearman'] = {}
    col = lambda k: dict((r['name'], r[k]) for r in recs)
    for a, b in (('lst', 'stl_pct'), ('lst', 'wc2021'), ('lst', 'chm3'), ('lst', 'heat_night'), ('lst', 'heat_daily_max'),
                 ('lst', 'pop_density_per_km2'), ('heat_night', 'stl_pct'), ('heat_night', 'wc2021'), ('heat_night', 'chm3'),
                 ('heat_night', 'pop_density_per_km2'), ('stl_pct', 'wc2021'), ('stl_pct', 'chm3'), ('wc2021', 'chm3'),
                 ('lst', 'buildings_n'), ('lst', 'roof_municipal_m2')):
        rho, n = spearman(col(a), col(b))
        V['%s~%s' % (a, b)] = {'rho': rho, 'n': n}

    for I in INTERVENTIONS:
        RI = R[I] = {}
        ind0 = [x for x in rules[I]['need_indicators'].split(';') if x]
        w_ind0 = dict((k, W('weight_need_indicator_' + k)) for k in ind0)
        comp0 = components(recs, I, ind0)
        base, det0 = combine(comp0, w_ind0, w_need0, w_people0, detail=True)
        order0 = ranking(base)
        names = comp0['names']
        rank0 = dict((n, i + 1) for i, n in enumerate(order0))
        mine = dict((norm(p['neighbourhood']), p) for p in pk if p['intervention_id'] == I)
        cost = dict((n, num(p['cost_central_eur'])) for n, p in mine.items())

        # ---------------------------------------------- 0. reproduction check
        same = set(mine) == set(names)
        dmax_score = max(abs(base[n] - num(mine[n]['priority_score'])) for n in names) if same else None
        dmax_need = max(abs(det0[n]['need'] - num(mine[n]['need_score'])) for n in names) if same else None
        dmax_pp = max(abs((det0[n]['pp'] or 0) - (num(mine[n]['people_percentile_within_intervention']) or 0))
                      for n in names) if same else None
        rank_mismatch = sum(1 for n in names if rank0[n] != int(mine[n]['rank_within_intervention'])) if same else None
        RI['reproduction'] = {'n_packages_engine': len(mine), 'n_packages_reimplemented': len(names),
                              'same_package_set': same,
                              'max_abs_diff_priority_score': dmax_score, 'max_abs_diff_need_score': dmax_need,
                              'max_abs_diff_people_percentile': dmax_pp, 'rank_mismatches': rank_mismatch,
                              'note': 'packages.csv stores 4 decimals, so a max diff <= 0.00005 is exact reproduction'}
        if not (same and dmax_score <= 5.1e-5 and rank_mismatch == 0):
            raise SystemExit('REPRODUCTION FAILED for %s: %s' % (I, RI['reproduction']))

        # ---------------------------------------------- 1. construct audit
        A = RI['construct'] = {}
        cols = list(ind0) + (['people_pop_total'] if PEOPLE[I] else [])
        pctd = dict((k, comp0['ind'][k]) for k in ind0)
        if PEOPLE[I]:
            pctd['people_pop_total'] = comp0['pp']
        corr = {}
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                rho, n = spearman(pctd[a], pctd[b], names)
                corr['%s~%s' % (a, b)] = {'rho': rho, 'n': n}
        A['spearman_between_need_percentiles_over_packages'] = corr
        A['spearman_note'] = ('computed on the need-oriented percentiles used in the score (positive = both point at '
                              'the same neighbourhoods), over the packages of the tab where both exist')
        A['missing'] = dict((k, {'missing_of_144': sum(1 for r in recs if comp0['ind'][k][r['name']] is None),
                                 'missing_of_packages': sum(1 for n in names if comp0['ind'][k][n] is None)})
                            for k in ind0)
        nind = {}
        for n in names:
            nind.setdefault(det0[n]['n_ind'], []).append(n)
        A['by_number_of_indicators'] = {}
        for k in sorted(nind):
            grp = nind[k]
            A['by_number_of_indicators'][str(k)] = {
                'n': len(grp), 'score_mean': mean([base[n] for n in grp]), 'score_sd': sd([base[n] for n in grp]),
                'need_mean': mean([det0[n]['need'] for n in grp]), 'need_sd': sd([det0[n]['need'] for n in grp]),
                'in_top10': sum(1 for n in order0[:10] if n in grp), 'in_top20': sum(1 for n in order0[:20] if n in grp),
                'in_top30': sum(1 for n in order0[:30] if n in grp),
                'in_bottom20': sum(1 for n in order0[-20:] if n in grp)}
        # sensor vs no sensor; is the no-sensor share in the top 20 unusual? (permutation over the packages)
        nos = set(n for n in names if not byname[n]['has_sensor'])
        rng = random.Random(SEED_PERM)
        exp20 = 20.0 * len(nos) / len(names)
        obs = sum(1 for n in order0[:20] if n in nos)
        dist = [sum(1 for n in rng.sample(names, 20) if n in nos) for _ in range(N_PERM)]
        A['no_sensor_in_top20'] = {'observed': obs, 'expected': exp20,
                                   'p_two_sided': (sum(1 for d in dist if abs(d - exp20) >= abs(obs - exp20) - 1e-9) + 1)
                                   / (N_PERM + 1.0),
                                   'n_no_sensor_packages': len(nos), 'n_packages': len(names)}
        # counterfactual: the sensor neighbourhoods scored WITHOUT night_temp (same footing as the others)
        ind_nn = [k for k in ind0 if k != 'night_temp_c']
        s_nn = combine(components(recs, I, ind_nn), dict((k, w_ind0[k]) for k in ind_nn), w_need0, w_people0)
        o_nn = ranking(s_nn)
        r_nn = dict((n, i + 1) for i, n in enumerate(o_nn))
        sens = [n for n in names if byname[n]['has_sensor']]
        A['night_temp_effect'] = {
            'n_sensor_packages': len(sens),
            'mean_score_change_when_night_added_sensor_nbhds': mean([base[n] - s_nn[n] for n in sens]),
            'mean_abs_score_change_sensor_nbhds': mean([abs(base[n] - s_nn[n]) for n in sens]),
            'mean_abs_rank_change_all_packages': mean([abs(rank0[n] - r_nn[n]) for n in names]),
            'max_abs_rank_change': max(abs(rank0[n] - r_nn[n]) for n in names),
            'top20_overlap_with_and_without_night': overlap(order0, o_nn, 20),
            'spearman_night_pct_vs_mean_of_other_need_pcts': spearman(
                comp0['ind']['night_temp_c'],
                dict((n, mean([comp0['ind'][k][n] for k in ind_nn])) for n in names), sens)[0]}
        # area effects
        area = dict((n, byname[n]['area_km2']) for n in names)
        med_area = quantile([area[n] for n in names], 0.5)
        A['area'] = {
            'spearman_canopy_deficit_m2_vs_area': spearman(dict((n, byname[n]['canopy_deficit_m2']) for n in names), area)[0],
            'spearman_residents_vs_area': spearman(dict((n, byname[n]['pop_total']) for n in names), area)[0],
            'spearman_priority_score_vs_area': spearman(base, area)[0],
            'area_km2_median_all_packages': med_area,
            'area_km2_mean_top20': mean([area[n] for n in order0[:20]]),
            'area_km2_mean_all_packages': mean([area[n] for n in names]),
            'top20_larger_than_median_area': sum(1 for n in order0[:20] if area[n] > med_area),
            'spearman_roof_m2_vs_area': spearman(dict((n, byname[n]['roof_municipal_m2']) for n in names), area)[0],
            'spearman_buildings_vs_area': spearman(dict((n, byname[n]['buildings_n']) for n in names), area)[0]}
        if I == TREES:
            A['area']['spearman_canopy_deficit_pct_vs_tree_cover_pct'] = spearman(
                comp0['ind']['canopy_deficit_m2'], comp0['ind']['tree_cover_stl2018_pct'], names)[0]
            alt = [('canopy_deficit_pp' if k == 'canopy_deficit_m2' else k) for k in ind0]
            s_pp = combine(components(recs, I, alt), None, w_need0, w_people0)
            A['area']['variant_deficit_per_area_instead_of_m2'] = {
                'top20_overlap': overlap(order0, ranking(s_pp), 20), 'spearman': spearman(base, s_pp)[0],
                'spearman_deficit_pp_vs_metachm_cover': spearman(
                    dict((n, IND['canopy_deficit_pp'][0](byname[n])) for n in names),
                    dict((n, byname[n]['chm3']) for n in names))[0],
                'spearman_deficit_pp_vs_stl_cover': spearman(
                    dict((n, IND['canopy_deficit_pp'][0](byname[n])) for n in names),
                    dict((n, byname[n]['stl_pct']) for n in names))[0]}
        # variance decomposition: share of the score variance carried by each term (sums to 1)
        terms = sorted(set(k for n in names for k in det0[n]['terms']))
        ms = mean([base[n] for n in names])
        vs = sum((base[n] - ms) ** 2 for n in names)
        contrib = {}
        for t in terms:
            vals = [det0[n]['terms'].get(t, 0.0) for n in names]
            mt = mean(vals)
            contrib[t] = sum((v - mt) * (base[n] - ms) for v, n in zip(vals, names)) / vs
        A['variance_share_of_score_by_term'] = contrib
        A['spearman_score_vs_each_percentile'] = dict((k, spearman(base, comp0['ind'][k], names)[0]) for k in ind0)
        if PEOPLE[I]:
            A['spearman_score_vs_each_percentile']['people_pop_total'] = spearman(base, comp0['pp'])[0]
            A['population_twice'] = {
                'spearman_residents_vs_density': spearman(dict((n, byname[n]['pop_total']) for n in names),
                                                          dict((n, byname[n]['pop_density_per_km2']) for n in names))[0],
                'nominal_weight_of_population_terms': 'people 0.5 + density 0.1 + new trees per 1000 (pop in the '
                                                      'denominator) 0.1 = 0.7 at default weights with a sensor; '
                                                      '0.5 + 0.125 + 0.125 = 0.75 without'}
        A['mean_percentile_in_top20'] = dict((k, mean([comp0['ind'][k][n] for n in order0[:20]])) for k in ind0)
        if PEOPLE[I]:
            A['mean_percentile_in_top20']['people_pop_total'] = mean([comp0['pp'][n] for n in order0[:20]])
        A['ties'] = {'adjacent_equal_scores_in_top20': sum(1 for i in range(19)
                                                           if round(base[order0[i]], 4) == round(base[order0[i + 1]], 4)),
                     'distinct_scores_in_top20': len(set(round(base[n], 4) for n in order0[:20])),
                     'packages_sharing_the_rank20_score': sum(1 for n in names
                                                              if round(base[n], 4) == round(base[order0[19]], 4))}

        if I == ROOFS:
            lg = A['roof_logic'] = {}
            lstd = dict((n, byname[n]['lst']) for n in names)
            bld = dict((n, byname[n]['buildings_n']) for n in names)
            roofm = dict((n, byname[n]['roof_municipal_m2']) for n in names)
            for k in ind0:
                lg[k] = {'spearman_with_lst': spearman(comp0['ind'][k], lstd, names),
                         'spearman_with_buildings_n': spearman(comp0['ind'][k], bld, names),
                         'spearman_with_roof_m2': spearman(comp0['ind'][k], roofm, names)}
            lg['score'] = {'spearman_with_lst': spearman(base, lstd)[0],
                           'spearman_with_buildings_n': spearman(base, bld)[0],
                           'spearman_with_roof_m2': spearman(base, roofm)[0],
                           'spearman_with_user_sites_n': spearman(base, dict((n, byname[n]['user_sites_n']) for n in names))[0]}
            share1 = [n for n in names if byname[n]['low_canopy_sites_share'] == 1.0]
            lg['low_canopy_share_equal_1'] = {'n_packages': len(share1),
                                             'of_which_1_or_2_sites': sum(1 for n in share1 if (byname[n]['sites_all4_n'] or 0) <= 2),
                                             'in_top20': sum(1 for n in order0[:20] if n in share1)}
            lg['top20_with_1_building'] = sum(1 for n in order0[:20] if byname[n]['buildings_n'] <= 1)
            lg['all_packages_with_1_building'] = sum(1 for n in names if byname[n]['buildings_n'] <= 1)
            alts = {'heat_lst+buildings': ['lst_summer_day_c', 'buildings_n'],
                    'heat_lst+night+buildings': ['lst_summer_day_c', 'night_temp_c', 'buildings_n'],
                    'heat_lst+user_sites': ['lst_summer_day_c', 'user_sites_n']}
            lg['alternatives'] = {}
            for an, inds in alts.items():
                sa = combine(components(recs, I, inds))
                lg['alternatives'][an] = {'indicators': inds, 'spearman_with_current': spearman(base, sa)[0],
                                          'top20_overlap': overlap(order0, ranking(sa), 20)}

        # ---------------------------------------------- 2. sensitivity
        S = RI['sensitivity'] = {}
        base_sel = budget_select(order0, cost)
        S['budget_baseline'] = {'n_selected': len(base_sel), 'spent': sum(cost[n] for n in base_sel),
                                'selected': base_sel}

        def run_family(label, gen_scores, n_runs, track_core=True):
            ov = {10: [], 20: [], 30: []}
            rhos, bsh = [], []
            cnt = dict((n, 0) for n in names)
            for i in range(n_runs):
                s = gen_scores(i)
                o = ranking(s)
                for k in ov:
                    ov[k].append(overlap(order0, o, k))
                rhos.append(spearman(base, s, names)[0])
                sel = budget_select(o, cost)
                bsh.append(len(set(sel) & set(base_sel)) / float(len(base_sel)))
                for n in o[:20]:
                    cnt[n] += 1
            out = {'top10_overlap': dist_summary(ov[10]), 'top20_overlap': dist_summary(ov[20]),
                   'top30_overlap': dist_summary(ov[30]), 'spearman': dist_summary(rhos),
                   'budget_share_of_baseline_selection_kept': dist_summary(bsh)}
            out['share_runs_in_top20'] = dict((n, cnt[n] / float(n_runs)) for n in names)
            core = [n for n in order0 if cnt[n] / float(n_runs) >= 0.9]
            out['robust_core_ge90pct'] = core
            out['robust_core_size'] = len(core)
            out['baseline_top20_in_top20_ge50pct_of_runs'] = sum(1 for n in order0[:20] if cnt[n] / float(n_runs) >= 0.5)
            if not track_core:
                out.pop('share_runs_in_top20')
            sens_rows.append([I, label, n_runs] + [out['top%d_overlap' % k][q] for k in (10, 20, 30) for q in ('mean', 'p5', 'p95')]
                             + [out['spearman'][q] for q in ('mean', 'p5', 'p95')]
                             + [out['budget_share_of_baseline_selection_kept'][q] for q in ('mean', 'p5', 'p95')]
                             + [out['robust_core_size']])
            return out

        def single(label, s):
            o = ranking(s)
            d = {'top10_overlap': overlap(order0, o, 10), 'top20_overlap': overlap(order0, o, 20),
                 'top30_overlap': overlap(order0, o, 30), 'spearman': spearman(base, s)[0],
                 'budget_share_kept': len(set(budget_select(o, cost)) & set(base_sel)) / float(len(base_sel))}
            sens_rows.append([I, label, 1, d['top10_overlap'], None, None, d['top20_overlap'], None, None,
                              d['top30_overlap'], None, None, d['spearman'], None, None, d['budget_share_kept'],
                              None, None, None])
            return d

        # (a) random weights
        has_people = PEOPLE[I] is not None
        rngw = random.Random(SEED_WEIGHTS)
        draws = []
        for _ in range(N_RUNS):
            wi = dirichlet(rngw, len(ind0))
            wn = dirichlet(rngw, 2)
            draws.append((dict(zip(ind0, wi)), wn[0], wn[1]))
        S['a_weights_need_and_people'] = run_family(
            'a_random_weights_need_indicators_and_need_vs_people' if has_people else 'a_random_weights_need_indicators',
            lambda i: combine(comp0, draws[i][0], draws[i][1], draws[i][2]), N_RUNS)
        if has_people:
            S['a1_weights_need_indicators_only'] = run_family(
                'a1_random_need_indicator_weights_only', lambda i: combine(comp0, draws[i][0], w_need0, w_people0), N_RUNS, False)
            S['a2_need_vs_people_only'] = run_family(
                'a2_random_w_need_vs_w_people_only', lambda i: combine(comp0, w_ind0, draws[i][1], draws[i][2]), N_RUNS, False)
        rngm = random.Random(SEED_MODERATE)
        mdraws = [(dict((k, 2.0 ** rngm.uniform(-1, 1)) for k in ind0), 2.0 ** rngm.uniform(-1, 1)) for _ in range(N_RUNS)]
        S['a3_moderate_weights'] = run_family('a3_moderate_weights_loguniform_half_to_double',
                                              lambda i: combine(comp0, mdraws[i][0], mdraws[i][1], 1.0), N_RUNS, False)

        # (b) leave one indicator out (+ drop the people part)
        S['b_leave_one_out'] = {}
        for k in ind0:
            rest = [x for x in ind0 if x != k]
            S['b_leave_one_out'][k] = single('b_drop_' + k, combine(components(recs, I, rest),
                                                                     dict((x, w_ind0[x]) for x in rest), w_need0, w_people0))
        if has_people:
            S['b_leave_one_out']['people_part'] = single('b_drop_people_part',
                                                         combine(components(recs, I, ind0, people=False), w_ind0))

        # (c) normalisation
        S['c_normalisation'] = {}
        for m in ('minmax', 'z'):
            S['c_normalisation'][m] = single('c_' + m + '_instead_of_percentile',
                                             combine(components(recs, I, ind0, method=m), w_ind0, w_need0, w_people0))

        # (d) population +-30%
        rngp = random.Random(SEED_POP)
        S['d_population_pm30'] = run_family(
            'd_population_uniform_pm30pct',
            lambda i: combine(components(perturb_population(recs, rngp), I, ind0), w_ind0, w_need0, w_people0), N_RUNS)
        S['d_note'] = ('roofs: no population figure enters the roof score, so (d) cannot move it' if I == ROOFS else
                       'population enters through the people percentile, density and new trees per 1000')

        # robust core table
        sa_ = S['a_weights_need_and_people']['share_runs_in_top20']
        sd_ = S['d_population_pm30']['share_runs_in_top20']
        rows = []
        for n in order0:
            if sa_[n] > 0 or sd_[n] > 0 or rank0[n] <= 30:
                rows.append([n, byname[n]['community'], rank0[n], base[n], sa_[n], sd_[n],
                             'yes' if sa_[n] >= 0.9 else 'no', 'yes' if (sa_[n] >= 0.9 and sd_[n] >= 0.9) else 'no'])
        write_csv('robust_core_%s.csv' % ('trees' if I == TREES else 'roofs'),
                  ['neighbourhood', 'community', 'baseline_rank', 'baseline_priority_score', 'share_runs_top20_random_weights',
                   'share_runs_top20_population_pm30', 'robust_core_weights_ge90pct',
                   'robust_core_weights_and_population_ge90pct'], rows)
        S['robust_core_weights_and_population'] = [n for n in order0 if sa_[n] >= 0.9 and sd_[n] >= 0.9]

        # ---------------------------------------------- 3/4. external validation and alternatives
        rngx = random.Random(SEED_PERM + (0 if I == TREES else 1))
        samples = [rngx.sample(names, 40) for _ in range(N_PERM)]
        sens_pool = [n for n in names if byname[n]['has_sensor']]
        sens_samples = [rngx.sample(sens_pool, 20) for _ in range(N_PERM)]

        def var(key):
            return dict((n, byname[n][key]) for n in names)

        def mean_test(order, key, k, higher):
            v = var(key)
            obs = mean([v[n] for n in order[:k]])
            d = [mean([v[n] for n in s[:k]]) for s in samples]
            ext = sum(1 for x in d if (x >= obs - 1e-12 if higher else x <= obs + 1e-12))
            return {'top': obs, 'all_packages': mean([v[n] for n in names]), 'bottom': mean([v[n] for n in order[-k:]]),
                    'random_mean': mean(d), 'random_p5': quantile(d, 0.05), 'random_p95': quantile(d, 0.95),
                    'random_sd': sd(d), 'p_one_sided': (ext + 1) / (N_PERM + 1.0)}

        def diff_test(order, key, k):
            v = var(key)
            obs = mean([v[n] for n in order[:k]]) - mean([v[n] for n in order[-k:]])
            d = [mean([v[n] for n in s[:k]]) - mean([v[n] for n in s[k:2 * k]]) for s in samples]
            return {'top_minus_bottom': obs, 'p_one_sided': (sum(1 for x in d if x >= obs - 1e-12) + 1) / (N_PERM + 1.0)}

        def share_test(order, key, k, total):
            v = var(key)
            obs = sum(v[n] or 0 for n in order[:k]) / total
            d = [sum(v[n] or 0 for n in s[:k]) / total for s in samples]
            return {'top': obs, 'random_mean': mean(d), 'random_p5': quantile(d, 0.05), 'random_p95': quantile(d, 0.95),
                    'p_one_sided': (sum(1 for x in d if x >= obs - 1e-12) + 1) / (N_PERM + 1.0)}

        def night_oos(order, k=20):
            so = [n for n in order if byname[n]['has_sensor']]
            v = dict((n, byname[n]['heat_night']) for n in sens_pool)
            obs = mean([v[n] for n in so[:k]])
            d = [mean([v[n] for n in s]) for s in sens_samples]
            pos = dict((n, -i) for i, n in enumerate(so))
            return {'top20_sensor_mean_night_c': obs, 'all_sensor_packages_mean_night_c': mean(list(v.values())),
                    'bottom20_sensor_mean_night_c': mean([v[n] for n in so[-k:]]),
                    'random_mean': mean(d), 'p_one_sided': (sum(1 for x in d if x >= obs - 1e-12) + 1) / (N_PERM + 1.0),
                    'spearman_rankposition_vs_night': spearman(pos, v)[0], 'n_sensor_packages': len(sens_pool)}

        def evaluate(label, order, scores=None, uses_night=False, uses_lst=False, kind='current'):
            sc = scores if scores is not None else dict((n, -i) for i, n in enumerate(order))
            e = {'uses_night_temp': uses_night, 'uses_lst': uses_lst}
            e['lst_spearman'] = spearman(sc, var('lst'))[0]
            e['lst_top20'] = mean_test(order, 'lst', 20, True)
            e['lst_top30'] = mean_test(order, 'lst', 30, True)
            e['lst_top20_minus_bottom20'] = diff_test(order, 'lst', 20)
            e['wc2021_top20'] = mean_test(order, 'wc2021', 20, False)
            e['metachm_top20'] = mean_test(order, 'chm3', 20, False)
            e['stl_top20'] = mean_test(order, 'stl_pct', 20, False)
            e['night_out_of_sample'] = night_oos(order) if not uses_night else 'circular: ranking uses night_temp_c'
            if I == TREES:
                for k in (20, 30):
                    e['residents_share_top%d' % k] = share_test(order, 'pop_total', k, muni_pop)
                    e['residents65_share_top%d' % k] = share_test(order, 'pop_65plus', k, muni_65)
                    e['low_canopy_schools_share_top%d' % k] = share_test(order, 'low_canopy_schools_n', k, muni_lcs)
            else:
                e['buildings_top20'] = mean_test(order, 'buildings_n', 20, True)
                e['roof_m2_top20'] = mean_test(order, 'roof_municipal_m2', 20, True)
                e['user_sites_top20'] = mean_test(order, 'user_sites_n', 20, True)
                e['low_canopy_schools_top20'] = mean_test(order, 'low_canopy_schools_n', 20, True)
                e['spearman_with_buildings_n'] = spearman(sc, var('buildings_n'))[0]
                e['spearman_with_roof_m2'] = spearman(sc, var('roof_municipal_m2'))[0]
                e['top20_buildings_sum'] = sum(byname[n]['buildings_n'] for n in order[:20])
                e['top20_roof_m2_sum'] = sum(byname[n]['roof_municipal_m2'] for n in order[:20])
                e['all_buildings_sum'] = sum(byname[n]['buildings_n'] for n in names)
                e['all_roof_m2_sum'] = sum(byname[n]['roof_municipal_m2'] for n in names)
            sel = budget_select(order, cost)
            e['budget_1m'] = {'n_selected': len(sel), 'overlap_with_current_selection': len(set(sel) & set(base_sel)),
                              'mean_lst_selected': mean([byname[n]['lst'] for n in sel])}
            if I == ROOFS:
                e['budget_1m']['buildings_selected'] = sum(byname[n]['buildings_n'] for n in sel)
                e['budget_1m']['roof_m2_selected'] = sum(byname[n]['roof_municipal_m2'] for n in sel)
            else:
                e['budget_1m']['residents_selected'] = sum(byname[n]['pop_total'] for n in sel)
            e['top20_overlap_with_current'] = overlap(order0, order, 20)
            e['top10_overlap_with_current'] = overlap(order0, order, 10)
            e['spearman_with_current'] = spearman(base, sc)[0]
            ext_metrics = [('lst_top20', 'city_lst_summer_day_2016_2020_c (mean, top 20)'),
                           ('wc2021_top20', 'wc2021_tree_pct (mean, top 20; independent canopy product)'),
                           ('metachm_top20', 'metachm_ge3m_pct (mean, top 20; NOT independent for trees: canopy deficit is built from it)'),
                           ('stl_top20', 'ua_stl2018_pct (mean, top 20; IN the score where tree cover is used)')]
            if I == ROOFS:
                ext_metrics += [('buildings_top20', 'matched municipal buildings (mean, top 20)'),
                                ('roof_m2_top20', 'matched municipal roof m2 (mean, top 20)'),
                                ('user_sites_top20', 'schools+nurseries+elderly clubs (mean, top 20)'),
                                ('low_canopy_schools_top20', 'schools with canopy<5% within 150 m (mean, top 20)')]
            for key, lab in ext_metrics:
                m = e[key]
                ext_rows.append([I, label, kind, lab, m['top'], m['bottom'], m['all_packages'], m['random_mean'],
                                 m['random_p5'], m['random_p95'], m['p_one_sided']])
            if I == TREES:
                for k in (20, 30):
                    for key, lab in (('residents_share_top%d' % k, 'share of municipal residents, top %d' % k),
                                     ('residents65_share_top%d' % k, 'share of municipal residents 65+, top %d' % k),
                                     ('low_canopy_schools_share_top%d' % k, 'share of the municipality low-canopy schools, top %d' % k)):
                        m = e[key]
                        ext_rows.append([I, label, kind, lab, m['top'], None, None, m['random_mean'], m['random_p5'],
                                         m['random_p95'], m['p_one_sided']])
            nos_ = e['night_out_of_sample']
            if isinstance(nos_, dict):
                ext_rows.append([I, label, kind, 'heat_night, top 20 sensor neighbourhoods (out of sample)',
                                 nos_['top20_sensor_mean_night_c'], nos_['bottom20_sensor_mean_night_c'],
                                 nos_['all_sensor_packages_mean_night_c'], nos_['random_mean'], None, None, nos_['p_one_sided']])
            alt_rows.append([I, label, kind, e['top10_overlap_with_current'], e['top20_overlap_with_current'],
                             e['spearman_with_current'], e['lst_spearman'], e['lst_top20']['top'], e['lst_top20']['p_one_sided'],
                             e['wc2021_top20']['top'], e['wc2021_top20']['p_one_sided'],
                             nos_['top20_sensor_mean_night_c'] if isinstance(nos_, dict) else 'circular',
                             nos_['p_one_sided'] if isinstance(nos_, dict) else '',
                             nos_['spearman_rankposition_vs_night'] if isinstance(nos_, dict) else '',
                             e['residents_share_top20']['top'] if I == TREES else '',
                             e['residents65_share_top20']['top'] if I == TREES else '',
                             e['low_canopy_schools_share_top20']['top'] if I == TREES else '',
                             e['buildings_top20']['top'] if I == ROOFS else '',
                             e['roof_m2_top20']['top'] if I == ROOFS else '',
                             e['budget_1m']['n_selected'], e['budget_1m']['overlap_with_current_selection']])
            return e

        E = RI['external'] = {}
        E['current'] = evaluate('current_composite', order0, base, uses_night=True)
        E['current_without_night_temp'] = evaluate('current_composite_without_night_temp', o_nn, s_nn,
                                                   kind='out_of_sample_variant')
        if I == TREES:
            # the task asks n=144: same formula for all 144, people percentile among all 144
            comp_all = components(recs, I, ind0)
            pp144 = pct_ranks(dict((r['name'], r['pop_total']) for r in recs), True)
            v144 = {}
            for r in recs:
                n = r['name']
                ps = [comp_all['ind'][k][n] for k in ind0 if comp_all['ind'][k][n] is not None]
                v144[n] = (mean(ps) + pp144[n]) / 2.0
            E['lst_spearman_n144_extended_score'] = spearman(v144, dict((r['name'], r['lst']) for r in recs))
        E['lst_spearman_packages'] = spearman(base, dict((n, byname[n]['lst']) for n in names))
        Nv = RI['alternatives'] = {}
        Nv['tree_cover_alone'] = evaluate('naive_tree_cover_alone', rank_by_value(names, var('stl_pct'), False), kind='naive')
        Nv['density_alone'] = evaluate('naive_density_alone', rank_by_value(names, var('pop_density_per_km2'), True), kind='naive')
        Nv['low_canopy_sites_count_alone'] = evaluate('naive_low_canopy_sites_count_alone',
                                                      rank_by_value(names, var('low_canopy_sites_n'), True), kind='naive')
        Nv['lst_alone'] = evaluate('naive_lst_alone', rank_by_value(names, var('lst'), True), uses_lst=True, kind='naive_heat')
        if I == TREES:
            Nv['residents_alone'] = evaluate('naive_residents_alone', rank_by_value(names, var('pop_total'), True), kind='naive')
        else:
            Nv['buildings_alone'] = evaluate('naive_buildings_alone', rank_by_value(names, var('buildings_n'), True), kind='naive')
        Nv['ties'] = {'tree_cover_zero_among_packages': sum(1 for n in names if byname[n]['stl_pct'] == 0.0),
                      'low_canopy_sites_n_value_at_rank20_shared_by': None}
        lv = var('low_canopy_sites_n')
        o_l = rank_by_value(names, lv, True)
        Nv['ties']['low_canopy_sites_n_value_at_rank20_shared_by'] = sum(1 for n in names if lv[n] == lv[o_l[19]])

        # proposed minimal changes (computed here; the engine is NOT changed)
        if I == TREES:
            B, C = combine_balanced, None
            variants = {
                'T1_drop_night_temp': (ind_nn, C),
                'T2_drop_canopy_deficit_m2': ([k for k in ind0 if k != 'canopy_deficit_m2'], C),
                'T2b_deficit_per_area_instead_of_m2': ([('canopy_deficit_pp' if k == 'canopy_deficit_m2' else k) for k in ind0], C),
                'T3_drop_density': ([k for k in ind0 if k != 'pop_density_per_km2'], C),
                'T3b_new_trees_per_km2_instead_of_per_1000': ([('new_trees_per_km2' if k == 'new_trees_per_1000_residents' else k) for k in ind0], C),
                'T4_lst_instead_of_night': ([('lst_summer_day_c' if k == 'night_temp_c' else k) for k in ind0], C),
                'T6_balanced_need_vs_people': (ind0, B),
                'T12_drop_night_and_deficit': ([k for k in ind0 if k not in ('night_temp_c', 'canopy_deficit_m2')], C),
                'T123_drop_night_deficit_density': (['tree_cover_stl2018_pct', 'new_trees_per_1000_residents'], C),
                'T7_balanced_cover_newtrees_km2_night': (['tree_cover_stl2018_pct', 'new_trees_per_km2', 'night_temp_c'], B),
                'T8_balanced_cover_newtrees_km2': (['tree_cover_stl2018_pct', 'new_trees_per_km2'], B),
                'T9_balanced_cover_only': (['tree_cover_stl2018_pct'], B),
                'T10_balanced_cover_night': (['tree_cover_stl2018_pct', 'night_temp_c'], B),
                'TA_drop_density_and_deficit': ([k for k in ind0 if k not in ('pop_density_per_km2', 'canopy_deficit_m2')], C),
                'TC_balanced_cover_newtrees_1000': (['tree_cover_stl2018_pct', 'new_trees_per_1000_residents'], B),
            }
        else:
            C = None
            variants = {
                'R1_buildings_instead_of_low_canopy_share': ([('buildings_n' if k == 'low_canopy_sites_share' else k) for k in ind0], C),
                'R2_lst_instead_of_night': ([('lst_summer_day_c' if k == 'night_temp_c' else k) for k in ind0], C),
                'R3_drop_tree_cover': ([k for k in ind0 if k != 'tree_cover_stl2018_pct'], C),
                'R5_drop_night_temp': (ind_nn, C),
                'R12_buildings_tree_cover_lst': (['buildings_n', 'tree_cover_stl2018_pct', 'lst_summer_day_c'], C),
                'R123_lst_plus_buildings': (['lst_summer_day_c', 'buildings_n'], C),
                'R4_lst_plus_user_sites': (['lst_summer_day_c', 'user_sites_n'], C),
                'R6_tree_cover_plus_lst': (['tree_cover_stl2018_pct', 'lst_summer_day_c'], C),
            }
        RI['proposed_variants'] = {}
        for vn, (inds, comb) in variants.items():
            fcomb = comb or combine
            cv = components(recs, I, inds)
            sv = fcomb(cv, None, w_need0, w_people0)
            ov_ = ranking(sv)
            ev = evaluate(vn, ov_, sv, uses_night=('night_temp_c' in inds), uses_lst=('lst_summer_day_c' in inds),
                          kind='proposed')
            rngv = random.Random(SEED_WEIGHTS)
            cnt = dict((n, 0) for n in names)
            ovs, rh = [], []
            for _ in range(N_RUNS):
                wi = dict(zip(inds, dirichlet(rngv, len(inds))))
                wn = dirichlet(rngv, 2)
                s = fcomb(cv, wi, wn[0], wn[1])
                o = ranking(s)
                ovs.append(overlap(ov_, o, 20))
                rh.append(spearman(sv, s, names)[0])
                for n in o[:20]:
                    cnt[n] += 1
            ev['indicators'] = inds
            ev['combiner'] = 'balanced (need re-ranked to a percentile before combining)' if comb else 'engine formula'
            ev['weights_robustness'] = {'top20_overlap_with_own_baseline': dist_summary(ovs), 'spearman': dist_summary(rh),
                                        'robust_core_size_ge90pct': sum(1 for n in names if cnt[n] >= 0.9 * N_RUNS)}
            if PEOPLE[I]:
                rngq = random.Random(SEED_POP)
                ovp, cntp = [], dict((n, 0) for n in names)
                for _ in range(N_RUNS):
                    o = ranking(fcomb(components(perturb_population(recs, rngq), I, inds), None, w_need0, w_people0))
                    ovp.append(overlap(ov_, o, 20))
                    for n in o[:20]:
                        cntp[n] += 1
                ev['population_robustness'] = {'top20_overlap_with_own_baseline': dist_summary(ovp),
                                               'robust_core_size_ge90pct': sum(1 for n in names if cntp[n] >= 0.9 * N_RUNS)}
                ev['spearman_score_vs_people_pct'] = spearman(sv, comp0['pp'])[0]
            ev['no_sensor_in_top20'] = sum(1 for n in ov_[:20] if not byname[n]['has_sensor'])
            ev['new_in_top20'] = [n for n in ov_[:20] if n not in order0[:20]]
            ev['dropped_from_top20'] = [n for n in order0[:20] if n not in ov_[:20]]
            ev['top20'] = ov_[:20]
            RI['proposed_variants'][vn] = ev
        RI['baseline_top30'] = [{'rank': rank0[n], 'neighbourhood': n, 'score': base[n], 'need': det0[n]['need'],
                                 'people_pct': det0[n]['pp'], 'n_indicators': det0[n]['n_ind'],
                                 'area_km2': byname[n]['area_km2'], 'lst': byname[n]['lst'],
                                 'buildings_n': byname[n]['buildings_n'], 'sites_all4_n': byname[n]['sites_all4_n'],
                                 'pop_total': byname[n]['pop_total']}
                                for n in order0[:30]]

    # ------------------------------------------------------------ write
    write_csv('sensitivity_summary.csv',
              ['intervention', 'analysis', 'n_runs', 'top10_overlap_mean', 'top10_p5', 'top10_p95', 'top20_overlap_mean',
               'top20_p5', 'top20_p95', 'top30_overlap_mean', 'top30_p5', 'top30_p95', 'spearman_mean', 'spearman_p5',
               'spearman_p95', 'budget1m_share_of_baseline_selection_kept_mean', 'budget_p5', 'budget_p95',
               'robust_core_size_top20_ge90pct'], sens_rows)
    write_csv('external_validation.csv',
              ['intervention', 'ranking', 'kind', 'metric', 'top_value', 'bottom_value', 'all_packages_value',
               'random_pick_mean', 'random_p5', 'random_p95', 'p_one_sided'], ext_rows)
    write_csv('alternatives.csv',
              ['intervention', 'ranking', 'kind', 'top10_overlap_with_current', 'top20_overlap_with_current',
               'spearman_with_current', 'spearman_with_lst', 'lst_top20_mean_c', 'lst_top20_p', 'wc2021_top20_mean_pct',
               'wc2021_top20_p', 'night_top20_sensor_mean_c_out_of_sample', 'night_p', 'night_spearman_out_of_sample',
               'residents_share_top20', 'residents65_share_top20', 'low_canopy_schools_share_top20',
               'buildings_top20_mean', 'roof_m2_top20_mean', 'budget1m_n_selected',
               'budget1m_overlap_with_current_selection'], alt_rows)
    for I in INTERVENTIONS:   # the per-neighbourhood shares are in robust_core_*.csv; keep the json readable
        for k in ('a_weights_need_and_people', 'd_population_pm30'):
            R[I]['sensitivity'][k].pop('share_runs_in_top20', None)
    with open(os.path.join(HERE, 'results.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print('ok')


if __name__ == '__main__':
    main()
