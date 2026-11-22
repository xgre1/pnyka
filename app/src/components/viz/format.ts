// Number formatting for the viz components. Greek locale throughout.

export const num = (n: number, digits = 0) =>
  n.toLocaleString('el-GR', { maximumFractionDigits: digits, minimumFractionDigits: 0 })

/** Estimates of people: to the hundred above 1.000, to the ten below. */
export const roundPeople = (n: number) => {
  const step = n >= 1000 ? 100 : 10
  return Math.round(n / step) * step
}

/** Euros written the way people say them: "56k €", "1,25M €". */
export const euro = (n: number, digits = 2) => {
  if (n >= 1e6) return `${num(n / 1e6, digits)}M €`
  if (n < 1000) return `${num(Math.round(n))} €`
  return `${num(Math.round(n / 1000))}k €`
}

/** m²: to the ten above 1.000. */
export const area = (m2: number) => num(m2 >= 1000 ? Math.round(m2 / 10) * 10 : Math.round(m2))

export const clamp = (v: number, lo = 0, hi = 100) => Math.min(hi, Math.max(lo, v))

/** Position of v on a 0..max scale, in % (safe for max = 0). */
export const pos = (v: number, max: number) => (max > 0 ? clamp((v / max) * 100) : 0)
