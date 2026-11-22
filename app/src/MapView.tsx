import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import type { Map as MLMap, StyleSpecification, ExpressionSpecification, LngLatBoundsLike, LngLatLike } from 'maplibre-gl'
import { type AppData, type Mode, type Side, DATA } from './data'
import './map.css'

// MapLibre is the heaviest dependency: load it as its own chunk, starting as soon as this module
// is evaluated, so it downloads in parallel with /data/app.json instead of blocking the first paint.
// Static import: Vite emits a modulepreload for the maplibre chunk, so it downloads in parallel with the app and the data.
const mlModule = Promise.resolve(maplibregl)

interface Props {
  data: AppData
  mode: Mode
  alloc: Record<string, number>  // id -> % of the full intervention (0-100), set by the user per area
  hot: string[]                   // the areas with the most need, outlined
  selected: string | null
  onSelect: (id: string | null) => void
  cmp: { year: string; side: Side }
  layer?: string                  // in 'layers' mode: which data layer colours the map
  focus?: { trees: number; roof: number } | null  // selected area in the trees tool: how many spots and roof m2 are filled
  show?: { planted: boolean; canopy: boolean }   // toggles: trees planted 2024-26, satellite canopy
}

type RGB = [number, number, number]
type Cell = { h: number; c: RGB }
type Box = [number, number, number, number]

// ---------- colour ----------
const hex = (s: string, fb: string): RGB => {
  const m = /^#?([0-9a-f]{6})$/i.exec(s.trim()) ?? /^#?([0-9a-f]{6})$/i.exec(fb)!
  const n = parseInt(m[1], 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
const tok = (name: string, fb: string): RGB => {
  try { return hex(getComputedStyle(document.documentElement).getPropertyValue(name), fb) } catch { return hex(fb, fb) }
}
const mix = (a: RGB, b: RGB, t: number): RGB => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]
const css = (c: RGB) => `rgb(${Math.round(c[0])},${Math.round(c[1])},${Math.round(c[2])})`
const lighten = (c: RGB, t: number) => mix(c, [255, 255, 255], t)

// ---------- motion ----------
const easeOut = (k: number) => 1 - Math.pow(1 - k, 4)                                          // heights, colour
const easeInOut = (k: number) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2)  // camera
const reducedMotion = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

// Heights shrink when zoomed in so the streets stay readable; flat from zoom 15. zoom must be the top-level input.
const H = (v: ExpressionSpecification | number): ExpressionSpecification =>
  ['interpolate', ['linear'], ['zoom'], 12, v, 14, ['*', v, 0.25], 15, 0]
const FS_H: ExpressionSpecification = ['coalesce', ['feature-state', 'h'], 0]
const capOf = (k: number) => ({ 'fill-extrusion-base': H(FS_H), 'fill-extrusion-height': H(['+', FS_H, k]) })
const NOTHING: ExpressionSpecification = ['boolean', false]
// A planted tree: the small light dot (with 'plant-glow' under it).
const TREE_DOT = (core: string) => ({
  'circle-radius': ['interpolate', ['linear'], ['zoom'], 11, 0.6, 16, 2] as ExpressionSpecification,
  'circle-color': core, 'circle-opacity': 0.85,
})
const idIn = (ids: string[]): ExpressionSpecification => ['in', ['to-string', ['get', 'id']], ['literal', ids]]

// ---------- base map: built here from the OpenFreeMap vector tiles, only what the data needs ----------
function baseStyle(bg: string): StyleSpecification {
  const roads = (id: string, classes: string[], minzoom: number, w: [number, number], a: number) => ({
    id, type: 'line' as const, source: 'omt', 'source-layer': 'transportation', minzoom,
    filter: ['match', ['get', 'class'], classes, true, false] as ExpressionSpecification,
    layout: { 'line-cap': 'round' as const, 'line-join': 'round' as const },
    paint: { 'line-color': `rgba(255,255,255,${a})`, 'line-width': ['interpolate', ['exponential', 1.6], ['zoom'], 11, w[0], 17, w[1]] as ExpressionSpecification },
  })
  return {
    version: 8,
    glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
    sources: {
      omt: { type: 'vector', url: 'https://tiles.openfreemap.org/planet' },
    },
    layers: [
      { id: 'bg', type: 'background', paint: { 'background-color': bg } },
      { id: 'park', type: 'fill', source: 'omt', 'source-layer': 'park', paint: { 'fill-color': 'rgba(52,224,161,0.035)' } },
      { id: 'wood', type: 'fill', source: 'omt', 'source-layer': 'landcover', filter: ['match', ['get', 'class'], ['wood', 'grass'], true, false], paint: { 'fill-color': 'rgba(52,224,161,0.025)' } },
      { id: 'water', type: 'fill', source: 'omt', 'source-layer': 'water', filter: ['!=', ['get', 'brunnel'], 'tunnel'], paint: { 'fill-color': '#0b1622' } },
      { id: 'building', type: 'fill', source: 'omt', 'source-layer': 'building', minzoom: 14.5, paint: { 'fill-color': 'rgba(255,255,255,0.028)' } },
      roads('road-minor', ['minor', 'service'], 12.5, [0.3, 3], 0.09),
      roads('road-path', ['path', 'pedestrian'], 14, [0.3, 2], 0.08),
      roads('road-major', ['primary', 'secondary', 'tertiary', 'trunk'], 10, [0.5, 6], 0.13),
      roads('road-motorway', ['motorway'], 9, [0.6, 7], 0.15),
    ],
  }
}

// The city itself, on top of the data colour: 3D buildings and street names once you zoom in.
function addCity(m: MLMap) {
  m.addLayer({
    id: 'bld-3d', type: 'fill-extrusion', source: 'omt', 'source-layer': 'building', minzoom: 14,
    paint: {
      'fill-extrusion-color': '#c9d2dc',
      'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 12],
      'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
      'fill-extrusion-opacity': ['interpolate', ['linear'], ['zoom'], 14, 0, 15, 0.5],
    },
  })
  m.addLayer({
    id: 'street-name', type: 'symbol', source: 'omt', 'source-layer': 'transportation_name', minzoom: 14.5,
    layout: { 'symbol-placement': 'line', 'text-field': ['coalesce', ['get', 'name:el'], ['get', 'name']], 'text-font': ['Noto Sans Regular'], 'text-size': ['interpolate', ['linear'], ['zoom'], 14.5, 10, 17, 13], 'text-max-angle': 30 },
    paint: { 'text-color': 'rgba(242,245,247,0.75)', 'text-halo-color': 'rgba(10,13,18,0.9)', 'text-halo-width': 1.4 },
  })
}

// Labels for major places only, in Greek, on top but quiet.
function addLabels(m: MLMap) {
  m.addLayer({
    id: 'place', type: 'symbol', source: 'omt', 'source-layer': 'place',
    filter: ['match', ['get', 'class'], ['city', 'town'], true, false],
    layout: { 'text-field': ['coalesce', ['get', 'name:el'], ['get', 'name']], 'text-font': ['Noto Sans Regular'], 'text-size': ['interpolate', ['linear'], ['zoom'], 10, 11, 14, 13], 'text-letter-spacing': 0.04, 'text-max-width': 8 },
    paint: { 'text-color': 'rgba(242,245,247,0.42)', 'text-halo-color': 'rgba(10,13,18,0.85)', 'text-halo-width': 1.4, 'text-halo-blur': 0.5 },
  })
}

const box = (): Box => [180, 90, -180, -90]
const walk = (c: unknown, b: Box): void => {
  if (Array.isArray(c) && typeof c[0] === 'number') { b[0] = Math.min(b[0], c[0]); b[1] = Math.min(b[1], c[1] as number); b[2] = Math.max(b[2], c[0]); b[3] = Math.max(b[3], c[1] as number) }
  else if (Array.isArray(c)) c.forEach(x => walk(x, b))
}
const toBounds = (b: Box): LngLatBoundsLike => [[b[0], b[1]], [b[2], b[3]]]

export default function MapView({ data, mode, alloc, hot, selected, onSelect, cmp, layer, focus, show = { planted: true, canopy: true } }: Props) {
  const el = useRef<HTMLDivElement>(null)
  const map = useRef<MLMap | null>(null)
  const ready = useRef(false)
  const cells = useRef<Record<string, Cell>>({})
  const anim = useRef(0)
  const bounds = useRef<Record<string, Box>>({})
  const home = useRef<{ center: LngLatLike; zoom: number } | null>(null)
  const hoverId = useRef<string | null>(null)
  const selRef = useRef<string | null>(selected)
  selRef.current = selected
  const pulseIds = useRef<string[]>([])
  const pending = useRef<Record<string, () => void>>({})
  const whenReady = (key: string, fn: () => void) => { if (ready.current && map.current) fn(); else pending.current[key] = fn }
  const onSelectRef = useRef(onSelect)
  onSelectRef.current = onSelect
  const ids = Object.keys(data.neighbourhoods)

  // Colours come from the design tokens.
  const C = useRef({ need: tok('--need', '#ff6a3d'), cool: tok('--cool', '#34e0a1'), bg: tok('--bg', '#0a0d12') }).current
  // Sequential need ramp: quiet slate (little need) to --need (most need).
  // Mid stops lean plum, not brown, so the ramp stays clean between slate and orange.
  // Diverging: calm blue = better than most of the city, neutral = typical, warm = worse. Not everything is red.
  const GOOD: RGB = [64, 132, 196], MID: RGB = [52, 58, 72]
  const RAMP: RGB[] = [GOOD, mix(GOOD, MID, 0.55), MID, mix(MID, C.need, 0.5), C.need]
  // Neutral layers (e.g. elevation): one calm hue, no judgement.
  const SEQ: RGB[] = [MID, [70, 92, 150], [118, 150, 230]]
  const seq = (t: number): RGB => { const x = Math.max(0, Math.min(1, t)) * (SEQ.length - 1); const i = Math.min(SEQ.length - 2, Math.floor(x)); return mix(SEQ[i], SEQ[i + 1], x - i) }
  const ramp = (t: number): RGB => { const x = Math.max(0, Math.min(1, t)) * (RAMP.length - 1); const i = Math.min(RAMP.length - 2, Math.floor(x)); return mix(RAMP[i], RAMP[i + 1], x - i) }
  const NONE: RGB = mix(C.bg, [255, 255, 255], 0.05)
  const NEUTRAL: RGB = [74, 84, 98]          // compare, as planted: recorded, so neutral
  const PROJ: RGB = mix(C.cool, C.bg, 0.22)  // compare, by need: projected, mint body under a lighter roof

  // Tween only the areas whose height or colour changed: a slider move touches one area, not 144.
  const tweenTo = (next: Record<string, Cell>) => {
    const m = map.current
    if (!m) return
    cancelAnimationFrame(anim.current)
    const changed = ids.filter(id => {
      const a = cells.current[id], b = next[id]
      return !a || Math.abs(a.h - b.h) > 0.5 || Math.abs(a.c[0] - b.c[0]) + Math.abs(a.c[1] - b.c[1]) + Math.abs(a.c[2] - b.c[2]) > 1.5
    })
    if (!changed.length) return
    const from: Record<string, Cell> = {}
    for (const id of changed) from[id] = cells.current[id] ?? { h: 0, c: next[id].c }
    // First paint is instant; later changes animate.
    const dur = reducedMotion() || !Object.keys(cells.current).length ? 0 : 650
    const t0 = performance.now()
    const step = (t: number) => {
      const k = dur ? Math.min(1, (t - t0) / dur) : 1
      const e = easeOut(k)
      for (const id of changed) {
        const a = from[id], b = next[id]
        const cell = { h: a.h + (b.h - a.h) * e, c: mix(a.c, b.c, e) }
        cells.current[id] = cell
        m.setFeatureState({ source: 'nb', id }, { h: cell.h, c: css(cell.c) })
      }
      if (k < 1) anim.current = requestAnimationFrame(step)
    }
    if (!dur) step(performance.now()); else anim.current = requestAnimationFrame(step)
  }

  const setHl = () => {
    const m = map.current
    if (!m || !m.getLayer('nb-hl')) return
    m.setFilter('nb-hl', idIn([hoverId.current, selRef.current].filter(Boolean) as string[]))
  }

  // Map, sources and layers: once per data.
  useEffect(() => {
    let m: MLMap | null = null
    let cancelled = false
    let pulseRaf = 0
    ;(async () => {
      const maplibregl = await mlModule
      if (cancelled || !el.current) return
      const phone = window.innerWidth < 900
      m = new maplibregl.Map({
        container: el.current, style: baseStyle(css(C.bg)), center: [23.735, 37.99], zoom: 12.3, pitch: 50, bearing: -15,
        attributionControl: false, maxPitch: 70, fadeDuration: 0,
      })
      map.current = m
      ;(window as unknown as { __map: MLMap }).__map = m
      m.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right')
      m.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left')
      // On a phone the attribution starts folded behind its (i) button so it does not cover the map.
      if (phone) m.once('load', () => el.current?.querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show'))
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, className: 'map-hover', offset: 14, maxWidth: 'none' })

      // Listen for the style before awaiting the data: if the style finishes first, its event must not be missed.
      const styleReady = new Promise<void>(res => { m!.once('style.load', () => res()); if ((m as unknown as { style?: { _loaded?: boolean } }).style?._loaded) res() })
      const [nbGeo, sites, pts] = await Promise.all([DATA.nb, DATA.sites, data.with_plantings ? DATA.plant : Promise.resolve(null)])
      if (cancelled) return
      const all = box()
      for (const f of nbGeo.features as { properties: { id: number }; geometry: { coordinates: unknown } }[]) {
        const b = box(); walk(f.geometry.coordinates, b); walk(f.geometry.coordinates, all)
        bounds.current[String(f.properties.id)] = b
      }

      const build = async () => {
        const mm = m!
        mm.setLight({ anchor: 'map', position: [1.2, 200, 35], intensity: 0.38, color: '#ffffff' })
        mm.addSource('nb', { type: 'geojson', data: nbGeo, promoteId: 'id' })
        mm.addSource('sites', { type: 'geojson', data: { type: 'FeatureCollection', features: sites.map((s: [string, string, number, number, number | null]) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [s[3], s[2]] }, properties: { t: s[0], name: s[1], canopy: s[4] ?? 100 } })) } })

        // Hairline seams between areas, on the ground (visible where an area stays flat).
        mm.addLayer({ id: 'nb-seam', type: 'line', source: 'nb', paint: { 'line-color': 'rgba(255,255,255,0.06)', 'line-width': 0.6 } })
        mm.addLayer({
          id: 'nb-3d', type: 'fill-extrusion', source: 'nb',
          paint: {
            'fill-extrusion-color': ['to-color', ['coalesce', ['feature-state', 'c'], css(NONE)]],
            'fill-extrusion-height': H(FS_H),
            'fill-extrusion-opacity': ['interpolate', ['linear'], ['zoom'], 12.5, 0.94, 14.5, 0.38],
            'fill-extrusion-vertical-gradient': true,
          },
        })
        // Compare, by need: a lighter mint roof on every projected extrusion.
        mm.addLayer({ id: 'nb-cap', type: 'fill-extrusion', source: 'nb', filter: idIn([]), paint: { ...capOf(6), 'fill-extrusion-color': css(lighten(C.cool, 0.3)), 'fill-extrusion-opacity': 0.9 } })
        // The areas that hurt most: their roof breathes softly until the user acts there.
        mm.addLayer({ id: 'nb-hot', type: 'fill-extrusion', source: 'nb', filter: idIn([]), paint: { ...capOf(4), 'fill-extrusion-color': css(lighten(C.need, 0.32)), 'fill-extrusion-opacity': 0.3 } })
        // Hover and selection: a faint sheen on the roof.
        mm.addLayer({ id: 'nb-hl', type: 'fill-extrusion', source: 'nb', filter: idIn([]), paint: { ...capOf(5), 'fill-extrusion-color': '#ffffff', 'fill-extrusion-opacity': 0.16 } })

        if (pts) {
          mm.addSource('plant', { type: 'geojson', data: { type: 'FeatureCollection', features: (pts as [number, number, number][]).map(c => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [c[0], c[1]] }, properties: { y: c[2] } })) } })
          mm.addLayer({ id: 'plant-glow', type: 'circle', source: 'plant', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 11, 2.2, 16, 7], 'circle-color': css(C.cool), 'circle-opacity': ['interpolate', ['linear'], ['zoom'], 11, 0.08, 16, 0.16], 'circle-blur': 1 } })
          mm.addLayer({ id: 'plant', type: 'circle', source: 'plant', paint: TREE_DOT(css(lighten(C.cool, 0.45))) })
        }
        mm.addLayer({
          id: 'sites', type: 'circle', source: 'sites', minzoom: 13,
          paint: {
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 13, 1.8, 17, 4],
            'circle-color': '#f2f5f7', 'circle-stroke-color': css(C.need), 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 13, 1, 17, 1.6],
            'circle-opacity': ['interpolate', ['linear'], ['zoom'], 13, 0, 13.4, 1], 'circle-stroke-opacity': ['interpolate', ['linear'], ['zoom'], 13, 0, 13.4, 1],
          },
        })
        // Existing tree canopy (satellite, trees >= 3 m), under the buildings, once you zoom into an area.
        try {
          const cj = await fetch('/data/canopy.json').then(r => r.json())
          mm.addSource('canopy', { type: 'image', url: '/data/canopy.png', coordinates: cj.coordinates })
          mm.addLayer({ id: 'canopy', type: 'raster', source: 'canopy', minzoom: 13, paint: { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], 13, 0, 14.5, 0.9], 'raster-resampling': 'nearest' } })
        } catch { /* no canopy image: the map still works */ }
        addCity(mm)
        mm.addLayer({ id: 'nb-mask', type: 'fill', source: 'nb', filter: NOTHING, paint: { 'fill-color': css(C.bg), 'fill-opacity': 0.78 } })
        mm.addLayer({ id: 'nb-focus', type: 'line', source: 'nb', filter: NOTHING, paint: { 'line-color': '#ffffff', 'line-width': 2.2, 'line-opacity': 0.9 } })
        const [spotsData, roofsData] = await Promise.all([DATA.spots, DATA.roofs])
        const spotFeats: { type: "Feature"; geometry: { type: "Point"; coordinates: [number, number] }; properties: { nb: string; i: number } }[] = []
        for (const [nb, pts] of Object.entries(spotsData as Record<string, [number, number][]>)) pts.forEach((c, i) => spotFeats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: c }, properties: { nb, i } }))
        mm.addSource('spots', { type: 'geojson', data: { type: 'FeatureCollection', features: spotFeats } })
        mm.addSource('roofs', { type: 'geojson', data: roofsData as never })
        mm.addLayer({ id: 'roof-cand', type: 'line', source: 'roofs', filter: NOTHING, paint: { 'line-color': 'rgb(140,185,240)', 'line-width': 1.6, 'line-dasharray': [2, 1.5] } })
        mm.addLayer({ id: 'roof-green', type: 'fill', source: 'roofs', filter: NOTHING, paint: { 'fill-color': '#5fbf5a', 'fill-opacity': 0.9 } })
        mm.addLayer({ id: 'spot-cand', type: 'circle', source: 'spots', filter: NOTHING, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 14, 1.6, 18, 5], 'circle-color': 'rgba(52,224,161,0)', 'circle-stroke-color': 'rgba(52,224,161,0.55)', 'circle-stroke-width': 1 } })
        // Same look as the existing plantings ('plant-glow' + 'plant'): the slider adds trees of the same kind.
        mm.addLayer({ id: 'spot-tree-glow', type: 'circle', source: 'spots', filter: NOTHING, paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 11, 2.2, 16, 7], 'circle-color': css(C.cool), 'circle-opacity': ['interpolate', ['linear'], ['zoom'], 11, 0.08, 16, 0.16], 'circle-blur': 1 } })
        mm.addLayer({ id: 'spot-tree', type: 'circle', source: 'spots', filter: NOTHING, paint: TREE_DOT(css(lighten(C.cool, 0.45))) })
        // Planted trees sit on top of the satellite canopy and the buildings, so they never get lost under them.
        if (mm.getLayer('plant')) { mm.moveLayer('plant-glow'); mm.moveLayer('plant') }
        addLabels(mm)

        const cam = mm.cameraForBounds(toBounds(all), { padding: phone ? 16 : 48 })
        if (cam?.center) {
          home.current = { center: cam.center, zoom: (cam.zoom ?? 12) + (phone ? 0 : 0.35) }
          // Open straight on the final view: no intro flight.
          mm.jumpTo({ ...home.current, pitch: 50, bearing: -15 })
        }

        ready.current = true
        Object.values(pending.current).forEach(fn => fn())
        pending.current = {}

        // Calm pulse: one uniform paint property at ~20 fps, paused when the tab is hidden or nothing is hot.
        if (false as boolean) {
          let last = 0
          const loop = (t: number) => {
            pulseRaf = requestAnimationFrame(loop)
            if (t - last < 50 || document.hidden || !pulseIds.current.length) return
            last = t
            const s = 0.5 - 0.5 * Math.cos((t / 2600) * Math.PI * 2)
            mm.setPaintProperty('nb-hot', 'fill-extrusion-opacity', 0.04 + 0.42 * s)
          }
          pulseRaf = requestAnimationFrame(loop)
        }
      }
      styleReady.then(() => { if (!cancelled) build() })

      m.on('mousemove', 'nb-3d', e => {
        const f = e.features?.[0]
        if (!f) return
        const id = String(f.id)
        if (id !== hoverId.current) { hoverId.current = id; setHl(); popup.setText(String(f.properties.name)) }
        m!.getCanvas().style.cursor = 'pointer'
        popup.setLngLat(e.lngLat).addTo(m!)
      })
      m.on('mouseleave', 'nb-3d', () => {
        hoverId.current = null; setHl()
        m!.getCanvas().style.cursor = ''
        popup.remove()
      })
      m.on('click', e => {
        if (!m!.getLayer('nb-3d')) return
        const f = m!.queryRenderedFeatures(e.point, { layers: ['nb-3d'] })[0]
        onSelectRef.current(f ? String(f.id) : null)
      })
    })()
    return () => { cancelled = true; cancelAnimationFrame(pulseRaf); cancelAnimationFrame(anim.current); m?.remove(); map.current = null; ready.current = false; cells.current = {} }
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  // Colours, heights and points for the current mode, alloc and selection.
  useEffect(() => {
    const run = () => {
      const m = map.current!
      const tab = mode === 'buildings' ? 'buildings' : 'streets'
      m.setFilter('sites', mode === 'layers' ? NOTHING : mode === 'buildings' ? ['!=', ['get', 't'], 'playground'] : ['<', ['get', 'canopy'], 5])
      if (m.getLayer('plant')) {
        const vis = show.planted && (mode !== 'compare' || cmp.side === 'actual')
        const f: ExpressionSpecification | null = mode === 'compare' && cmp.year !== 'all' ? ['==', ['get', 'y'], +cmp.year] : null
        for (const l of ['plant-glow', 'plant']) {
          m.setLayoutProperty(l, 'visibility', vis ? 'visible' : 'none')
          m.setFilter(l, f)
          m.setLayerZoomRange(l, mode === 'compare' ? 0 : 13, 24)
        }
      }
      if (m.getLayer('canopy')) m.setLayoutProperty('canopy', 'visibility', show.canopy ? 'visible' : 'none')
      const next: Record<string, Cell> = {}
      let caps: string[] = []
      let pulse: string[] = []
      const L = mode === 'layers' ? data.layers.find(x => x.id === layer) ?? data.layers[0] : null
      if (L) {
        // Data layer: colour and a gentle height by the value; areas without a value stay dark (never imputed).
        // Rank-based (quantile) position, so the colours spread across the city instead of a few outliers
        // pushing everything to one end. 0 = best, 0.5 = typical, 1 = worst.
        const sorted = Object.values(L.values).sort((a, b) => a - b)
        const q = (v: number) => { let lo = 0, hi = sorted.length; while (lo < hi) { const m = (lo + hi) >> 1; if (sorted[m] < v) lo = m + 1; else hi = m } let e = lo; while (e < sorted.length && sorted[e] === v) e++; return sorted.length > 1 ? ((lo + e - 1) / 2) / (sorted.length - 1) : 0.5 }
        for (const id of ids) {
          const v = L.values[id]
          if (v === undefined) { next[id] = { h: 0, c: NONE }; continue }
          let t = q(v)
          if (L.worse === 'low') t = 1 - t
          const pa = alloc[id] ?? 0
          const green = (c: RGB) => (pa > 0 ? mix(c, C.cool, 0.35 + 0.65 * (pa / 100)) : c)
          if (L.worse === 'none') { next[id] = { h: 8 + 50 * t * t, c: green(seq(t)) }; continue }
          // Only the worse-than-typical half rises.
          next[id] = { h: 8 + 80 * Math.max(0, (t - 0.5) * 2) ** 2, c: green(ramp(t)) }
        }
      } else if (mode === 'compare' && data.compare) {
        const by = data.compare[cmp.year][cmp.side].by
        const need = cmp.side === 'need'
        for (const id of ids) {
          const v = by[id] ?? 0
          next[id] = { h: v ? 22 * Math.sqrt(v) : 0, c: v ? (need ? PROJ : NEUTRAL) : NONE }
        }
        if (need) caps = Object.keys(by).filter(id => by[id] > 0)
      } else {
        const n = data.counts[tab]
        for (const id of ids) {
          const r = data.packages[tab][id]?.rank ?? -1
          const p = alloc[id] ?? 0
          const t = r >= 1 ? 1 - (r - 1) / Math.max(1, n - 1) : 0
          const base = r >= 1 ? ramp(t) : NONE
          // The intervention raises the area and pulls its colour toward --cool in step with the %.
          next[id] = { h: r >= 1 ? 8 + 70 * Math.max(0, (t - 0.5) * 2) ** 2 : 0, c: p > 0 ? mix(base, C.cool, 0.35 + 0.65 * (p / 100)) : base }
        }
        pulse = hot.filter(id => !(alloc[id] > 0))
      }
      if (selected) for (const id of ids) if (id !== selected) next[id] = { ...next[id], c: mix(next[id].c, C.bg, 0.5) }
      m.setFilter('nb-cap', idIn(caps))
      m.setFilter('nb-hot', idIn(pulse))
      pulseIds.current = pulse
      m.setPaintProperty('nb-hot', 'fill-extrusion-opacity', pulse.length ? 0.4 : 0)
      setHl()
      tweenTo(next)
    }
    whenReady('mode', run)
  }, [mode, alloc, hot, cmp.year, cmp.side, data, selected, layer, show.planted, show.canopy]) // eslint-disable-line react-hooks/exhaustive-deps

  // Camera: fly to the selected area, or back to the whole city.
  const firstSel = useRef(true)
  useEffect(() => {
    const run = () => {
      const m = map.current!
      const reduce = reducedMotion()
      const lock = (on: boolean) => {
        for (const h of [m.dragPan, m.scrollZoom, m.boxZoom, m.dragRotate, m.keyboard, m.doubleClickZoom, m.touchZoomRotate, m.touchPitch]) { if (on) h.disable(); else h.enable() }
      }
      if (selected && bounds.current[selected]) {
        const w = m.getContainer().clientWidth
        // Focus mode: top-down, north up, the area fills the map, everything else dimmed, camera locked.
        const cam = m.cameraForBounds(toBounds(bounds.current[selected]), { padding: Math.round(Math.min(40, w * 0.04)), maxZoom: 18, bearing: 0 })
        if (cam?.center) m.easeTo({ center: cam.center, zoom: cam.zoom, pitch: 0, bearing: 0, duration: reduce ? 0 : 650, easing: easeInOut, essential: true })
        lock(true)
      } else {
        lock(false)
        if (!firstSel.current && home.current) m.flyTo({ ...home.current, pitch: 50, bearing: -15, duration: reduce ? 0 : 1000, curve: 1.2, easing: easeInOut, essential: true })
      }
      const notSel: ExpressionSpecification = ['!=', ['to-string', ['get', 'id']], selected ?? '']
      m.setFilter('nb-mask', selected ? notSel : NOTHING)
      m.setFilter('nb-focus', selected ? ['==', ['to-string', ['get', 'id']], selected] : NOTHING)
      firstSel.current = false
    }
    whenReady('sel', run)
  }, [selected])

  // Focus mode in the trees tool: candidate spots faint, planted ones solid; City roofs dashed, greened ones filled.
  useEffect(() => {
    const run = () => {
      const m = map.current!
      if (!m.getLayer('spot-tree')) return
      const on = (mode === 'streets' || mode === 'layers') && !!selected && !!focus
      const inNb: ExpressionSpecification = ['==', ['get', 'nb'], selected ?? '']
      m.setFilter('spot-cand', NOTHING)
      const planted: ExpressionSpecification = on ? ['all', inNb, ['<', ['get', 'i'], focus!.trees]] : NOTHING
      m.setFilter('spot-tree', planted)
      m.setFilter('spot-tree-glow', planted)
      m.setFilter('roof-cand', NOTHING)
      m.setFilter('roof-green', on ? ['all', inNb, ['<=', ['get', 'cum'], (focus!.roof || 0) + 1]] : NOTHING)
    }
    whenReady('focus', run)
  }, [mode, selected, focus?.trees, focus?.roof]) // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={el} className="map map-root" />
}
