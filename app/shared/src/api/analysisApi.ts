import { axisOrder, type Axis } from '../domain/axes'
import { isExperimentCapabilities, isExperimentConfig, type ExperimentConfig, type ExperimentCapabilities } from '../domain/experimentConfig'
import { isLabBuild } from '../domain/experimentConfig'
import { isOrdinalScale, sameContent, type OrdinalScale } from '../domain/ordinalScale'

export type Mode = 'low' | 'medium' | 'high'
export type LabProvider = 'typesafe' | 'maritaca' | 'gemini'
export const modes: Mode[] = ['low', 'medium', 'high']
export const modeLabels: Record<Mode, string> = { low: 'Baixo', medium: 'Médio', high: 'Alto' }
export const modeDescriptions: Record<Mode, string> = { low: 'Análise com JEV', medium: 'JEV com revisão por LLM quando necessária', high: 'Análise diretamente com LLM' }
export const recipients: Record<Mode, string> = { low: 'TypeSafe (JEV)', medium: 'TypeSafe (JEV) e, quando necessário, Maritaca (Sabiá)', high: 'Maritaca (Sabiá)' }
export type EvidenceAudit = {
  chunk_index: number; kind: 'search' | 'semantic'; status: 'found' | 'not_selected' | 'not_literal' | 'sustenta' | 'contradiz' | 'insuficiente' | 'uncertain' | 'failed' | 'invalid';
  level: number; quote?: string | null; sentence_id?: string | null; start?: number | null; end?: number | null;
  confidence?: number | null; existence_probability?: number | null; probabilities?: Record<string, number> | null; model?: string | null
}
export type JevDiagnostic = {
  chunk_index: number; regra_decisao: 'nivel' | 'polo_primeiro'; relevante: boolean;
  nivel_jev_bruto: number | null; nivel: number | null; grupo_mais_provavel: 'A' | 'B' | 'C' | null;
  probabilities_nivel: Record<string, number>; probabilities_abc: { A: number; B: number; C: number };
  margem_grupo: number; probabilidade_nivel_condicional: number | null; confianca_nivel: number
  desempate_intensidade?: boolean
}
export type AxisResult = {
  axis: Axis; pole_a: number | null; pole_b: number | null;
  status: 'estimated' | 'no_evidence' | 'abstained'; coverage: number;
  valid_chunks: number; total_chunks: number; sufficient_evidence: boolean;
  level_counts: { minus4?: number; minus3?: number; minus2: number; minus1: number; zero: number; plus1: number; plus2: number; plus3?: number; plus4?: number };
  ci95: [number, number] | null; methods_used: ('jev' | 'llm')[];
  reason_codes: string[]; evidence: { chunk_index: number; quote: string; verified: true }[]
  evidence_audit?: EvidenceAudit[]
  jev_diagnostics?: JevDiagnostic[]
  level_counts_by_key?: Record<string, number>
}
export type Analysis = {
  schema_version: string; pipeline_version: string; processing_level: Mode;
  models_used: string[]; axes: AxisResult[]; chunks: { index: number; text: string }[];
  logical_calls: { jev: number; llm: number }; warnings: string[];
  effective_config?: ExperimentConfig; config_version?: '1'; config_hash?: string; environment?: 'development' | 'lab' | 'production'; lab_execution_id?: string
  escala?: OrdinalScale; escala_hash?: string
}
export type AnalysisEntry<Id extends number | string = number> = { id: Id; title: string; text: string; analysis: Analysis; mode: Mode; source?: string }
export type Capabilities = { max_chars: number; max_tokens: number; max_chunks: number; modes: Record<Mode, boolean>; timeout_seconds: number;
  analysis_defaults?: ExperimentConfig; model_providers?: Record<string, 'maritaca' | 'gemini'>;
  environment?: 'development' | 'lab' | 'production'; experimental?: ExperimentCapabilities | { enabled: false } }

export function configuredRecipients(mode: Mode, caps: Capabilities | null): string {
  const config = caps?.analysis_defaults
  if (!config) return recipients[mode]
  const llm = caps?.model_providers?.[config.llm_model] === 'gemini' ? 'Google Gemini' : 'Maritaca (Sabiá)'
  if (mode === 'low') return recipients.low
  if (mode === 'medium') return `TypeSafe (JEV) e, quando necessário, ${llm}`
  return config.semantic_evidence_check ? `${llm} e TypeSafe (checagem de evidências)` : llm
}

function object(value: unknown): value is Record<string, unknown> { return !!value && typeof value === 'object' && !Array.isArray(value) }
function strings(value: unknown): value is string[] { return Array.isArray(value) && value.every(item => typeof item === 'string') }
function count(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 }
function positive(value: unknown): value is number { return count(value) && value > 0 }
function score(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100 }
function probability(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 }
function distribution(value: unknown, keys: string[]): boolean {
  return object(value) && Object.keys(value).length === keys.length && keys.every(key => probability(value[key])) && Math.abs(Object.values(value).reduce<number>((sum, p) => sum + Number(p), 0) - 1) < 1e-6
}
function isJevDiagnostic(value: unknown, chunks: Analysis['chunks'], scale: OrdinalScale, rule?: string): value is JevDiagnostic {
  return object(value) && count(value.chunk_index) && chunks.some(c => c.index === value.chunk_index) &&
    ['nivel', 'polo_primeiro'].includes(value.regra_decisao as string) && (!rule || value.regra_decisao === rule) && typeof value.relevante === 'boolean' &&
    [value.nivel, value.nivel_jev_bruto].every(n => n === null || scale.niveis.some(level => level.codigo === n)) &&
    (value.grupo_mais_provavel === null || ['A', 'B', 'C'].includes(value.grupo_mais_provavel as string)) &&
    distribution(value.probabilities_nivel, scale.niveis.map(n => n.chave)) && distribution(value.probabilities_abc, ['A', 'B', 'C']) &&
    probability(value.margem_grupo) && probability(value.confianca_nivel) && (value.probabilidade_nivel_condicional === null || probability(value.probabilidade_nivel_condicional)) &&
    (value.desempate_intensidade === undefined || typeof value.desempate_intensidade === 'boolean')
}
function isEvidenceAudit(value: unknown, chunks: Analysis['chunks'], schemaVersion: string, codes?: number[]): value is EvidenceAudit {
  if (!object(value) || !count(value.chunk_index) || !chunks.some(c => c.index === value.chunk_index) ||
      !['search', 'semantic'].includes(value.kind as string) || !['found', 'not_selected', 'not_literal', 'sustenta', 'contradiz', 'insuficiente', 'uncertain', 'failed', 'invalid'].includes(value.status as string) ||
      !(codes ?? (schemaVersion === '2' ? [-4, -3, -2, -1, 0, 1, 2, 3, 4] : [-2, -1, 0, 1, 2])).includes(value.level as number)) return false
  if (!['confidence', 'existence_probability'].every(key => value[key] == null || (typeof value[key] === 'number' && Number.isFinite(value[key]) && value[key] >= 0 && value[key] <= 1))) return false
  if (!['quote', 'sentence_id', 'model'].every(key => value[key] == null || typeof value[key] === 'string')) return false
  if (!['start', 'end'].every(key => value[key] == null || count(value[key]))) return false
  if (value.probabilities != null && (!object(value.probabilities) || !Object.values(value.probabilities).every(p => typeof p === 'number' && Number.isFinite(p) && p >= 0 && p <= 1))) return false
  if (value.status === 'found') {
    const text = Array.from(chunks.find(c => c.index === value.chunk_index)!.text)
    return value.kind === 'search' && typeof value.sentence_id === 'string' && count(value.start) && count(value.end) && value.start < value.end && value.end <= text.length && text.slice(value.start, value.end).join('') === value.quote
  }
  return true
}
export function isCapabilities(value: unknown): value is Capabilities {
  if (!object(value) || !object(value.modes)) return false
  const available = value.modes
  if (value.analysis_defaults !== undefined && !isExperimentConfig(value.analysis_defaults)) return false
  if (value.model_providers !== undefined && (!object(value.model_providers) || !Object.values(value.model_providers).every(provider => provider === 'maritaca' || provider === 'gemini'))) return false
  if (value.environment !== undefined && !['development', 'lab', 'production'].includes(value.environment as string)) return false
  if (value.experimental !== undefined && (!object(value.experimental) ||
    (value.experimental.enabled !== false && !(value.environment === 'lab' && isExperimentCapabilities(value.experimental))))) return false
  return positive(value.max_chars) && positive(value.max_tokens) && positive(value.max_chunks) &&
    typeof value.timeout_seconds === 'number' && Number.isFinite(value.timeout_seconds) && value.timeout_seconds > 0 &&
    modes.every(mode => typeof available[mode] === 'boolean')
}
export function isAnalysis(value: unknown): value is Analysis {
  if (object(value) && value.lab_execution_id !== undefined && (typeof value.lab_execution_id !== 'string' || !/^[a-f0-9-]{36}$/.test(value.lab_execution_id))) return false
  if (object(value) && ['effective_config', 'config_version', 'config_hash', 'environment'].some(name => name in value) &&
    (!isExperimentConfig(value.effective_config) || value.config_version !== '1' || typeof value.config_hash !== 'string' || !/^[a-f0-9]{64}$/.test(value.config_hash) || !['development', 'lab', 'production'].includes(value.environment as string))) return false
  if (!object(value) || !['1', '2', '3'].includes(value.schema_version as string) || typeof value.pipeline_version !== 'string' ||
    !modes.includes(value.processing_level as Mode) || !strings(value.models_used) || !strings(value.warnings) ||
    !object(value.logical_calls) || !count(value.logical_calls.jev) || !count(value.logical_calls.llm) ||
    !Array.isArray(value.chunks) || !value.chunks.every(chunk => object(chunk) && count(chunk.index) && typeof chunk.text === 'string') ||
    !Array.isArray(value.axes) || value.axes.length !== 4) return false
  const chunks = value.chunks
  const axes = value.axes
  const scale = isOrdinalScale(value.escala) ? value.escala : undefined
  if (value.schema_version !== '3' && (value.escala !== undefined || value.escala_hash !== undefined)) return false
  if (value.schema_version === '3' && (!scale || typeof value.escala_hash !== 'string' || !/^[a-f0-9]{64}$/.test(value.escala_hash) || (isExperimentConfig(value.effective_config) && !sameContent(value.effective_config.escala, scale)))) return false
  return axisOrder.every(axis => axes.filter(item => object(item) && item.axis === axis).length === 1) && axes.every(item => {
    if (object(item) && item.jev_diagnostics !== undefined && (!scale || !Array.isArray(item.jev_diagnostics) || !item.jev_diagnostics.every(d => isJevDiagnostic(d, chunks, scale, (value.effective_config as ExperimentConfig | undefined)?.regra_decisao)))) return false
    if (object(item) && item.evidence_audit !== undefined && (!Array.isArray(item.evidence_audit) || !item.evidence_audit.every(audit => isEvidenceAudit(audit, chunks, value.schema_version as string, scale?.niveis.map(n => n.codigo))))) return false
    if (!object(item) || !['estimated', 'no_evidence', 'abstained'].includes(item.status as string) ||
      !count(item.valid_chunks) || !count(item.total_chunks) || item.valid_chunks > item.total_chunks ||
      typeof item.coverage !== 'number' || !Number.isFinite(item.coverage) || item.coverage < 0 || item.coverage > 1 ||
      typeof item.sufficient_evidence !== 'boolean' || !object(item.level_counts) || !strings(item.reason_codes) ||
      !Array.isArray(item.methods_used) || !item.methods_used.every(method => ['jev', 'llm'].includes(method))) return false
    const levels = item.level_counts
    if (value.schema_version === '3') {
      const counts = item.level_counts_by_key
      if (!object(counts) || Object.keys(counts).length !== scale!.niveis.length || !scale!.niveis.every(n => count(counts[n.chave])) || Object.values(counts).reduce<number>((sum, c) => sum + Number(c), 0) !== item.valid_chunks) return false
    }
    if (value.schema_version === '2' && !['minus4', 'minus3', 'plus3', 'plus4'].every(key => count(levels[key]))) return false
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

export type LabSessionStorage = {
  getItem: (key: string) => string | null | Promise<string | null>
  setItem: (key: string, value: string) => void | Promise<void>
  removeItem: (key: string) => void | Promise<void>
}

export function createAnalysisClient(baseUrl = '', fetcher: typeof fetch = (...args) => fetch(...args), labClient: 'web' | 'extension' = 'web', sessionStore?: LabSessionStorage) {
  const base = baseUrl.replace(/\/$/, '')
  const sessionKey = `8values-lab-key-session-v1:${base || 'same-origin'}`
  let memoryToken = ''
  async function token() { try { return await (sessionStore ?? sessionStorage).getItem(sessionKey) ?? '' } catch { return memoryToken } }
  async function setToken(value: string) {
    memoryToken = value
    try {
      const storage = sessionStore ?? sessionStorage
      if (value) await storage.setItem(sessionKey, value)
      else await storage.removeItem(sessionKey)
    } catch {
      if (sessionStore) throw new Error('Não foi possível guardar a sessão de chaves na extensão. Tente novamente antes de fechar o painel.')
    }
  }
  async function headers() { const value = await token(); return { ...(value ? { 'X-Lab-Session': value } : {}), ...(isLabBuild ? { 'X-Lab-Client': labClient } : {}) } }
  async function updateKey(provider: LabProvider, apiKey?: string) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 10000)
    try {
      const response = await fetcher(`${base}/api/lab/api-keys${apiKey === undefined ? `/${provider}` : ''}`, {
        method: apiKey === undefined ? 'DELETE' : 'POST', headers: { ...await headers(), 'Content-Type': 'application/json' },
        body: apiKey === undefined ? undefined : JSON.stringify({ provider, api_key: apiKey }), signal: controller.signal, cache: 'no-store', credentials: 'omit',
      })
      if (response.status === 401) { await setToken(''); throw new Error('Sessão expirada. Tente cadastrar a chave novamente.') }
      if (!response.ok) throw new Error('Não foi possível atualizar a chave. Confira o formato e a conexão com a API Lab.')
      const data = await response.json()
      if (typeof data.session_token !== 'string' || !/^[A-Za-z0-9_-]{40,100}$/.test(data.session_token)) throw new Error('Resposta inválida da API Lab.')
      await setToken(data.session_token)
    } finally { clearTimeout(timer) }
  }
  return {
    saveLabKey: (provider: LabProvider, apiKey: string) => updateKey(provider, apiKey),
    removeLabKey: (provider: LabProvider) => updateKey(provider),
    async clearLabSession() {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 10000)
      try {
        const response = await fetcher(`${base}/api/lab/session`, { method: 'DELETE', headers: await headers(), cache: 'no-store', credentials: 'omit', signal: controller.signal })
        if (!response.ok) throw new Error('Não foi possível encerrar a sessão de chaves.')
        await setToken('')
      } finally { clearTimeout(timer) }
    },
    async getCapabilities(signal?: AbortSignal): Promise<Capabilities> {
      const controller = new AbortController()
      const abort = () => controller.abort()
      signal?.addEventListener('abort', abort, { once: true })
      if (signal?.aborted) abort()
      const timer = setTimeout(abort, 10000)
      try {
        let response = await fetcher(`${base}/api/capabilities`, { headers: await headers(), cache: 'no-store', credentials: 'omit', signal: controller.signal })
        if (response.status === 401 && await token()) { await setToken(''); response = await fetcher(`${base}/api/capabilities`, { headers: await headers(), cache: 'no-store', credentials: 'omit', signal: controller.signal }) }
        if (!response.ok) throw new Error('Não foi possível consultar a API.')
        const data: unknown = await response.json()
        if (!isCapabilities(data)) throw new Error('A API retornou capacidades inválidas.')
        return data
      } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort) }
    },
    async analyze(text: string, processingLevel: Mode, signal: AbortSignal, timeoutSeconds = 120, experimentConfig?: ExperimentConfig): Promise<Analysis> {
      const controller = new AbortController()
      let timedOut = false
      const abort = () => controller.abort()
      signal.addEventListener('abort', abort, { once: true })
      if (signal.aborted) abort()
      const timer = setTimeout(() => { timedOut = true; controller.abort() }, (timeoutSeconds + 15) * 1000)
      try {
        const response = await fetcher(`${base}/api/analyze`, {
          method: 'POST', headers: { 'Content-Type': 'application/json', ...await headers() }, credentials: 'omit', cache: 'no-store',
          body: JSON.stringify({ text, processing_level: processingLevel, ...(experimentConfig ? { experiment_config: experimentConfig } : {}) }), signal: controller.signal,
        })
        if (!response.ok) {
          if (response.status === 401) { await setToken(''); throw new Error('Sessão de chaves expirada. Atualize a conexão e cadastre novamente na aba API keys.') }
          const messages: Record<number, string> = { 403: 'Configuração experimental indisponível nesta API. Atualize a conexão.', 413: 'Texto acima do limite. No Lab, aumente os tokens por trecho ou reduza o texto.', 422: 'Entrada ou configuração inválida. Atualize a conexão e confira os parâmetros.', 429: 'Limite de uso atingido. Tente mais tarde.', 503: 'Modo indisponível no servidor.', 504: 'A análise excedeu o tempo disponível.' }
          throw new Error(messages[response.status] ?? 'Falha na análise. Tente novamente.')
        }
        const data: unknown = await response.json()
        if (!isAnalysis(data) || data.processing_level !== processingLevel) throw new Error('A API retornou uma análise inválida.')
        if (experimentConfig && (data.environment !== 'lab' || !data.effective_config || Object.keys(experimentConfig).some(name => !sameContent(data.effective_config![name as keyof ExperimentConfig], experimentConfig[name as keyof ExperimentConfig])))) throw new Error('A API não confirmou a configuração experimental utilizada.')
        return data
      } catch (err) {
        if (timedOut) throw new AnalysisTimeoutError()
        throw err
      } finally { clearTimeout(timer); signal.removeEventListener('abort', abort) }
    },
  }
}
