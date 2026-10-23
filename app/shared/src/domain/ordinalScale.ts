export type ScaleLevel = { chave: string; codigo: number; rotulo: string; polo: 'A' | 'B' | null; valor: number }
export type OrdinalScale = { id: string; versao: number; niveis: ScaleLevel[]; rubricas_por_eixo: Record<string, Record<string, { situacao: string; exemplos: string[] }>> }
const axes = ['economic', 'diplomatic', 'state', 'society']
function object(value: unknown): value is Record<string, unknown> { return !!value && typeof value === 'object' && !Array.isArray(value) }
function text(value: unknown): value is string { return typeof value === 'string' && !!value.trim() }
function keys(value: Record<string, unknown>, expected: string[]) { return Object.keys(value).sort().join(',') === [...expected].sort().join(',') }

export function isOrdinalScale(value: unknown): value is OrdinalScale {
  if (!object(value) || !keys(value, ['id', 'versao', 'niveis', 'rubricas_por_eixo']) || !text(value.id) || !Number.isSafeInteger(value.versao) || Number(value.versao) < 1 || !Array.isArray(value.niveis) || value.niveis.length < 3 || value.niveis.length % 2 !== 1 || !object(value.rubricas_por_eixo) || !keys(value.rubricas_por_eixo, axes)) return false
  const levels = value.niveis
  const center = Math.floor(levels.length / 2)
  if (!levels.every((n, i) => object(n) && keys(n, ['chave', 'codigo', 'rotulo', 'polo', 'valor']) && text(n.chave) && text(n.rotulo) && Number.isSafeInteger(n.codigo) && typeof n.valor === 'number' && Number.isFinite(n.valor) && n.valor >= 0 && n.valor <= 1 && n.polo === (i < center ? 'B' : i === center ? null : 'A'))) return false
  const typed = levels as ScaleLevel[]
  if (new Set(typed.map(n => n.chave)).size !== levels.length || new Set(typed.map(n => n.codigo)).size !== levels.length || typed[0].valor !== 0 || typed[center].valor !== .5 || typed.at(-1)!.valor !== 1 || typed.some((n, i) => i > 0 && typed[i - 1].valor >= n.valor)) return false
  return axes.every(axis => {
    const rubric = (value.rubricas_por_eixo as Record<string, unknown>)[axis]
    return object(rubric) && keys(rubric, typed.map(n => n.chave)) && Object.values(rubric).every(a => object(a) && keys(a, ['situacao', 'exemplos']) && text(a.situacao) && Array.isArray(a.exemplos) && a.exemplos.length > 0 && a.exemplos.every(text))
  })
}

export function sameContent(a: unknown, b: unknown): boolean {
  const canonical = (v: unknown): unknown => Array.isArray(v) ? v.map(canonical) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)).map(([k, x]) => [k, canonical(x)])) : v
  return JSON.stringify(canonical(a)) === JSON.stringify(canonical(b))
}

export function historicalLevels(version: string): ScaleLevel[] {
  const extent = version === '1' ? 2 : 4
  return Array.from({ length: 2 * extent + 1 }, (_, i) => ({ chave: i < extent ? `minus${extent - i}` : i === extent ? 'zero' : `plus${i - extent}`, codigo: i - extent, polo: i < extent ? 'B' : i === extent ? null : 'A', rotulo: `${i - extent}`, valor: i / (2 * extent) }))
}
