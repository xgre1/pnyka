/* Panel primitives  Radix for behaviour and accessibility, styles in src/index.css. */
import type { ReactNode } from 'react'
import * as RSlider from '@radix-ui/react-slider'
import * as RToggle from '@radix-ui/react-toggle-group'
import * as RCollapsible from '@radix-ui/react-collapsible'
import { ChevronDown } from 'lucide-react'

/** An Apple-style continuous control: thin track, mint fill, white thumb. */
export function Slider({ value, onChange, label, step = 5, min = 0, max = 100 }: { value: number; onChange: (v: number) => void; label: string; step?: number; min?: number; max?: number }) {
  return (
    <RSlider.Root className="ui-slider" value={[value]} min={min} max={max} step={step} onValueChange={v => onChange(v[0])}>
      <RSlider.Track className="ui-slider-track"><RSlider.Range className="ui-slider-range" /></RSlider.Track>
      <RSlider.Thumb className="ui-slider-thumb" aria-label={label} />
    </RSlider.Root>
  )
}

/** iOS segmented control. */
export function Segmented<T extends string>({ value, onChange, options, label }: { value: T; onChange: (v: T) => void; options: { value: T; label: ReactNode }[]; label: string }) {
  const i = Math.max(0, options.findIndex(o => o.value === value))
  return (
    <RToggle.Root type="single" className="ui-seg" value={value} onValueChange={v => { if (v) onChange(v as T) }} aria-label={label}
      style={{ ['--n' as string]: options.length, ['--i' as string]: i }}>
      <span className="ui-seg-thumb" aria-hidden />
      {options.map(o => <RToggle.Item key={o.value} value={o.value} className="ui-seg-item">{o.label}</RToggle.Item>)}
    </RToggle.Root>
  )
}

/** One quiet disclosure, e.g. "Πηγές". */
export function Disclosure({ label, children }: { label: string; children: ReactNode }) {
  return (
    <RCollapsible.Root className="ui-disc">
      <RCollapsible.Trigger className="ui-disc-trigger">{label}<ChevronDown size={16} aria-hidden /></RCollapsible.Trigger>
      <RCollapsible.Content className="ui-disc-content">{children}</RCollapsible.Content>
    </RCollapsible.Root>
  )
}

/** The single legend line: solid = today, dashed mint = if the intervention happens. */
export function Legend({ now, then, ramp }: { now: string; then: string; ramp?: boolean }) {
  return (
    <p className="ui-legend">
      <span><i className={ramp ? 'sw ramp' : 'sw now'} aria-hidden />{now}</span>
      <span><i className="sw proj" aria-hidden />{then}</span>
    </p>
  )
}


/** Segmented slider: one track split into stages (trees, roofs, facades). Each stage fills in its own colour. */
export function StageSlider({ value, onChange, label, stages, toggles = [], onToggle }: {
  value: number; onChange: (v: number) => void; label: string
  stages: { from: number; to: number; tone: string; icon: ReactNode; name: string }[]
  toggles?: { key: string; on: boolean; tone: string; icon: ReactNode; name: string }[]
  onToggle?: (key: string) => void
}) {
  return (
    <div className="stage-slider">
      <RSlider.Root className="ss-root" value={[value]} min={0} max={100} step={1} onValueChange={v => onChange(v[0])}>
        <RSlider.Track className="ss-track">
          {stages.map(s => {
            const fill = Math.max(0, Math.min(1, (value - s.from) / Math.max(1, s.to - s.from)))
            return (
              <span key={s.name} className={`ss-seg ${s.tone}`} style={{ left: `${s.from}%`, width: `${s.to - s.from}%` }}>
                <i style={{ width: `${fill * 100}%` }} />
              </span>
            )
          })}
        </RSlider.Track>
        <RSlider.Thumb className="ss-thumb" aria-label={label} />
      </RSlider.Root>
      <div className="ss-legend">
        {toggles.map(t => (
          <button key={t.key} type="button" className={`ss-tog ${t.tone} ${t.on ? 'on' : 'off'}`} aria-pressed={t.on} onClick={() => onToggle?.(t.key)} title={`${t.name}: ${t.on ? 'πάτα για να βγει από το σχέδιο' : 'πάτα για να μπει στο σχέδιο'}`}>
            {t.icon}
          </button>
        ))}
      </div>
    </div>
  )
}

/** Share of an area under tree shade, as a ring that fills toward `max` (e.g. the 30% target). */
export function ShadeDonut({ value, max = 100 }: { value: number; max?: number }) {
  const r = 17, c = 2 * Math.PI * r
  const f = Math.max(0, Math.min(1, value / max))
  return (
    <svg width="44" height="44" viewBox="0 0 44 44" className="donut" aria-hidden>
      <circle cx="22" cy="22" r={r} className="d-bg" />
      <circle cx="22" cy="22" r={r} className="d-val" strokeDasharray={`${f * c} ${c}`} transform="rotate(-90 22 22)" />
    </svg>
  )
}
