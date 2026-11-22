/* Data-visualisation components. CONTRACT (props) is fixed; implementations are owned by the viz team.
   Rules: tokens from src/tokens.css only; at most the four font sizes; no badges, no small-caps labels;
   recorded/calculated values use solid fills, projected values use the --cool colour with a dashed or hatched edge. */
import type { ReactNode } from 'react'
import { area, clamp, euro, num, pos, roundPeople } from './format'
import './viz.css'

/* ------------------------------------------------------------------ PeopleViz */

/** One dot = N people, N chosen so the grid stays between ~20 and ~120 dots. */
const PEOPLE_STEPS = [10, 50, 100, 200, 250, 500, 1000, 2000]
const perDot = (total: number) => PEOPLE_STEPS.find(s => total / s <= 120) ?? 5000

/** Residents of an area, shown as people, with the share of 65+ and 0-14. Values are recorded estimates. */
export function PeopleViz({ total, over65, under15 }: { total: number; over65: number | null; under15: number | null }): ReactNode {
  const t = Math.max(0, total)
  const step = perDot(t)
  const dots = Math.max(1, Math.round(t / step))
  const old = over65 && t ? Math.round((over65 / t) * dots) : 0
  const kids = under15 && t ? Math.min(dots - old, Math.round((under15 / t) * dots)) : 0
  const cls = (i: number) => (i < old ? 'viz-dot viz-dot-old' : i < old + kids ? 'viz-dot viz-dot-kid' : 'viz-dot')
  return (
    <figure className="viz viz-people" aria-label={`Περίπου ${num(roundPeople(t))} κάτοικοι`}>
      <p className="viz-people-total">
        <span className="viz-2">περίπου </span>
        <span className="viz-title viz-num">{num(roundPeople(t))}</span>
        <span> κάτοικοι</span>
      </p>
      <div className="viz-dots" aria-hidden="true">
        {Array.from({ length: dots }, (_, i) => <span key={i} className={cls(i)} />)}
      </div>
      <figcaption className="viz-people-key">
        {over65 != null && over65 > 0 && (
          <span><i className="viz-dot viz-dot-old" /><span className="viz-num">{num(roundPeople(over65))}</span> άνω των 65</span>
        )}
        {under15 != null && under15 > 0 && (
          <span><i className="viz-dot viz-dot-kid" /><span className="viz-num">{num(roundPeople(under15))}</span> παιδιά έως 14 ετών</span>
        )}
        <span className="viz-3">κάθε κουκκίδα, {num(step)} κάτοικοι</span>
      </figcaption>
    </figure>
  )
}

/* ------------------------------------------------------------------ AreaViz */

/* Reference: a basketball court is 28 m x 15 m = 420 m².
   Source: FIBA Official Basketball Rules, Rule 2 (Court), "the playing court shall have ... dimensions of 28 m in length by 15 m in width". */
const COURT_L = 28
const COURT_W = 15
const COURT_M2 = COURT_L * COURT_W

const courtPhrase = (m2: number) => {
  const r = m2 / COURT_M2
  if (r < 0.75) return 'μικρότερο από ένα γήπεδο μπάσκετ'
  if (r < 1.5) return 'περίπου όσο ένα γήπεδο μπάσκετ'
  return `περίπου όσο ${num(r < 10 ? Math.round(r) : Math.round(r / 5) * 5)} γήπεδα μπάσκετ`
}

/** An area in m² made tangible (e.g. compared with a familiar size). kind: 'recorded' (exists today) or 'projected' (planned). */
export function AreaViz({ m2, kind, caption }: { m2: number; kind: 'recorded' | 'projected'; caption: string }): ReactNode {
  const a = Math.max(0, m2)
  const side = Math.sqrt(a)
  const extent = Math.max(side, COURT_L) // metres that fit the box width
  const sq = (side / extent) * 100
  return (
    <figure className="viz viz-area">
      <div className="viz-area-box" aria-hidden="true">
        <div className={`viz-area-sq viz-${kind}`} style={{ width: `${sq}%`, height: `${sq}%` }} />
        <svg className="viz-court" viewBox={`0 0 ${COURT_L} ${COURT_W}`}
          style={{ width: `${(COURT_L / extent) * 100}%`, height: `${(COURT_W / extent) * 100}%` }}>
          <rect x="0" y="0" width={COURT_L} height={COURT_W} />
          <line x1={COURT_L / 2} y1="0" x2={COURT_L / 2} y2={COURT_W} />
          <circle cx={COURT_L / 2} cy={COURT_W / 2} r="1.8" />
          <rect x="0" y={(COURT_W - 4.9) / 2} width="5.8" height="4.9" />
          <rect x={COURT_L - 5.8} y={(COURT_W - 4.9) / 2} width="5.8" height="4.9" />
        </svg>
      </div>
      <figcaption className="viz-area-text">
        <span className="viz-title viz-num">{area(a)} m²</span>
        <span>{caption}</span>
        <span className="viz-3 viz-meta">{courtPhrase(a)}</span>
      </figcaption>
    </figure>
  )
}

/* ------------------------------------------------------------------ CoverViz */

/** Tree cover of the area today versus a target, as one bar. Values in % of area. */
export function CoverViz({ today, target, city }: { today: number; target: number; city: number }): ReactNode {
  const max = Math.max(target, city, today) * 1.2 || 1
  const t = pos(today, max), g = pos(target, max), c = pos(city, max)
  const pct = (v: number) => `${num(v, 1)}%`
  return (
    <figure className="viz viz-cover" aria-label={`Δενδροκάλυψη σήμερα ${pct(today)}, στόχος ${pct(target)}, μέσος όρος Δήμου ${pct(city)}`}>
      <div className="viz-cover-bar" aria-hidden="true">
        <div className="viz-cover-track" />
        {target > today && <div className="viz-cover-gap" style={{ left: `${t}%`, width: `${g - t}%` }} />}
        <div className="viz-cover-today" style={{ width: `${t}%` }} />
        <div className="viz-cover-city" style={{ left: `${c}%` }} />
        <div className="viz-cover-target" style={{ left: `${g}%` }} />
      </div>
      <figcaption className="viz-cover-key">
        <span><i className="viz-key viz-key-today" /><b className="viz-num">{pct(today)}</b><span className="viz-2">σήμερα</span></span>
        <span><i className="viz-key viz-key-target" /><b className="viz-num">{pct(target)}</b><span className="viz-2">στόχος</span></span>
        <span><i className="viz-key viz-key-city" /><b className="viz-num">{pct(city)}</b><span className="viz-2">μέσος όρος Δήμου</span></span>
      </figcaption>
    </figure>
  )
}

/* ------------------------------------------------------------------ NeedRows */

/** Why here: one row per indicator, label + value + how this area ranks among all (percentile 0-100, 100 = most need). */
export function NeedRows({ rows }: { rows: { label: string; value: string; percentile: number | null }[] }): ReactNode {
  return (
    <ul className="viz viz-rows">
      {rows.map(r => {
        const p = r.percentile == null ? null : clamp(r.percentile)
        const hint = p == null ? undefined : `Μεγαλύτερη ανάγκη από το ${num(Math.round(p))}% των γειτονιών`
        return (
          <li key={r.label} className="viz-row" title={hint}>
            <span className="viz-row-label">{r.label}</span>
            <span className="viz-row-value viz-num">{r.value}</span>
            <span className="viz-row-bar" aria-label={hint}>
              {p != null && <span className="viz-row-fill" style={{ width: `${Math.max(p, 3)}%` }} />}
            </span>
          </li>
        )
      })}
    </ul>
  )
}

/* ------------------------------------------------------------------ CostRange */

/** A projected cost: central value with a low-high range. */
export function CostRange({ central, low, high }: { central: number; low: number; high: number }): ReactNode {
  const max = Math.max(high, central) * 1.04 || 1
  const l = pos(low, max), h = pos(high, max), c = pos(central, max)
  return (
    <figure className="viz viz-cost" aria-label={`Περίπου ${euro(central)}, από ${euro(low, 1)} έως ${euro(high, 1)}`}>
      <p className="viz-title viz-num viz-cost-central">{euro(central)}</p>
      <div className="viz-cost-line" aria-hidden="true">
        <div className="viz-cost-base" />
        <div className="viz-cost-range" style={{ left: `${l}%`, width: `${Math.max(h - l, 0.5)}%` }} />
        <div className="viz-cost-mark" style={{ left: `${c}%` }} />
      </div>
      <figcaption className="viz-cost-ends viz-meta viz-2">
        <span>από <span className="viz-num">{euro(low, 1)}</span></span>
        <span>έως <span className="viz-num">{euro(high, 1)}</span></span>
      </figcaption>
    </figure>
  )
}

/* ------------------------------------------------------------------ TempDrop */

/** Before / after of a measured temperature effect, e.g. pavement 60° in sun vs 30° in shade. */
export function TempDrop({ before, after, beforeLabel, afterLabel, source }: { before: number; after: number; beforeLabel: string; afterLabel: string; source: string }): ReactNode {
  // Shared scale from 0 °C, so a small difference looks small.
  const top = Math.max(10, Math.ceil(Math.max(before, after) / 10) * 10)
  const diff = before - after
  const tube = (v: number, cls: string) => (
    <div className="viz-temp-tube" aria-hidden="true">
      <div className={`viz-temp-fill ${cls}`} style={{ height: `${pos(v, top)}%` }} />
    </div>
  )
  return (
    <figure className="viz viz-temp" aria-label={`${beforeLabel} ${num(before, 1)}°, ${afterLabel} ${num(after, 1)}°`}>
      {/* 3 x 3 grid: degrees, tubes, labels; so the tubes line up whatever the label length. */}
      <div className="viz-temp-pair">
        <span className="viz-title viz-num">{num(before, 1)}°</span>
        <span />
        <span className="viz-title viz-num">{num(after, 1)}°</span>
        {tube(before, 'viz-temp-hot')}
        <span className="viz-temp-diff viz-2 viz-num">{diff >= 0 ? `${num(diff, 1)}° λιγότερο` : `${num(-diff, 1)}° περισσότερο`}</span>
        {tube(after, 'viz-temp-cool')}
        <span className="viz-temp-label">{beforeLabel}</span>
        <span />
        <span className="viz-temp-label">{afterLabel}</span>
      </div>
      <figcaption className="viz-meta viz-3">{source}</figcaption>
    </figure>
  )
}

/* ------------------------------------------------------------------ CompareBar */

/** Two values side by side: recorded (as planted) vs projected (by need). */
export function CompareBar({ label, recorded, projected, unit, max, active }: { label: string; recorded: number; projected: number; unit: string; max: number; active: 'recorded' | 'projected' }): ReactNode {
  const m = Math.max(max, recorded, projected) || 1
  const digits = Math.max(recorded, projected) < 100 ? 1 : 0
  const bar = (kind: 'recorded' | 'projected', v: number, name: string) => (
    <div className={`viz-cmp-row${active === kind ? ' viz-on' : ''}`}>
      <div className="viz-cmp-line">
        <span className="viz-cmp-name">{name}</span>
        <span className="viz-num viz-cmp-value">{num(v, digits)}{unit}</span>
      </div>
      <div className="viz-cmp-track">
        <div className={`viz-cmp-bar viz-${kind}`} style={{ width: v > 0 ? `max(4px, ${pos(v, m)}%)` : '0' }} />
      </div>
    </div>
  )
  return (
    <figure className="viz viz-cmp">
      <figcaption className="viz-cmp-label">{label}</figcaption>
      {bar('recorded', recorded, 'όπως φυτεύτηκαν')}
      {bar('projected', projected, 'με βάση την ανάγκη')}
    </figure>
  )
}
