import { isOrdinalScale, type OrdinalScale } from './ordinalScale'
declare const __APP_VARIANT__: string
export const isLabBuild = typeof __APP_VARIANT__ !== 'undefined' && __APP_VARIANT__ === 'lab'
export const storagePrefix = isLabBuild ? '8values-lab' : '8values'

export const numericFields = ['chunk_tokens', 'relevance_margin_min', 'level_confidence_min', 'direction_margin_min', 'min_valid_chunks', 'bootstrap_samples', 'bootstrap_seed'] as const
export type NumericField = typeof numericFields[number]
export const evidenceDefaults = { semantic_evidence_check: false, jev_evidence_search: false, evidence_existence_min: 0.7 }
export const evidenceFields = ['semantic_evidence_check', 'jev_evidence_search', 'evidence_existence_min'] as const
export type ExperimentConfig = Record<NumericField, number> & { jev_model: string; llm_model: string; escala?: OrdinalScale; primitiva_polaridade?: 'score' | 'choice'; regra_decisao?: 'nivel' | 'polo_primeiro'; chunk_strategy?: 'sentencas' | 'tokens' } & Partial<typeof evidenceDefaults>
export type ConfigRange = { min: number; max: number; step: number }
export type ExperimentCapabilities = {
  enabled: true; config_version: '1'; defaults: ExperimentConfig;
  ranges: Record<NumericField, ConfigRange>; allowed_models: { jev: string[]; llm: string[] };
  providers: { typesafe: boolean; maritaca: boolean }
    & { gemini?: boolean };
  model_providers?: Record<string, 'maritaca' | 'gemini'>; execution_storage?: boolean
  scales?: OrdinalScale[]
}
const fields = [...numericFields, 'jev_model', 'llm_model']
export const configLabels: Record<keyof ExperimentConfig, string> = {
  chunk_strategy: 'Estratégia de segmentação',
  escala: 'Escala ordinal',
  primitiva_polaridade: 'Classificação da polaridade no JEV',
  regra_decisao: 'Regra de decisão do JEV',
  semantic_evidence_check: 'Verificar apoio semântico da citação', jev_evidence_search: 'Buscar citações do JEV por ID', evidence_existence_min: 'Limiar de existência de evidência',
  chunk_tokens: 'Tokens por trecho', relevance_margin_min: 'Margem mínima de relevância',
  level_confidence_min: 'Confiança mínima do nível', direction_margin_min: 'Margem mínima de direção',
  min_valid_chunks: 'Trechos para evidência suficiente', bootstrap_samples: 'Reamostragens do intervalo',
  bootstrap_seed: 'Semente da reamostragem', jev_model: 'Modelo JEV', llm_model: 'Modelo LLM',
}
function object(value: unknown): value is Record<string, unknown> { return !!value && typeof value === 'object' && !Array.isArray(value) }
export function isExperimentConfig(value: unknown): value is ExperimentConfig {
  if (!object(value) || Object.keys(value).some(name => ![...fields, ...evidenceFields, 'escala', 'primitiva_polaridade', 'regra_decisao', 'chunk_strategy'].includes(name)) || fields.some(name => !(name in value))) return false
  if (value.chunk_strategy !== undefined && !['sentencas', 'tokens'].includes(value.chunk_strategy as string)) return false
  if (value.primitiva_polaridade !== undefined && !['score', 'choice'].includes(value.primitiva_polaridade as string)) return false
  if (value.regra_decisao !== undefined && !['nivel', 'polo_primeiro'].includes(value.regra_decisao as string)) return false
  if (value.escala !== undefined && !isOrdinalScale(value.escala)) return false
  if (!numericFields.every(name => typeof value[name] === 'number' && Number.isFinite(value[name]))) return false
  if (['semantic_evidence_check', 'jev_evidence_search'].some(name => value[name] !== undefined && typeof value[name] !== 'boolean')) return false
  if (value.evidence_existence_min !== undefined && (typeof value.evidence_existence_min !== 'number' || !Number.isFinite(value.evidence_existence_min) || value.evidence_existence_min < 0 || value.evidence_existence_min > 1)) return false
  const config = value as ExperimentConfig
  return Number.isSafeInteger(config.chunk_tokens) && config.chunk_tokens >= 100 && config.chunk_tokens <= 2000 &&
    ['relevance_margin_min', 'level_confidence_min', 'direction_margin_min'].every(name => Number(value[name]) >= 0 && Number(value[name]) <= 1) &&
    Number.isSafeInteger(config.min_valid_chunks) && config.min_valid_chunks >= 1 &&
    Number.isSafeInteger(config.bootstrap_samples) && config.bootstrap_samples >= 200 && config.bootstrap_samples <= 10000 &&
    Number.isSafeInteger(config.bootstrap_seed) && config.bootstrap_seed >= 0 && config.bootstrap_seed <= 2 ** 32 - 1 &&
    [config.jev_model, config.llm_model].every(model => typeof model === 'string' && model.length <= 100 && /^[A-Za-z0-9_.:/-]+$/.test(model))
}
export function configError(config: unknown, caps: ExperimentCapabilities): string {
  if (!isExperimentConfig(config)) return 'Preencha todos os parâmetros com valores válidos.'
  for (const name of numericFields) {
    if (config[name] < caps.ranges[name].min || config[name] > caps.ranges[name].max) return `${configLabels[name]} deve estar entre ${caps.ranges[name].min} e ${caps.ranges[name].max}.`
  }
  if (!caps.allowed_models.jev.includes(config.jev_model) || !caps.allowed_models.llm.includes(config.llm_model)) return 'Escolha modelos permitidos nesta API.'
  return ''
}
export function modelProvider(caps: ExperimentCapabilities, model: string): 'maritaca' | 'gemini' {
  return caps.model_providers?.[model] ?? 'maritaca'
}
export function modelReady(caps: ExperimentCapabilities, model: string): boolean {
  return !!caps.providers[modelProvider(caps, model)]
}
export function isExperimentCapabilities(value: unknown): value is ExperimentCapabilities {
  if (!object(value) || value.enabled !== true || value.config_version !== '1' || !isExperimentConfig(value.defaults) ||
    !object(value.ranges) || !object(value.allowed_models) || !object(value.providers)) return false
  const ranges = value.ranges
  if (!numericFields.every(name => {
    const range = ranges[name]
    return object(range) && [range.min, range.max, range.step].every(item => typeof item === 'number' && Number.isFinite(item)) && Number(range.min) <= Number(range.max) && Number(range.step) > 0
  })) return false
  const allowed = value.allowed_models
  if (value.scales !== undefined && (!Array.isArray(value.scales) || !value.scales.every(isOrdinalScale))) return false
  if (!['jev', 'llm'].every(name => Array.isArray(allowed[name]) && (allowed[name] as unknown[]).length > 0 && (allowed[name] as unknown[]).every(item => typeof item === 'string'))) return false
  if (typeof value.providers.typesafe !== 'boolean' || typeof value.providers.maritaca !== 'boolean') return false
  if (value.providers.gemini !== undefined && typeof value.providers.gemini !== 'boolean') return false
  if (value.model_providers !== undefined && (!object(value.model_providers) || !Object.values(value.model_providers).every(provider => provider === 'maritaca' || provider === 'gemini'))) return false
  return !configError(value.defaults, value as ExperimentCapabilities)
}

export function exportPreset(config: ExperimentConfig) {
  if (!isExperimentConfig(config)) throw new Error('Configuração inválida.')
  return { format: '8values-lab-preset', format_version: config.escala ? 2 : 1, environment: 'lab', config_version: '1', config }
}
export function importPreset(value: unknown, caps: ExperimentCapabilities): ExperimentConfig {
  if (!object(value) || Object.keys(value).sort().join(',') !== 'config,config_version,environment,format,format_version' ||
    value.format !== '8values-lab-preset' || ![1, 2].includes(value.format_version as number) || value.environment !== 'lab' || value.config_version !== caps.config_version) throw new Error('Arquivo de configuração Lab inválido ou de outra versão.')
  const error = configError(value.config, caps)
  if (error) throw new Error(error)
  const config = value.config as ExperimentConfig
  if (value.format_version === 2 && !config.escala) throw new Error('Preset sem snapshot da escala.')
  const legacy = caps.scales?.find(s => s.id === 'ordinal_9_v1')
  return { ...evidenceDefaults, primitiva_polaridade: 'score', regra_decisao: 'nivel', chunk_strategy: 'tokens', ...config, ...(!config.escala && legacy ? { escala: structuredClone(legacy) } : {}) }
}

export function experimentRecipients(mode: 'low' | 'medium' | 'high', config: ExperimentConfig | null, caps: ExperimentCapabilities | null): string {
  const llm = config && caps && modelProvider(caps, config.llm_model) === 'gemini' ? 'Google Gemini' : 'Maritaca (Sabiá)'
  if (mode === 'low') return 'TypeSafe (JEV)'
  if (mode === 'medium') return `TypeSafe (JEV) e, quando necessário, ${llm}`
  return config?.semantic_evidence_check ? `${llm} e TypeSafe (checagem de evidências)` : llm
}
