import type { Analysis, Capabilities, Mode } from '../api/analysisApi'
import type { ExperimentCapabilities } from '../domain/experimentConfig'
export const experimentCapabilities: ExperimentCapabilities = {
  enabled: true, config_version: '1', defaults: { chunk_tokens: 600, relevance_margin_min: 0.6, level_confidence_min: 0.5, direction_margin_min: 0.2, min_valid_chunks: 16, bootstrap_samples: 2000, bootstrap_seed: 42, jev_model: 'jev-1.13.0', llm_model: 'sabia-4' },
  ranges: { chunk_tokens: { min: 100, max: 2000, step: 1 }, relevance_margin_min: { min: 0, max: 1, step: 0.01 }, level_confidence_min: { min: 0, max: 1, step: 0.01 }, direction_margin_min: { min: 0, max: 1, step: 0.01 }, min_valid_chunks: { min: 1, max: 20, step: 1 }, bootstrap_samples: { min: 200, max: 10000, step: 1 }, bootstrap_seed: { min: 0, max: 2 ** 32 - 1, step: 1 } },
  allowed_models: { jev: ['jev-1.13.0', 'jev-test'], llm: ['sabia-4', 'sabiazinho-4', 'llm-test', 'gemini-3.1-flash-lite', 'gemini-3.7-flash'] }, providers: { typesafe: true, maritaca: true, gemini: false },
  model_providers: { 'sabia-4': 'maritaca', 'sabiazinho-4': 'maritaca', 'llm-test': 'maritaca', 'gemini-3.1-flash-lite': 'gemini', 'gemini-3.7-flash': 'gemini' }, execution_storage: true,
}
export const labCapabilities: Capabilities = { max_chars: 60000, max_tokens: 12000, max_chunks: 20, modes: { low: true, medium: true, high: true }, timeout_seconds: 120, environment: 'lab', experimental: experimentCapabilities }
export const capabilities: Capabilities = { max_chars: 60000, max_tokens: 12000, max_chunks: 20, modes: { low: true, medium: true, high: true }, timeout_seconds: 120 }
export function analysisFixture(mode: Mode = 'medium', text = 'Trecho político com evidência.'): Analysis {
  return {
    schema_version: '1', pipeline_version: 'test-only', processing_level: mode, models_used: ['provedor-simulado'],
    axes: (['economic', 'diplomatic', 'state', 'society'] as const).map((axis, i) => ({
      axis, pole_a: i === 1 ? null : 75, pole_b: i === 1 ? null : 25, status: i === 1 ? 'no_evidence' : 'estimated',
      coverage: i === 1 ? 0 : 1, valid_chunks: i === 1 ? 0 : 1, total_chunks: 1, sufficient_evidence: false,
      level_counts: { minus2: 0, minus1: 0, zero: 0, plus1: i === 1 ? 0 : 1, plus2: 0 }, ci95: null,
      methods_used: mode === 'low' ? ['jev'] : ['llm'], reason_codes: [],
      evidence: mode === 'low' || i === 1 ? [] : [{ chunk_index: 0, quote: text, verified: true }],
    })), chunks: [{ index: 0, text }], logical_calls: { jev: mode === 'low' ? 1 : 0, llm: mode === 'low' ? 0 : 1 }, warnings: [],
  }
}
