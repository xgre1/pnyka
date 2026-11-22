// Types and helpers for the data built by app/scripts/build_data.py from engine/packages.json.

export type Tab = 'streets' | 'buildings'
export type Mode = Tab | 'compare' | 'layers'
export interface Layer { id: string; name: string; unit: string; kind: string; source: string; note: string; worse: 'high' | 'low' | 'none'; update: string; values: Record<string, number> }
export type Side = 'actual' | 'need'

export interface CmpSide {
  n_trees: number; share_bare_pct: number; per1000_bare: number; per1000_rest: number; top10_share_pct: number
  mean_cover_pct: number; neighbourhoods_receiving: number; residents_receiving: number
  cost_central_eur: number | null; schools_low_canopy_reached: number | null
  by: Record<string, number>
}
export type Compare = Record<string, { n: number; actual: CmpSide; need: CmpSide }>
// [metric_code, value_up_to, low, high, unit, status, source_code]
export type Impact = [string, number | null, number | null, number | null, string, string, string]
// [indicator_code, value, percentile, unit]
export type Why = [string, number, number | null, string]

export interface Pkg {
  rank: number
  q: [number, number, number]
  c: [number, number, number] | null
  sites: number | null
  cap: number | null
  time: [number, number] | null
  why: Why[]
  imp: Impact[]
  gaps: string[]; spots?: number; spots_parking?: number; spots_src?: string; groof?: number; facade?: number }

export interface Nb { name: string; raw: string; dk: number | null; pop: number | null; pop65: number | null; pop014: number | null; area_km2: number | null; tree_pct: number | null }

export interface AppData {
  neighbourhoods: Record<string, Nb>
  packages: Record<Tab, Record<string, Pkg>>
  counts: Record<Tab, number>
  labels: Record<string, { label: string; long: string }>
  with_plantings: boolean
  compare: Compare | null
  layers: Layer[]
  capitals: [string, number][]
  green_roof_eur_m2: [number, number, number]
  facade_eur_m2: [number, number, number]
  impact: { co2_kg_per_tree_yr: number; pollutants_kg_per_tree_yr: number; roof_rain_m3_per_m2_yr: number }
  energy: { cooling_kwh_per_m2: number; cooling_cut: number; heating_increase: number; eur_per_kwh: number; co2_kg_per_kwh: number; price_eur_m2: number }
  city: { tree_cover_pct: number; schools: number; schools_low_canopy: number; plantings_2024_2026: number | null; roof_school_m2: number; roof_other_m2: number; green_roofs_existing: number; green_roofs_existing_m2: number; sensor_gap_neighbourhoods: number; sensor_gap_residents: number }
}

export const STEPS = [100e3, 250e3, 500e3, 750e3, 1e6, 1.5e6, 2e6, 3e6, 5e6]

export const label = (d: AppData, c: string) => d.labels[c]?.label ?? c
export const longLabel = (d: AppData, c: string) => d.labels[c]?.long ?? ''

export const fmt = (n: number | null | undefined, digits = 0) =>
  n == null ? '' : n.toLocaleString('el-GR', { maximumFractionDigits: digits, minimumFractionDigits: 0 })

export const eur = (n: number | null | undefined) => {
  if (n == null) return ''
  if (n >= 1e6) return `${fmt(n / 1e6, 2)}M €`
  if (n < 1000) return `${fmt(Math.round(n / 10) * 10)} €`
  return `${fmt(Math.round(n / 1000))}k €`
}

export const UNIT: Record<string, string> = {
  degC: ' °C', percent: '%', percent_of_area: '%', m2: ' m²', persons_per_km2: ' /km²', trees_per_1000_residents: '',
}

// Short phrases for the big impact chips (UI copy). The full sentence comes from engine/labels_el.csv.
export const SHORT: Record<string, string> = {
  pavement_surface_temp_under_shade: 'πεζοδρόμιο στη σκιά',
  street_air_temp_shaded_street: 'αέρας στον δρόμο',
  street_air_temp_very_shaded_street: 'αέρας σε πολύ σκιερό δρόμο',
  felt_temp_under_tree: 'αίσθηση θερμοκρασίας κάτω από δέντρο',
  neighbourhood_mean_air_temp: 'μέση θερμοκρασία γειτονιάς',
  classroom_air_temp_summer: 'μέσα στην τάξη',
  roof_surface_temp: 'επιφάνεια στέγης',
  building_cooling_load: 'ψύξη που χρειάζεται το κτίριο',
}

// Neighbourhood selection for a budget. Decision σημείωμα ομάδας:
// each tab has its own budget; whole packages in engine rank order (need), skipping any that no longer fits.
export function select(d: AppData, tab: Tab, budget: number) {
  const list = Object.entries(d.packages[tab])
    .filter(([, p]) => p.c)
    .sort((a, b) => a[1].rank - b[1].rank)
  let left = budget
  const chosen: string[] = []
  for (const [id, p] of list) {
    const c = p.c![1]
    if (c <= left) { chosen.push(id); left -= c }
  }
  const pk = chosen.map(id => d.packages[tab][id])
  return {
    chosen,
    used: budget - left,
    quantity: pk.reduce((s, p) => s + p.q[1], 0),
    sites: pk.reduce((s, p) => s + (p.sites ?? 0), 0),
    people: chosen.reduce((s, id) => s + (d.neighbourhoods[id].pop ?? 0), 0),
  }
}

// All data is static JSON built by app/scripts/build_data.py. Start every request at module load,
// in parallel, so nothing waits on anything else.
const j = (u: string) => fetch(u).then(r => r.json())
export const DATA = {
  app: j('/data/app.json') as Promise<AppData>,
  nb: j('/data/neighbourhoods.geojson'),
  sites: j('/data/sites.json'),
  plant: j('/data/plantings.json').catch(() => null),
  spots: j('/data/spots.json').catch(() => ({})),
  roofs: j('/data/roofs.json').catch(() => ({ type: 'FeatureCollection', features: [] })),
}

// Cool roof on an air-conditioned municipal building: an upper-bound yearly saving on cooling electricity.
export function roofEnergy(d: AppData, m2: number) {
  const e = d.energy
  const kwh = m2 * e.cooling_kwh_per_m2 * e.cooling_cut
  const eur = kwh * e.eur_per_kwh
  return { kwh, eur, co2t: (kwh * e.co2_kg_per_kwh) / 1000, payback: eur > 0 ? (m2 * e.price_eur_m2) / eur : null }
}

const EL: Record<string, string> = { Valletta: 'Βαλέτα', Athens: 'Αθήνα', Nicosia: 'Λευκωσία', Pristina: 'Πρίστινα', Skopje: 'Σκόπια', Paris: 'Παρίσι', Bucharest: 'Βουκουρέστι', 'Reykjavík': 'Ρέικιαβικ', Copenhagen: 'Κοπεγχάγη', Belgrade: 'Βελιγράδι', Amsterdam: 'Άμστερνταμ', Tirana: 'Τίρανα', Podgorica: 'Ποντγκόριτσα', Rome: 'Ρώμη', Dublin: 'Δουβλίνο', Ankara: 'Άγκυρα', Budapest: 'Βουδαπέστη', Prague: 'Πράγα', Bratislava: 'Μπρατισλάβα', Luxembourg: 'Λουξεμβούργο', Brussels: 'Βρυξέλλες', Vienna: 'Βιέννη', Sarajevo: 'Σαράγεβο', Sofia: 'Σόφια', Riga: 'Ρίγα', Warsaw: 'Βαρσοβία', Stockholm: 'Στοκχόλμη', Lisbon: 'Λισαβόνα', Tallinn: 'Ταλίν', Berlin: 'Βερολίνο', Bern: 'Βέρνη', Madrid: 'Μαδρίτη', Vilnius: 'Βίλνιους', Helsinki: 'Ελσίνκι', Ljubljana: 'Λιουμπλιάνα', Zagreb: 'Ζάγκρεμπ', Oslo: 'Όσλο' }
export const elCity = (n: string) => EL[n] ?? n

// Where Athens stands among 37 European capitals in tree cover (EEA), if `addedM2` of grown canopy is added on top of its 11%.
export function capitalRank(d: AppData, addedM2: number) {
  const area = Object.values(d.neighbourhoods).reduce((s, n) => s + (n.area_km2 ?? 0), 0) * 1e6
  const base = d.capitals.find(c => c[0] === 'Athens')?.[1] ?? 11
  const pct = base + (area ? (addedM2 / area) * 100 : 0)
  const others = d.capitals.filter(c => c[0] !== 'Athens')
  const rank = 1 + others.filter(c => c[1] > pct).length
  const passed = others.filter(c => c[1] > base && c[1] < pct).sort((a, b) => a[1] - b[1]).map(c => elCity(c[0]))
  const nx = others.filter(c => c[1] >= pct).sort((a, b) => a[1] - b[1])[0]
  return { pct, base, rank, baseRank: 1 + others.filter(c => c[1] > base).length, n: d.capitals.length, passed, next: nx ? [elCity(nx[0]), nx[1]] as [string, number] : null }
}
