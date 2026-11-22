import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowUpLeft, TriangleAlert, TreeDeciduous, Columns3, TreePine, School, ChevronLeft, ChevronRight, Thermometer, Sun, Wind, Factory, Users, RadioTower, Leaf, Trees, Mountain, Building2, Palette, Sprout, MapPin as Pin, Bus, Bike, Footprints, ShoppingBasket, Coffee, Pill, Droplets, Armchair, ParkingSquare, Home, Landmark, Dumbbell, Wifi, Recycle, PlugZap, HeartHandshake, TrainFront, FileText, Shovel, Satellite, RotateCcw } from 'lucide-react'
import MapView from './MapView'
import { type AppData, type Layer, type Mode, type Pkg, type Side, type Tab, UNIT, SHORT, eur, fmt, label, DATA, roofEnergy, capitalRank } from './data'
import { INSIGHTS, GENERIC, type Tool } from './insights'
import { PeopleViz, CompareBar } from './components/viz'
import { Slider, Segmented, Disclosure, StageSlider, ShadeDonut } from './components/ui'

const reduced = () => typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function useCountUp(target: number, ms = 600) {
  const [v, setV] = useState(target)
  const from = useRef(target)
  useEffect(() => {
    if (reduced()) { setV(target); from.current = target; return }
    const t0 = performance.now(), a = from.current
    let raf = 0
    const tick = (t: number) => {
      const k = Math.min(1, (t - t0) / ms), e = 1 - Math.pow(1 - k, 3)
      setV(a + (target - a) * e)
      if (k < 1) raf = requestAnimationFrame(tick); else from.current = target
    }
    raf = requestAnimationFrame(tick)
    return () => { cancelAnimationFrame(raf); from.current = target }
  }, [target, ms])
  return v
}

function Num({ value, format = v => fmt(Math.round(v)) }: { value: number; format?: (v: number) => string }) {
  return <>{format(useCountUp(value))}</>
}

// Full intervention per area: capacity (trees to the 10% canopy target, or all municipal roof m²) and its central unit price.
function full(p: Pkg) {
  const unit = p.c && p.q[1] ? p.c[1] / p.q[1] : 0
  return { cap: p.cap ?? p.q[1], unit, lowF: p.c ? p.c[0] / p.c[1] : 1, highF: p.c ? p.c[2] / p.c[1] : 1 }
}
function areaPlan(p: Pkg, pct: number) {
  const f = full(p)
  const q = Math.round((f.cap * pct) / 100)
  return { q, cost: q * f.unit, low: q * f.unit * f.lowF, high: q * f.unit * f.highF, cap: f.cap, unit: f.unit }
}
const ranked = (d: AppData, tab: Tab) => Object.entries(d.packages[tab]).filter(([, p]) => p.c).sort((a, b) => a[1].rank - b[1].rank)

// Short, natural copy for the measured effects shown in the main view. Full sentences stay in Πηγές.
const EFFECT: Record<string, string> = {
  pavement_surface_temp_under_shade: 'Πεζοδρόμιο κάτω από ώριμο δέντρο',
  street_air_temp_shaded_street: 'Αέρας σε σκιερό δρόμο',
  street_air_temp_very_shaded_street: 'Αέρας σε πολύ σκιερό δρόμο',
  classroom_air_temp_summer: 'Μέσα στην τάξη, το καλοκαίρι',
  roof_surface_temp: 'Επιφάνεια της ταράτσας',
}

function HotList({ d, tab, alloc, onPick }: { d: AppData; tab: Tab; alloc: Record<string, number>; onPick: (id: string) => void }) {
  return (
    <ol className="rank">
      {ranked(d, tab).slice(0, 12).map(([id, p]) => (
        <li key={id}>
          <button className="hot-row" onClick={() => onPick(id)}>
            <span className="rk">{p.rank}</span>
            <span className="nm">{d.neighbourhoods[id].name}{d.neighbourhoods[id].pop ? <small>{fmt(Math.round((d.neighbourhoods[id].pop ?? 0) / 10) * 10)} κάτοικοι</small> : null}</span>
            {alloc[id] ? <span className="pill cool">{alloc[id]}%</span> : <ChevronRight size={18} className="chev" aria-hidden />}
          </button>
        </li>
      ))}
    </ol>
  )
}

function Overview({ d, tab, alloc, onPick }: { d: AppData; tab: Tab; alloc: Record<string, number>; onPick: (id: string) => void }) {
  const c = d.city
  const facts: [string, string][] = tab === 'streets'
    ? [[`${fmt(c.tree_cover_pct, 1)}%`, 'κάλυψη δέντρων στον Δήμο'],
       ...(c.plantings_2024_2026 ? [[fmt(c.plantings_2024_2026), 'δέντρα φυτεύτηκαν 2024-26'] as [string, string]] : []),
       [fmt(c.schools_low_canopy), `από τα ${fmt(c.schools)} σχολεία έχουν λίγη σκιά`]]
    : (() => {
        const all = roofEnergy(d, c.roof_other_m2)
        return [[`${fmt(Math.round(c.roof_other_m2 / 1000))}k m²`, 'στέγες δημοτικών κτιρίων, εκτός σχολείων'],
                [`έως ${eur(all.eur)}`, 'λιγότερα στον κλιματισμό κάθε χρόνο, αν γίνουν όλες'],
                [`~${fmt(Math.round(all.payback ?? 0))} χρόνια`, 'για να αποσβεστεί η επένδυση']] as [string, string][]
      })()
  return (
    <div className="view">
      <header className="head">
        <h1>{tab === 'streets' ? 'Πού λείπει η σκιά' : 'Ποια κτίρια ψήνονται'}</h1>
        <p className="lead">Διάλεξε γειτονιά και όρισε πόσο επεμβαίνεις.</p>
      </header>
      <div className="card">
        <p className="hero-n">{facts[0][0]}</p>
        <p className="hero-cap">{facts[0][1]}</p>
      </div>
      {tab === 'streets' && (() => { const cr = capitalRank(d, 0); return (
        <div className="card">
          <p className="hero-n">{cr.rank}η <small>από {cr.n}</small></p>
          <p className="hero-cap">ευρωπαϊκή πρωτεύουσα στα δέντρα: {fmt(cr.base)}% της πόλης, ο μέσος όρος 29%</p>
          <div className="caprow" aria-hidden>{[...d.capitals].sort((a, b) => b[1] - a[1]).map(c => <i key={c[0]} className={c[0] === 'Athens' ? 'me' : ''} style={{ height: `${Math.max(6, (c[1] / 72) * 100)}%` }} />)}</div>
        </div>) })()}
      <div className="duo">{facts.slice(1).map(([v, t]) => <div className="card" key={t}><p className="big">{v}</p><p className="cap">{t}</p></div>)}</div>
      <div className="card">
        <h2>{tab === 'streets' ? 'Πού λείπει περισσότερο' : 'Πού ψήνονται περισσότερο'}</h2>
        <HotList d={d} tab={tab} alloc={alloc} onPick={onPick} />
      </div>
    </div>
  )
}

// What changes in the area, scaled by the slider. Only numbers with a source; each says when it applies.
// The investment, read like a statement: what you buy, what it costs, what the area gets back.
function Invest({ d, g, nb, unit, air, on }: { d: AppData; g: ReturnType<typeof greenPlan>; nb: number; unit: number; air: number | null; on: boolean }) {
  const k = d.impact, e = d.energy
  const gr = d.green_roof_eur_m2[1], fa = d.facade_eur_m2[1]
  const buy: [string, string, number, string][] = []
  if (g.trees > 0 || !on) buy.push(['Δέντρα', `${fmt(g.trees)} × ${fmt(Math.round(unit))} €`, g.trees * unit, 'tree'])
  if (g.roof > 0) buy.push(['Πράσινες ταράτσες', `${fmt(g.roof)} m² × ${fmt(gr)} €`, g.roof * gr, 'roof'])
  if (g.facade > 0) buy.push(['Πράσινες προσόψεις', `${fmt(g.facade)} m² × ${fmt(fa)} €`, g.facade * fa, 'facade'])
  const power = g.roof * e.cooling_kwh_per_m2 * 0.49 * e.eur_per_kwh + g.facade * e.cooling_kwh_per_m2 * 0.27 * e.eur_per_kwh
  const gets: [string, string, string?][] = []
  if (g.canopy > 0) gets.push(['Σκιά στους δρόμους', `${fmt(Math.round(g.canopy / 10) * 10)} m²`, 'όταν μεγαλώσουν τα δέντρα, σε 10 με 20 χρόνια'])
  if (g.trees > 0 && air) gets.push(['Αέρας στους σκιερούς δρόμους', `έως ${fmt(air, 1)} °C πιο δροσερός`, 'μέτρηση στην Αθήνα, καλοκαίρι'])
  if (g.trees > 0) gets.push(['CO₂ που δεσμεύεται', `${fmt((g.trees * k.co2_kg_per_tree_yr) / 1000, 1)} t τον χρόνο`, 'μελέτη i-Tree, Βαρκελώνη'])
  if (g.trees > 0) gets.push(['Σκόνη και ρύποι', `${fmt(g.trees * k.pollutants_kg_per_tree_yr)} kg τον χρόνο`, 'μελέτη i-Tree, Βαρκελώνη'])
  if (power > 0) gets.push(['Ρεύμα κλιματισμού', `έως ${eur(power)} τον χρόνο`, 'αν τα κτίρια έχουν κλιματισμό· ταράτσα έως 49%, πρόσοψη έως 27% λιγότερη ψύξη'])
  if (g.roof > 0) gets.push(['Νερό βροχής που κρατιέται', `${fmt(Math.round(g.roof * k.roof_rain_m3_per_m2_yr))} m³ τον χρόνο`])
  return (
    <section className={`card invest ${on ? '' : 'potential'}`} aria-live="polite">
      <h2>Επένδυση</h2>
      <dl className="stmt">
        {buy.map(([l, , v, tone]) => <div key={l}><dt><i className={`dot ${tone}`} />{l}</dt><dd><b>{eur(v)}</b></dd></div>)}
        <div className="total"><dt>Σύνολο</dt><dd><b><Num value={g.cost} format={v => eur(v)} /></b></dd></div>
      </dl>
      {gets.length > 0 && <>
        <h2>Τι κερδίζει η γειτονιά</h2>
        <dl className="stmt gets">
          {gets.map(([l, v, t]) => <div key={l} title={t}><dt>{l}</dt><dd><b>{v}</b></dd></div>)}
          {nb > 0 && <div><dt>Κάτοικοι της γειτονιάς</dt><dd><b>{fmt(Math.round(nb / 100) * 100)}</b></dd></div>}
        </dl>
      </>}
    </section>
  )
}

// One icon style for the editor: a tinted tile with a thin-stroke glyph. tone: tree | roof | facade | cost | fx
const Ico = ({ i, tone = 'fx', big }: { i: React.ElementType; tone?: string; big?: boolean }) => {
  const I = i
  return <span className={`ico ${tone} ${big ? 'big' : ''}`} aria-hidden><I size={big ? 20 : 17} strokeWidth={1.6} /></span>
}

// Greening per area: the slider fills the tree spots first, then green roofs on City buildings, then City facades.
const SEG = { trees: 60, roof: 25, facade: 15 }
export type Stages = { roof: boolean; facade: boolean }
let STAGES: Stages = { roof: true, facade: true }
export function greenPlan(d: AppData, id: string, pct: number) {
  const p = d.packages.streets[id]
  const nb = d.neighbourhoods[id]
  const cover = p?.why.find(w => w[0] === 'tree_cover_stl2018_pct')?.[1] ?? nb.tree_pct ?? 0
  const def10 = p?.why.find(w => w[0] === 'canopy_deficit_m2')?.[1] ?? 0
  const area = def10 > 0 && cover < 10 ? def10 / ((10 - cover) / 100) : (nb.area_km2 ?? 0) * 1e6
  const perM2 = p && def10 > 0 ? (p.cap ?? p.q[1]) / def10 : 1 / 17.5   // trees per m2 of grown canopy (engine)
  const unit = p?.c && p.q[1] ? p.c[1] / p.q[1] : 0
  // Range of the price per tree (251 / 339 / 615 € in research/cost/scenarios.md), not of the engine totals, which also vary the number of trees.
  const lowF = p?.c && p.q[0] && unit ? p.c[0] / p.q[0] / unit : 1, highF = p?.c && p.q[2] && unit ? p.c[2] / p.q[2] / unit : 1
  const T = p?.spots ?? 0, R = p?.groof ?? 0, F = p?.facade ?? 0
  // Segments of the bar, only for what exists here, scaled to 100.
  const w = { trees: T > 0 ? SEG.trees : 0, roof: R > 0 && STAGES.roof ? SEG.roof : 0, facade: F > 0 && STAGES.facade ? SEG.facade : 0 }
  const sum = w.trees + w.roof + w.facade || 1
  const e1 = (w.trees / sum) * 100, e2 = e1 + (w.roof / sum) * 100
  const part = (x0: number, x1: number) => (x1 > x0 ? Math.max(0, Math.min(1, (pct - x0) / (x1 - x0))) : 0)
  const trees = Math.round(T * part(0, e1))
  const roof = Math.round((R * part(e1, e2)) / 10) * 10
  const facade = Math.round((F * part(e2, 100)) / 10) * 10
  const canopy = perM2 > 0 ? trees / perM2 : 0
  const g = d.green_roof_eur_m2, fc = d.facade_eur_m2
  return {
    cover, after: cover + (area ? (canopy / area) * 100 : 0), canopy, trees, T, roof, R, facade, F, e1, e2,
    cost: trees * unit + roof * g[1] + facade * fc[1],
    low: trees * unit * lowF + roof * g[0] + facade * fc[0],
    high: trees * unit * highF + roof * g[2] + facade * fc[2], src: p?.spots_src,
  }
}

function AreaView({ d, id, tab, pct, setPct, onBack, stages, onStage }: { d: AppData; id: string; tab: Tab; pct: number; setPct: (n: number) => void; onBack: () => void; stages?: Stages; onStage?: (k: keyof Stages) => void }) {
  const nb = d.neighbourhoods[id]
  const p: Pkg | undefined = d.packages[tab][id]
  const trees = tab === 'streets'
  const back = <button className="back" onClick={onBack}><ChevronLeft size={20} aria-hidden />Πίσω</button>
  if (!p || !p.c) return (
    <div className="view">
      {back}
      <header className="head"><h1>{nb.name}</h1><p className="lead">Εδώ δεν βρέθηκε χώρος για {trees ? 'νέα δέντρα' : 'δροσερές στέγες'}.</p></header>
    </div>
  )
  const measured = p.imp.filter(i => i[5] === 'measured_athens' && i[1] != null)
  const head = (
    <header className="head row">
      <h1>{nb.name}</h1>
      <span className={`prio ${p.rank <= d.counts[tab] / 4 ? 'hi' : p.rank <= d.counts[tab] / 2 ? 'mid' : 'lo'}`} title={`${p.rank}η σε ανάγκη από ${d.counts[tab]} γειτονιές`}><TriangleAlert size={14} strokeWidth={2} aria-hidden />{p.rank}</span>
    </header>
  )

  if (trees) {
    const g = greenPlan(d, id, pct)
    const on = pct > 0
    const shown = g
    const unitPrice = p?.c && p.q[1] ? p.c[1] / p.q[1] : 0
    return (
      <div className="view">
        {back}
        {head}
        <section className="card plan2">
          <h2>Πόσο πράσινο βάζεις εδώ;</h2>
          <div className="cover-jump">
            <div className={`placed ${on ? '' : 'dim'}`}>
              <span className="pl-main"><Ico i={TreeDeciduous} tone="tree" big /><b><Num value={g.trees} /></b><em>δέντρα</em></span>
            </div>
            <div className={`shade ${on ? '' : 'dim'}`} title="πόσο από τη γειτονιά σκιάζεται από δέντρα· ο κύκλος γεμίζει στο 30%, τον στόχο των πράσινων πόλεων">
              <ShadeDonut value={g.after} max={30} />
              <div><b>{fmt(g.after, 1)}%</b><span>σκιά</span></div>
            </div>
          </div>
          <StageSlider value={pct} onChange={setPct} label={`Πόσο πράσινο στη γειτονιά ${nb.name}`} stages={[
            ...(g.T > 0 ? [{ from: 0, to: g.e1, tone: 'tree', icon: <TreeDeciduous size={14} strokeWidth={1.7} />, name: 'δέντρα' }] : []),
            ...(g.R > 0 && stages?.roof !== false ? [{ from: g.e1, to: g.e2, tone: 'roof', icon: <Building2 size={14} strokeWidth={1.7} />, name: 'ταράτσες' }] : []),
            ...(g.F > 0 && stages?.facade !== false ? [{ from: g.e2, to: 100, tone: 'facade', icon: <Columns3 size={14} strokeWidth={1.7} />, name: 'προσόψεις' }] : []),
          ]} toggles={[
            ...(g.R > 0 ? [{ key: 'roof', on: stages?.roof !== false, tone: 'roof', icon: <Building2 size={14} strokeWidth={1.7} />, name: 'πράσινες ταράτσες' }] : []),
            ...(g.F > 0 ? [{ key: 'facade', on: stages?.facade !== false, tone: 'facade', icon: <Columns3 size={14} strokeWidth={1.7} />, name: 'πράσινες προσόψεις' }] : []),
          ]} onToggle={k => onStage?.(k as keyof Stages)} />
        </section>

        <Invest d={d} g={shown} nb={nb.pop ?? 0} unit={unitPrice} air={measured.find(i => i[0] === 'street_air_temp_shaded_street')?.[1] ?? null} on={on} />

        <Disclosure label="Πώς βγαίνουν αυτά τα νούμερα">
          <p>Κόστος από {eur(shown.low)} έως {eur(shown.high)}.{p.time ? ` Η σκιά των δέντρων έρχεται σε ${p.time[0]} με ${p.time[1]} χρόνια· η ταράτσα πρασινίζει από τον πρώτο χρόνο.` : ''} Τα υπάρχοντα δέντρα των δρόμων δεν είναι καταγεγραμμένα δημόσια: ο χάρτης δείχνει τη σκιά από δορυφόρο (δέντρα πάνω από 3 μ.) και τις φυτεύσεις από το 2024.</p>
          <p>{g.src === 'planting'
            ? 'Οι θέσεις για δέντρα είναι πεζοδρόμια τουλάχιστον 2,80 μ. (ΦΕΚ 6213/Β/2022: ελεύθερη ζώνη 1,50 μ. και φύτευση έξω από αυτήν), πεζόδρομοι και σχολικές αυλές, από το OpenStreetMap. Είναι υποψήφια σημεία για αυτοψία.'
            : 'Οι θέσεις για δέντρα είναι προσωρινά τα δέντρα που χρειάζονται για 10% σκιά. Ο χάρτης με τα πραγματικά σημεία (πεζοδρόμια, πεζόδρομοι, αυλές) έρχεται.'}
            {' '}CO2 και ρύποι ανά δέντρο: μελέτη i-Tree της Βαρκελώνης (Baró κ.ά. 2014), μεσογειακή πόλη· για την Αθήνα δεν υπάρχει αντίστοιχη μελέτη. Νερό βροχής: περίπου 400 mm τον χρόνο, που κατά το μισό τα κρατά μια πράσινη ταράτσα. Όταν γεμίσουν τα δέντρα, η μπάρα συνεχίζει σε πράσινες ταράτσες μόνο σε κτίρια του Δήμου (σχολεία, παιδικοί σταθμοί, Λέσχες Φιλίας, υπηρεσίες), περίπου το 60% της στέγης, {fmt(d.green_roof_eur_m2[1])} €/m² (εύρος {fmt(d.green_roof_eur_m2[0])} έως {fmt(d.green_roof_eur_m2[2])}). Κάθε ταράτσα θέλει στατικό έλεγχο πριν από τη δουλειά. Μετά τις ταράτσες, πράσινες προσόψεις στους τυφλούς τοίχους των ίδιων κτιρίων (περίπου 30% του τοίχου), {fmt(d.facade_eur_m2[1])} €/m², εύρος {fmt(d.facade_eur_m2[0])} έως {fmt(d.facade_eur_m2[2])}: τιμή από απόσπασμα αναζήτησης για κάθετους κήπους στη Γερμανία, να ελεγχθεί.</p>
          <ul>{p.imp.map(i => <li key={i[0]}>{EFFECT[i[0]] ?? SHORT[i[0]] ?? label(d, i[0])}: έως {fmt(i[1], 1)}{UNIT[i[4]] ?? ''}. {label(d, i[6])}, {label(d, i[5])}.</li>)}</ul>
          {nb.pop ? <PeopleViz total={nb.pop} over65={nb.pop65} under15={nb.pop014} /> : null}
        </Disclosure>
      </div>
    )
  }

  const a = areaPlan(p, pct)
  const on = pct > 0
  const shown = on ? a : areaPlan(p, 100)
  const en = roofEnergy(d, shown.q)
  return (
    <div className="view">
      {back}
      {head}
      <section className="card plan2">
        <h2>Πόσες στέγες κάνεις δροσερές;</h2>
        <div className="cover-jump"><div><span className={`cj-n ${on ? 'cool' : 'dim'}`}>{pct}%</span><span className="cj-l">από {fmt(Math.round(a.cap / 10) * 10)} m² δημοτικές στέγες</span></div></div>
        <Slider value={pct} onChange={setPct} label={`Πόσες στέγες στη γειτονιά ${nb.name}`} />
        <div className="plan-ends"><span>καμία</span><span>όλες</span></div>
      </section>
      <section className={`card result ${on ? '' : 'potential'}`} aria-live="polite">
        {!on && <p className="r-hint">Αν γίνουν όλες:</p>}
        <div className="r-main">
          <div><p className="r-n"><Num value={Math.round(shown.q / 10) * 10} /> m²</p><p className="r-l">δροσερή στέγη</p></div>
          <div><p className="r-n"><Num value={shown.cost} format={v => eur(v)} /></p><p className="r-l">από {eur(shown.low)} έως {eur(shown.high)}</p></div>
        </div>
        <div className="r-fx">
          <div><b>έως {eur(en.eur)}</b><span>λιγότερα στον κλιματισμό κάθε χρόνο</span></div>
          <div><b>~{fmt(Math.round(en.payback ?? 0))} χρόνια</b><span>για να αποσβεστεί</span></div>
        </div>
      </section>
      <Disclosure label="Πώς βγαίνουν αυτά τα νούμερα">
        <p>{`Μόνο δημοτικά κτίρια εκτός σχολείων (Λέσχες Φιλίας, ιατρεία, βρεφονηπιακοί, υπηρεσίες). Υπολογισμός: m² × ${fmt(d.energy.cooling_kwh_per_m2)} kWh ψύξης ανά m² × ${fmt(d.energy.cooling_cut * 100)}% λιγότερη ψύξη × ${fmt(d.energy.eur_per_kwh, 3)} €/kWh. Ισχύει μόνο για κτίρια με κλιματισμό. Η θέρμανση τον χειμώνα ανεβαίνει περίπου 10%. Η τιμή ${fmt(a.unit)} €/m² είναι υπόθεση μέχρι να υπάρξει προσφορά.`}</p>
      </Disclosure>
    </div>
  )
}

// The bill: the global budget is the sum of what was set in each area.
// Always on, one thin line at the top of the map: budget, rank among capitals, clear.
function Bill({ d, tab, alloc, onReset }: { d: AppData; tab: Tab; alloc: Record<string, number>; onReset: () => void }) {
  const trees = tab === 'streets'
  const ids = Object.keys(alloc).filter(id => alloc[id] > 0 && d.packages[tab][id]?.c)
  const gp = trees ? ids.map(id => greenPlan(d, id, alloc[id])) : []
  const ap = trees ? [] : ids.map(id => areaPlan(d.packages[tab][id], alloc[id]))
  const cost = trees ? gp.reduce((s, a) => s + a.cost, 0) : ap.reduce((s, a) => s + a.cost, 0)
  const cr = trees ? capitalRank(d, gp.reduce((s, a) => s + a.canopy, 0)) : null
  return (
    <footer className="bill slim">
      <span className="b-item">Προϊπολογισμός <b className={cost ? 'on' : ''}><Num value={cost} format={v => eur(v)} /></b></span>
      {cr && <span className="b-item">Θέση <b className={cr.rank < cr.baseRank ? 'up' : ''}>{cr.rank}η</b> από {cr.n}</span>}
      {ids.length > 0 && <button className="b-reset" onClick={onReset} aria-label="Καθαρισμός" title="Καθαρισμός"><RotateCcw size={15} aria-hidden /></button>}
    </footer>
  )
}

const YEARS = [{ value: '2024', label: '2024' }, { value: '2025', label: '2025' }, { value: '2026', label: '2026' }, { value: 'all', label: 'Όλα' }]

function CompareView({ d, year, setYear, side, setSide }: { d: AppData; year: string; setYear: (y: string) => void; side: Side; setSide: (s: Side) => void }) {
  const c = d.compare![year]
  const r1 = (v: number) => Math.round(v * 10) / 10
  const active = side === 'actual' ? 'recorded' : 'projected'
  return (
    <div className="view">
      <header className="head">
        <h1>Πού πήγαν τα δέντρα</h1>
        <p className="lead">Τα ίδια δέντρα, όπως φυτεύτηκαν και όπως θα πήγαιναν αν ακολουθούσαν την ανάγκη.</p>
      </header>
      <Segmented label="Έτος" value={year} onChange={setYear} options={YEARS} />
      <div className="hero"><b><Num value={c.n} /></b><span>δέντρα φυτεύτηκαν</span></div>
      <Segmented<Side> label="Τι δείχνει ο χάρτης" value={side} onChange={setSide}
        options={[{ value: 'actual', label: 'Όπως φυτεύτηκαν' }, { value: 'need', label: 'Με σειρά ανάγκης' }]} />
      <div className="block">
        <CompareBar label="Μερίδιο δέντρων σε γειτονιές με κάλυψη κάτω από 2%" recorded={r1(c.actual.share_bare_pct)} projected={r1(c.need.share_bare_pct)} unit="%" max={100} active={active} />
        <CompareBar label="Δέντρα ανά 1.000 κατοίκους σε αυτές" recorded={r1(c.actual.per1000_bare)} projected={r1(c.need.per1000_bare)} unit="" max={Math.max(c.actual.per1000_bare, c.need.per1000_bare)} active={active} />
        <CompareBar label="Μέση κάλυψη εκεί που πήγαν τα δέντρα" recorded={r1(c.actual.mean_cover_pct)} projected={r1(c.need.mean_cover_pct)} unit="%" max={Math.max(c.actual.mean_cover_pct, c.need.mean_cover_pct)} active={active} />
      </div>
      <p className="note">Η σειρά ανάγκης δείχνει πού λείπουν δέντρα. Δεν είναι σχέδιο φύτευσης, γιατί δεν υπάρχει κατάλογος με τα σημεία όπου χωράει δέντρο.</p>
    </div>
  )
}

// Data layers: one value per neighbourhood. The user picks which one colours the map.
// One data layer: what it shows, where it is worst, and its source.
function LayersView({ d, layer, sel, onPick, onTool }: { d: AppData; layer: string; sel: string | null; onPick: (id: string | null) => void; onTool: (t: Tool) => void }) {
  const L: Layer = d.layers.find(x => x.id === layer) ?? d.layers[0]
  const I = INSIGHTS[L.id] ?? GENERIC
  const unit = I.unit ?? L.unit
  const n = Object.keys(d.neighbourhoods).length
  const covered = Object.keys(L.values).length
  const digits = (v: number) => (Math.abs(v) >= 100 ? 0 : Math.abs(v) < 1 ? 2 : 1)
  const show = (v: number) => `${fmt(v, digits(v))}${unit === '%' ? '%' : unit ? ` ${unit}` : ''}`
  const all = Object.values(L.values), max = Math.max(...all), min = Math.min(...all)
  const sortedV = [...all].sort((a, b) => a - b)
  const median = sortedV[Math.floor(sortedV.length / 2)]
  // Where the city median sits on the bar, which runs from better (left) to worse (right).
  const pos = (v: number) => Math.round(100 * (max > min ? (L.worse === 'low' ? (max - v) / (max - min) : (v - min) / (max - min)) : 0.5))
  const worst = Object.entries(L.values).sort((a, b) => (L.worse === 'low' ? a[1] - b[1] : b[1] - a[1])).slice(0, 10)
  const gap = L.id === 'sensor_gap'
  const worseThan = (v: number, t: number) => (L.worse === 'low' ? v < t : v > t)
  const ref = I.ref?.value
  const hitIds = Object.entries(L.values).filter(([, v]) => worseThan(v, ref ?? median)).map(([id]) => id)
  const people = hitIds.reduce((s, id) => s + (d.neighbourhoods[id].pop ?? 0), 0)
  const totalPop = Object.values(d.neighbourhoods).reduce((s, x) => s + (x.pop ?? 0), 0)
  const dots = Math.round(totalPop / 10000), on = Math.round(people / 10000)
  const tone = L.worse === 'none' ? 'neutral' : 'need'
  return (
    <div className="view">
      <header className="lhead">
        <span className={`tile big ${tone}`} aria-hidden>{iconFor(L.id, 22)}</span>
        <div>
          <h1>{L.name}</h1>
          {L.update && <p className="lfresh">{L.update === 'live' ? <><i className="live" aria-hidden />από τους αισθητήρες του Δήμου, τώρα</> : L.update}</p>}
        </div>
      </header>
      {I.meaning && <p className="lead">{I.meaning}</p>}
      {sel && <div className="card sel-card"><span>{d.neighbourhoods[sel].name}</span><span className={`pill ${tone}`}>{L.values[sel] !== undefined ? show(L.values[sel]) : 'χωρίς μέτρηση'}</span></div>}

      {L.worse !== 'none' && people > 0 ? (
        <div className="card">
          <p className="hero-n">{fmt(Math.round(people / 1000))}k</p>
          <p className="hero-cap">κάτοικοι ζουν σε {fmt(hitIds.length)} γειτονιές {ref !== undefined ? `${L.worse === 'low' ? 'κάτω από' : 'πάνω από'} ${/^στόχος/.test(I.ref!.label) ? 'τον ' : /^όριο/.test(I.ref!.label) ? 'το ' : ''}${I.ref!.label}` : 'που υστερούν σε σχέση με τη μέση γειτονιά του Δήμου'}</p>
          <div className="dots" aria-hidden>{Array.from({ length: dots }, (_, i) => <i key={i} className={i < on ? 'on' : ''} />)}</div>
        </div>
      ) : (
        <div className="card">
          <p className="hero-n">{show(median)}</p>
          <p className="hero-cap">στη μέση γειτονιά · {covered === n ? `${n} γειτονιές` : `${covered} από ${n} γειτονιές έχουν τιμή`}</p>
        </div>
      )}

      <div className="card">
        <h2>Η μέση γειτονιά</h2>
        <div className={`gauge ${L.worse === 'none' ? 'seq' : ''}`}>
          {I.ref && <b className="gref" style={{ left: `${Math.max(0, Math.min(100, pos(I.ref.value)))}%` }} />}
          <span className="gmark" style={{ left: `${pos(median)}%` }}><em>{show(median)}</em></span>
        </div>
        <div className="gends"><span>{L.worse === 'none' ? show(min) : 'ευνοϊκό'}</span><span>{L.worse === 'none' ? show(max) : 'κρίσιμο'}</span></div>
        {I.ref && <p className="gref-l">┃ {I.ref.label}</p>}
      </div>

      <div className="card">
        <h2>{gap ? 'Πού ένας αισθητήρας θα κάλυπτε περισσότερους' : L.worse === 'none' ? 'Οι υψηλότερες τιμές' : 'Γειτονιές με τη μεγαλύτερη ανάγκη'}</h2>
        <ol className="rank">
          {worst.slice(0, 6).map(([id, v], i) => (
            <li key={id}>
              <button className={sel === id ? 'on' : ''} onClick={() => onPick(id)}>
                <span className="rk">{i + 1}</span>
                <span className="nm">{d.neighbourhoods[id].name}{d.neighbourhoods[id].pop ? <small>{fmt(Math.round((d.neighbourhoods[id].pop ?? 0) / 10) * 10)} κάτοικοι</small> : null}</span>
                <span className={`pill ${tone}`}>{show(v)}</span>
              </button>
            </li>
          ))}
        </ol>
      </div>

      {I.actions.length > 0 && (
        <div className="acts">
          {I.actions.map((a, i) => a.tool
            ? <button key={a.text} className={`bigact ${i === 0 ? 'pri' : ''}`} onClick={() => onTool(a.tool!)}><span className="tile" aria-hidden>{iconFor(a.tool, 18)}</span><span className="t">{a.text}</span><ChevronRight size={18} aria-hidden /></button>
            : <div key={a.text} className="bigact static"><span className="tile" aria-hidden><Sparkle /></span><span className="t">{a.text}</span></div>)}
        </div>
      )}
      <p className="src">{L.source}{I.refSource ? ` · ${I.refSource}` : ''}</p>
    </div>
  )
}

const Sparkle = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6" /></svg>

// Under the editor, in a data layer: what this layer says about the selected area, and where it ranks.
function LayerHere({ d, layer, id }: { d: AppData; layer: string; id: string }) {
  const L: Layer = d.layers.find(x => x.id === layer) ?? d.layers[0]
  const I = INSIGHTS[L.id] ?? GENERIC
  const unit = I.unit ?? L.unit
  const v = L.values[id]
  const all = Object.values(L.values)
  const show = (x: number) => `${fmt(x, Math.abs(x) >= 100 ? 0 : Math.abs(x) < 1 ? 2 : 1)}${unit === '%' ? '%' : unit ? ` ${unit}` : ''}`
  const worseCount = v === undefined ? 0 : all.filter(x => (L.worse === 'low' ? x < v : x > v)).length
  const median = [...all].sort((a, b) => a - b)[Math.floor(all.length / 2)]
  return (
    <div className="card here">
      <div className="lhead"><span className={`tile ${L.worse === 'none' ? 'neutral' : 'need'}`} aria-hidden>{iconFor(L.id)}</span><h2>{L.name}</h2></div>
      {v === undefined
        ? <p className="hero-cap">Δεν υπάρχει μέτρηση εδώ.</p>
        : <>
            <p className="big">{show(v)}</p>
            <p className="cap">{L.worse === 'none' ? `μέση γειτονιά ${show(median)}` : `${worseCount + 1}η σε ανάγκη από ${all.length} γειτονιές · μέση γειτονιά ${show(median)}`}</p>
          </>}
    </div>
  )
}

// Sidebar: the two decision tools first, then every data layer, one under the other.
const ICON: Record<string, React.ReactNode> = {
  streets: <TreePine size={18} />, buildings: <School size={18} />,
  tree_cover: <Trees size={18} />, ndvi_2025: <Leaf size={18} />, tree_height: <Sprout size={18} />, zoned_green: <Leaf size={18} />, pocket_parks: <Pin size={18} />,
  heat_night: <Thermometer size={18} />, hours_35: <Sun size={18} />, lst_summer_day: <Sun size={18} />, albedo_2025: <Palette size={18} />, imperviousness: <Building2 size={18} />,
  pm25: <Wind size={18} />, no2: <Factory size={18} />, density: <Users size={18} />, sensor_gap: <RadioTower size={18} />, elevation: <Mountain size={18} />,
  osm_transit_stops: <Bus size={18} />, osm_bike_km: <Bike size={18} />, osm_pedestrian_km: <Footprints size={18} />, osm_food_shops: <ShoppingBasket size={18} />,
  osm_cafes_restaurants: <Coffee size={18} />, osm_pharmacies: <Pill size={18} />, osm_drinking_water: <Droplets size={18} />, osm_benches: <Armchair size={18} />,
  osm_parking: <ParkingSquare size={18} />, airbnb_listings: <Home size={18} />,
  city_rail_distance: <TrainFront size={18} />, city_kep_distance: <FileText size={18} />, city_culture_distance: <Landmark size={18} />, city_sports: <Dumbbell size={18} />,
  city_fountains: <Droplets size={18} />, city_ev_chargers: <PlugZap size={18} />, city_controlled_parking: <ParkingSquare size={18} />, city_archaeology_zone: <Landmark size={18} />,
  city_building_coefficient: <Building2 size={18} />,
}
// Sidebar order: greenery, heat, surfaces, air, people, then everything else (OSM, City services) as it arrives.
const ORDER = ['tree_cover', 'ndvi_2025', 'tree_height', 'zoned_green', 'pocket_parks', 'heat_night', 'hours_35', 'lst_summer_day', 'imperviousness', 'albedo_2025', 'pm25', 'no2', 'density', 'sensor_gap', 'airbnb_listings', 'city_building_coefficient', 'city_rail_distance', 'city_kep_distance', 'city_culture_distance', 'city_sports', 'city_fountains', 'city_ev_chargers', 'city_controlled_parking', 'city_archaeology_zone', 'elevation']
const order = (id: string) => { const i = ORDER.indexOf(id); return i < 0 ? 100 : i }
const iconFor = (id: string, _size = 18): React.ReactNode => ICON[id] ?? (/cult|museum|monument/.test(id) ? <Landmark size={18} /> : /sport|gym/.test(id) ? <Dumbbell size={18} /> : /wifi/.test(id) ? <Wifi size={18} /> : /recycl|waste|bin/.test(id) ? <Recycle size={18} /> : /charg|ev/.test(id) ? <PlugZap size={18} /> : /social|kapi|kdap|care/.test(id) ? <HeartHandshake size={18} /> : <Pin size={18} />)


export default function App() {
  const [d, setD] = useState<AppData | null>(null)
  const [active, setActive] = useState<string>('streets')
  const [alloc, setAlloc] = useState<Record<Tab, Record<string, number>>>({ streets: {}, buildings: {} })
  const [sel, setSel] = useState<string | null>(null)
  const [stages, setStages] = useState<Stages>({ roof: true, facade: true })
  STAGES = stages
  const onStage = (k: keyof Stages) => setStages(x => ({ ...x, [k]: !x[k] }))
  const [year, setYear] = useState('all')
  const [side, setSide] = useState<Side>('actual')
  const [show, setShow] = useState({ planted: true, canopy: true })
  const body = useRef<HTMLDivElement>(null)

  useEffect(() => { DATA.app.then(setD) }, [])
  useEffect(() => { body.current?.scrollTo({ top: 0 }) }, [sel, active])
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') setSel(null) }
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [])

  // 'compare' stays in the code for later; the sidebar does not offer it now.
  const mode = (active === 'streets' || active === 'buildings' ? active : 'layers') as Mode
  const layer = mode === 'layers' ? active : ''
  const tab: Tab = mode === 'buildings' ? 'buildings' : 'streets'
  const hot = useMemo(() => d ? ranked(d, tab).slice(0, 12).map(([id]) => id) : [], [d, tab])
  if (!d) return <div className="loading"><div className="pulse" /></div>

  const setPct = (id: string, v: number) => setAlloc(a => ({ ...a, [tab]: { ...a[tab], [id]: v } }))
  return (
    <div className="app">
      <main className="stage">
        <nav className="dock" aria-label="Επίπεδα του χάρτη">
          {[{ id: 'streets', name: 'Έλλειψη σκιάς' }, ...[...d.layers].sort((a, b) => order(a.id) - order(b.id)).map(l => ({ id: l.id, name: l.name }))].map(x => (
            <button key={x.id} className={`bub ${active === x.id ? 'on' : ''}`} aria-label={x.name} aria-current={active === x.id ? 'page' : undefined} onClick={() => { setActive(x.id); setSel(null) }}>
              {iconFor(x.id)}<span className="tip" aria-hidden>{x.name}</span>{d.layers.find(l => l.id === x.id)?.update === 'live' && <i className="live" aria-hidden />}
            </button>
          ))}
        </nav>
        <nav className="ctl" aria-label="Τι δείχνει ο χάρτης">
          {([['planted', 'Δέντρα που φυτεύτηκαν 2024-26', <Shovel key="i" size={18} />], ['canopy', 'Δέντρα από δορυφόρο', <Satellite key="i" size={18} />]] as const).map(([k, name, icon]) => (
            <button key={k} className={`bub tog ${show[k] ? 'lit' : ''}`} aria-label={name} aria-pressed={show[k]} onClick={() => setShow(s => ({ ...s, [k]: !s[k] }))}>
              {icon}<span className="tip" aria-hidden>{name}</span>
            </button>
          ))}
        </nav>
        <div className="topbar">
          {mode !== 'compare' && <Bill d={d} tab={tab} alloc={alloc[tab]} onReset={() => setAlloc(a => ({ ...a, [tab]: {} }))} />}
          {sel && <button className="map-exit" onClick={() => setSel(null)} aria-label="Έξοδος, πίσω σε όλη την πόλη"><ArrowUpLeft size={18} aria-hidden />Όλη η πόλη</button>}
        </div>
        <MapView show={show} focus={(mode === 'streets' || mode === 'layers') && sel ? (() => { const g = greenPlan(d, sel, alloc.streets[sel] ?? 0); return { trees: g.trees, roof: g.roof } })() : null} data={d} mode={mode} alloc={mode === 'compare' ? {} : mode === 'layers' ? alloc.streets : alloc[tab]} hot={mode === 'compare' || mode === 'layers' ? [] : hot} selected={sel} onSelect={setSel} cmp={{ year, side }} layer={layer} />
      </main>

      <aside className="panel">
        <div className="panel-body" ref={body} key={`${mode}-${sel ?? ''}`}>
          {mode === 'layers'
            ? (sel
              ? <div className="view">
                  <AreaView d={d} id={sel} tab="streets" pct={alloc.streets[sel] ?? 0} setPct={v => setAlloc(a => ({ ...a, streets: { ...a.streets, [sel]: v } }))} onBack={() => setSel(null)} stages={stages} onStage={onStage} />
                  <LayerHere d={d} layer={layer} id={sel} />
                </div>
              : <LayersView d={d} layer={layer} sel={sel} onPick={setSel} onTool={t => { setActive(t); setSel(null) }} />)
            : mode === 'compare'
            ? <CompareView d={d} year={year} setYear={setYear} side={side} setSide={setSide} />
            : sel
              ? <AreaView d={d} id={sel} tab={tab} pct={alloc[tab][sel] ?? 0} setPct={v => setPct(sel, v)} onBack={() => setSel(null)} stages={stages} onStage={onStage} />
              : <Overview d={d} tab={tab} alloc={alloc[tab]} onPick={setSel} />}
        </div>

      </aside>
    </div>
  )
}
