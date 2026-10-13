import { axisOrder, type Axis } from '../domain/axes'

export type Mode = 'low' | 'medium' | 'high'
export const modes: Mode[] = ['low', 'medium', 'high']
export const modeLabels: Record<Mode, string> = { low: 'Baixo', medium: 'Médio', high: 'Alto' }
export const modeDescriptions: Record<Mode, string> = { low: 'Análise com JEV', medium: 'JEV com revisão por LLM quando necessária', high: 'Análise diretamente com LLM' }
export const recipients: Record<Mode, string> = { low: 'TypeSafe (JEV)', medium: 'TypeSafe (JEV) e, quando necessário, Maritaca (Sabiá)', high: 'Maritaca (Sabiá)' }
export type AxisResult = {
  axis: Axis; pole_a: number | null; pole_b: number | null;
  status: 'estimated' | 'no_evidence' | 'abstained'; coverage: number;
  valid_chunks: number; total_chunks: number; sufficient_evidence: boolean;
  level_counts: { minus2: number; minus1: number; zero: number; plus1: number; plus2: number };
  ci95: [number, number] | null; methods_used: ('jev' | 'llm')[];
  reason_codes: string[]; evidence: { chunk_index: number; quote: string; verified: true }[]
}
export type Analysis = {
  schema_version: string; pipeline_version: string; processing_level: Mode;
  models_used: string[]; axes: AxisResult[]; chunks: { index: number; text: string }[];
  logical_calls: { jev: number; llm: number }; warnings: string[]
}
export type AnalysisEntry<Id extends number | string = number> = { id: Id; title: string; text: string; analysis: Analysis; mode: Mode; source?: string }
export type Capabilities = { max_chars: number; max_tokens: number; max_chunks: number; modes: Record<Mode, boolean>; timeout_seconds: number }

function object(value: unknown): value is Record<string, unknown> { return !!value && typeof value === 'object' && !Array.isArray(value) }
function strings(value: unknown): value is string[] { return Array.isArray(value) && value.every(item => typeof item === 'string') }
function count(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 }
function positive(value: unknown): value is number { return count(value) && value > 0 }
function score(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100 }
export function isCapabilities(value: unknown): value is Capabilities {
  if (!object(value) || !object(value.modes)) return false
  const available = value.modes
  return positive(value.max_chars) && positive(value.max_tokens) && positive(value.max_chunks) &&
    typeof value.timeout_seconds === 'number' && Number.isFinite(value.timeout_seconds) && value.timeout_seconds > 0 &&
    modes.every(mode => typeof available[mode] === 'boolean')
}
export function isAnalysis(value: unknown): value is Analysis {
  if (!object(value) || value.schema_version !== '1' || typeof value.pipeline_version !== 'string' ||
    !modes.includes(value.processing_level as Mode) || !strings(value.models_used) || !strings(value.warnings) ||
    !object(value.logical_calls) || !count(value.logical_calls.jev) || !count(value.logical_calls.llm) ||
    !Array.isArray(value.chunks) || !value.chunks.every(chunk => object(chunk) && count(chunk.index) && typeof chunk.text === 'string') ||
    !Array.isArray(value.axes) || value.axes.length !== 4) return false
  const chunks = value.chunks
  const axes = value.axes
  return axisOrder.every(axis => axes.filter(item => object(item) && item.axis === axis).length === 1) && axes.every(item => {
    if (!object(item) || !['estimated', 'no_evidence', 'abstained'].includes(item.status as string) ||
      !count(item.valid_chunks) || !count(item.total_chunks) || item.valid_chunks > item.total_chunks ||
      typeof item.coverage !== 'number' || !Number.isFinite(item.coverage) || item.coverage < 0 || item.coverage > 1 ||
      typeof item.sufficient_evidence !== 'boolean' || !object(item.level_counts) || !strings(item.reason_codes) ||
      !Array.isArray(item.methods_used) || !item.methods_used.every(method => ['jev', 'llm'].includes(method))) return false
    const levels = item.level_counts
    if (!['minus2', 'minus1', 'zero', 'plus1', 'plus2'].every(key => count(levels[key])) ||
      !Array.isArray(item.evidence) || !item.evidence.every(ev => object(ev) && count(ev.chunk_index) &&
        typeof ev.quote === 'string' && ev.quote.trim() && ev.verified === true &&
        chunks.some(chunk => chunk.index === ev.chunk_index))) return false
    if (item.status === 'estimated' ? !score(item.pole_a) || !score(item.pole_b) || Math.abs((item.pole_a as number) + (item.pole_b as number) - 100) > 0.01 : item.pole_a !== null || item.pole_b !== null) return false
    return item.ci95 === null || (Array.isArray(item.ci95) && item.ci95.length === 2 && item.ci95.every(score) && item.ci95[0] <= item.ci95[1])
  })
}

export class AnalysisTimeoutError extends Error {
  constructor() { super('A análise excedeu o tempo de espera. O texto foi preservado.'); this.name = 'AnalysisTimeoutError' }
}

export function createAnalysisClient(baseUrl = '', fetcher: typeof fetch = (...args) => fetch(...args)) {
  const base = baseUrl.replace(/\/$/, '')
  return {
    async getCapabilities(signal?: AbortSignal): Promise<Capabilities> {
      const controller = new AbortController()
      const abort = () => controller.abort()
      signal?.addEventListener('abort', abort, { once: true })
      if (signal?.aborted) abort()
      const timer = setTimeout(abort, 10000)
      try {
        const response = await fetcher(`${base}/api/capabilities`, { cache: 'no-store', credentials: 'omit', signal: controller.signal })
        if (!response.ok) throw new Error('Não foi possível consultar a API.')
        const data: unknown = await response.json()
        if (!isCapabilities(data)) throw new Error('A API retornou capacidades inválidas.')
        return data
      } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort) }
    },
    async analyze(text: string, processingLevel: Mode, signal: AbortSignal, timeoutSeconds = 120): Promise<Analysis> {
      const controller = new AbortController()
      let timedOut = false
      const abort = () => controller.abort()
      signal.addEventListener('abort', abort, { once: true })
      if (signal.aborted) abort()
      const timer = setTimeout(() => { timedOut = true; controller.abort() }, (timeoutSeconds + 15) * 1000)
      try {
        const response = await fetcher(`${base}/api/analyze`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'omit', cache: 'no-store',
          body: JSON.stringify({ text, processing_level: processingLevel }), signal: controller.signal,
        })
        if (!response.ok) {
          const messages: Record<number, string> = { 413: 'Texto acima do limite.', 422: 'Entrada inválida.', 429: 'Limite de uso atingido. Tente mais tarde.', 503: 'Modo indisponível no servidor.', 504: 'A análise excedeu o tempo disponível.' }
          throw new Error(messages[response.status] ?? 'Falha na análise. Tente novamente.')
        }
        const data: unknown = await response.json()
        if (!isAnalysis(data) || data.processing_level !== processingLevel) throw new Error('A API retornou uma análise inválida.')
        return data
      } catch (err) {
        if (timedOut) throw new AnalysisTimeoutError()
        throw err
      } finally { clearTimeout(timer); signal.removeEventListener('abort', abort) }
    },
  }
}
