import type { Axis } from '../domain/axes'
import type { ExperimentConfig, ExperimentCapabilities } from '../domain/experimentConfig'
import type { OrdinalScale } from '../domain/ordinalScale'

export type Mode = 'low' | 'medium' | 'high'

export type LabProvider = 'typesafe' | 'maritaca' | 'gemini'

export type EvidenceAudit = {
  chunk_index: number
  kind: 'search' | 'semantic'
  status: 'found' | 'not_selected' | 'not_literal' | 'sustenta' | 'contradiz' | 'insuficiente' | 'uncertain' | 'failed' | 'invalid'
  level: number
  quote?: string | null
  sentence_id?: string | null
  start?: number | null
  end?: number | null
  confidence?: number | null
  existence_probability?: number | null
  probabilities?: Record<string, number> | null
  model?: string | null
}

export type JevDiagnostic = {
  chunk_index: number
  regra_decisao: 'nivel' | 'polo_primeiro'
  relevante: boolean
  nivel_jev_bruto: number | null
  nivel: number | null
  grupo_mais_provavel: 'A' | 'B' | 'C' | null
  probabilities_nivel: Record<string, number>
  probabilities_abc: { A: number; B: number; C: number }
  margem_grupo: number
  probabilidade_nivel_condicional: number | null
  confianca_nivel: number
  desempate_intensidade?: boolean
}

export type AxisResult = {
  axis: Axis
  pole_a: number | null
  pole_b: number | null
  status: 'estimated' | 'no_evidence' | 'abstained'
  coverage: number
  valid_chunks: number
  total_chunks: number
  sufficient_evidence: boolean
  level_counts: {
    minus4?: number
    minus3?: number
    minus2: number
    minus1: number
    zero: number
    plus1: number
    plus2: number
    plus3?: number
    plus4?: number
  }
  ci95: [number, number] | null
  methods_used: ('jev' | 'llm')[]
  reason_codes: string[]
  evidence: { chunk_index: number; quote: string; verified: true }[]
  evidence_audit?: EvidenceAudit[]
  jev_diagnostics?: JevDiagnostic[]
  level_counts_by_key?: Record<string, number>
}

export type Analysis = {
  schema_version: string
  pipeline_version: string
  processing_level: Mode
  models_used: string[]
  axes: AxisResult[]
  chunks: { index: number; text: string }[]
  logical_calls: { jev: number; llm: number }
  warnings: string[]
  effective_config?: ExperimentConfig
  config_version?: '1'
  config_hash?: string
  environment?: 'development' | 'lab' | 'production'
  lab_execution_id?: string
  escala?: OrdinalScale
  escala_hash?: string
}

export type AnalysisEntry<Id extends number | string = number> = {
  id: Id
  title: string
  text: string
  analysis: Analysis
  mode: Mode
  source?: string
}

export type Capabilities = {
  max_chars: number
  max_tokens: number
  max_chunks: number
  modes: Record<Mode, boolean>
  timeout_seconds: number
  analysis_defaults?: ExperimentConfig
  model_providers?: Record<string, 'maritaca' | 'gemini'>
  environment?: 'development' | 'lab' | 'production'
  experimental?: ExperimentCapabilities | { enabled: false }
}
