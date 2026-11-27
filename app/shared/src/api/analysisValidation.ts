import { axisOrder } from '../domain/axes'
import { isExperimentCapabilities, isExperimentConfig, type ExperimentConfig } from '../domain/experimentConfig'
import { isOrdinalScale, sameContent, type OrdinalScale } from '../domain/ordinalScale'
import type { Analysis, Capabilities, EvidenceAudit, JevDiagnostic, Mode } from './analysisContracts'
import { modes } from './analysisModes'

function isRecord(value: unknown): value is Record<string, unknown> { return !!value && typeof value === 'object' && !Array.isArray(value) }
function isStringArray(value: unknown): value is string[] { return Array.isArray(value) && value.every(item => typeof item === 'string') }
function isNonNegativeInteger(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 }
function isPositiveInteger(value: unknown): value is number { return isNonNegativeInteger(value) && value > 0 }
function isPercentage(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100 }
function isProbability(value: unknown): value is number { return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 }
function isProbabilityDistribution(value: unknown, keys: string[]): boolean {
  return isRecord(value) && Object.keys(value).length === keys.length && keys.every(key => isProbability(value[key])) && Math.abs(Object.values(value).reduce<number>((sum, p) => sum + Number(p), 0) - 1) < 1e-6
}
function isJevDiagnostic(value: unknown, chunks: Analysis['chunks'], scale: OrdinalScale, rule?: string): value is JevDiagnostic {
  return isRecord(value) && isNonNegativeInteger(value.chunk_index) && chunks.some(chunk => chunk.index === value.chunk_index) &&
    ['nivel', 'polo_primeiro'].includes(value.regra_decisao as string) && (!rule || value.regra_decisao === rule) && typeof value.relevante === 'boolean' &&
    [value.nivel, value.nivel_jev_bruto].every(n => n === null || scale.niveis.some(level => level.codigo === n)) &&
    (value.grupo_mais_provavel === null || ['A', 'B', 'C'].includes(value.grupo_mais_provavel as string)) &&
    isProbabilityDistribution(value.probabilities_nivel, scale.niveis.map(level => level.chave)) && isProbabilityDistribution(value.probabilities_abc, ['A', 'B', 'C']) &&
    isProbability(value.margem_grupo) && isProbability(value.confianca_nivel) && (value.probabilidade_nivel_condicional === null || isProbability(value.probabilidade_nivel_condicional)) &&
    (value.desempate_intensidade === undefined || typeof value.desempate_intensidade === 'boolean')
}
function isEvidenceAudit(value: unknown, chunks: Analysis['chunks'], schemaVersion: string, codes?: number[]): value is EvidenceAudit {
  if (!isRecord(value) || !isNonNegativeInteger(value.chunk_index) || !chunks.some(chunk => chunk.index === value.chunk_index) ||
      !['search', 'semantic'].includes(value.kind as string) || !['found', 'not_selected', 'not_literal', 'sustenta', 'contradiz', 'insuficiente', 'uncertain', 'failed', 'invalid'].includes(value.status as string) ||
      !(codes ?? (schemaVersion === '2' ? [-4, -3, -2, -1, 0, 1, 2, 3, 4] : [-2, -1, 0, 1, 2])).includes(value.level as number)) return false
  if (!['confidence', 'existence_probability'].every(key => value[key] == null || (typeof value[key] === 'number' && Number.isFinite(value[key]) && value[key] >= 0 && value[key] <= 1))) return false
  if (!['quote', 'sentence_id', 'model'].every(key => value[key] == null || typeof value[key] === 'string')) return false
  if (!['start', 'end'].every(key => value[key] == null || isNonNegativeInteger(value[key]))) return false
  if (value.probabilities != null && (!isRecord(value.probabilities) || !Object.values(value.probabilities).every(p => typeof p === 'number' && Number.isFinite(p) && p >= 0 && p <= 1))) return false
  if (value.status === 'found') {
    const text = Array.from(chunks.find(chunk => chunk.index === value.chunk_index)!.text)
    return value.kind === 'search' && typeof value.sentence_id === 'string' && isNonNegativeInteger(value.start) && isNonNegativeInteger(value.end) && value.start < value.end && value.end <= text.length && text.slice(value.start, value.end).join('') === value.quote
  }
  return true
}
export function isCapabilities(value: unknown): value is Capabilities {
  if (!isRecord(value) || !isRecord(value.modes)) return false
  const available = value.modes
  if (value.analysis_defaults !== undefined && !isExperimentConfig(value.analysis_defaults)) return false
  if (value.model_providers !== undefined && (!isRecord(value.model_providers) || !Object.values(value.model_providers).every(provider => provider === 'maritaca' || provider === 'gemini'))) return false
  if (value.environment !== undefined && !['development', 'lab', 'production'].includes(value.environment as string)) return false
  if (value.experimental !== undefined && (!isRecord(value.experimental) ||
    (value.experimental.enabled !== false && !(value.environment === 'lab' && isExperimentCapabilities(value.experimental))))) return false
  return isPositiveInteger(value.max_chars) && isPositiveInteger(value.max_tokens) && isPositiveInteger(value.max_chunks) &&
    typeof value.timeout_seconds === 'number' && Number.isFinite(value.timeout_seconds) && value.timeout_seconds > 0 &&
    modes.every(mode => typeof available[mode] === 'boolean')
}
function hasValidExecutionMetadata(analysis: Record<string, unknown>): boolean {
  if (analysis.lab_execution_id !== undefined &&
      (typeof analysis.lab_execution_id !== 'string' || !/^[a-f0-9-]{36}$/.test(analysis.lab_execution_id))) return false
  const hasConfig = ['effective_config', 'config_version', 'config_hash', 'environment'].some(name => name in analysis)
  return !hasConfig || (isExperimentConfig(analysis.effective_config) && analysis.config_version === '1' &&
    typeof analysis.config_hash === 'string' && /^[a-f0-9]{64}$/.test(analysis.config_hash) &&
    ['development', 'lab', 'production'].includes(analysis.environment as string))
}

function hasValidScale(analysis: Record<string, unknown>, scale?: OrdinalScale): boolean {
  if (analysis.schema_version !== '3') return analysis.escala === undefined && analysis.escala_hash === undefined
  return !!scale && typeof analysis.escala_hash === 'string' && /^[a-f0-9]{64}$/.test(analysis.escala_hash) &&
    (!isExperimentConfig(analysis.effective_config) || sameContent(analysis.effective_config.escala, scale))
}

function hasValidLevelCounts(axis: Record<string, unknown>, schemaVersion: string, scale?: OrdinalScale): boolean {
  if (!isRecord(axis.level_counts)) return false
  const legacyCounts = axis.level_counts
  if (!['minus2', 'minus1', 'zero', 'plus1', 'plus2'].every(key => isNonNegativeInteger(legacyCounts[key]))) return false
  if (schemaVersion === '2' && !['minus4', 'minus3', 'plus3', 'plus4'].every(key => isNonNegativeInteger(legacyCounts[key]))) return false
  if (schemaVersion !== '3') return true
  const countsByKey = axis.level_counts_by_key
  return !!scale && isRecord(countsByKey) && Object.keys(countsByKey).length === scale.niveis.length &&
    scale.niveis.every(level => isNonNegativeInteger(countsByKey[level.chave])) &&
    Object.values(countsByKey).reduce<number>((sum, count) => sum + Number(count), 0) === axis.valid_chunks
}

function hasValidPoleEstimates(axis: Record<string, unknown>): boolean {
  if (axis.status !== 'estimated') return axis.pole_a === null && axis.pole_b === null
  return isPercentage(axis.pole_a) && isPercentage(axis.pole_b) && Math.abs(axis.pole_a + axis.pole_b - 100) <= 0.01
}

function isConfidenceInterval(value: unknown): boolean {
  return value === null || (Array.isArray(value) && value.length === 2 &&
    value.every(isPercentage) && value[0] <= value[1])
}

function isAxisResult(
  axis: unknown, chunks: Analysis['chunks'], schemaVersion: string, scale?: OrdinalScale, decisionRule?: string,
): boolean {
  if (!isRecord(axis)) return false
  if (axis.jev_diagnostics !== undefined && (!scale || !Array.isArray(axis.jev_diagnostics) ||
      !axis.jev_diagnostics.every(diagnostic => isJevDiagnostic(diagnostic, chunks, scale, decisionRule)))) return false
  if (axis.evidence_audit !== undefined && (!Array.isArray(axis.evidence_audit) ||
      !axis.evidence_audit.every(audit => isEvidenceAudit(audit, chunks, schemaVersion, scale?.niveis.map(level => level.codigo))))) return false
  if (!['estimated', 'no_evidence', 'abstained'].includes(axis.status as string) ||
      !isNonNegativeInteger(axis.valid_chunks) || !isNonNegativeInteger(axis.total_chunks) || axis.valid_chunks > axis.total_chunks ||
      !isProbability(axis.coverage) || typeof axis.sufficient_evidence !== 'boolean' || !isStringArray(axis.reason_codes) ||
      !Array.isArray(axis.methods_used) || !axis.methods_used.every(method => ['jev', 'llm'].includes(method))) return false
  if (!Array.isArray(axis.evidence) || !axis.evidence.every(evidence => isRecord(evidence) &&
      isNonNegativeInteger(evidence.chunk_index) && typeof evidence.quote === 'string' && evidence.quote.trim() &&
      evidence.verified === true && chunks.some(chunk => chunk.index === evidence.chunk_index))) return false
  return hasValidLevelCounts(axis, schemaVersion, scale) && hasValidPoleEstimates(axis) && isConfidenceInterval(axis.ci95)
}

export function isAnalysis(value: unknown): value is Analysis {
  if (!isRecord(value) || !hasValidExecutionMetadata(value)) return false
  if (!['1', '2', '3'].includes(value.schema_version as string) || typeof value.pipeline_version !== 'string' ||
      !modes.includes(value.processing_level as Mode) || !isStringArray(value.models_used) || !isStringArray(value.warnings) ||
      !isRecord(value.logical_calls) || !isNonNegativeInteger(value.logical_calls.jev) || !isNonNegativeInteger(value.logical_calls.llm) ||
      !Array.isArray(value.chunks) || !value.chunks.every(chunk => isRecord(chunk) && isNonNegativeInteger(chunk.index) && typeof chunk.text === 'string') ||
      !Array.isArray(value.axes) || value.axes.length !== 4) return false
  const chunks = value.chunks
  const axes = value.axes
  const scale = isOrdinalScale(value.escala) ? value.escala : undefined
  if (!hasValidScale(value, scale)) return false
  const decisionRule = (value.effective_config as ExperimentConfig | undefined)?.regra_decisao
  return axisOrder.every(axis => axes.filter(result => isRecord(result) && result.axis === axis).length === 1) &&
    axes.every(axis => isAxisResult(axis, chunks, value.schema_version as string, scale, decisionRule))
}
