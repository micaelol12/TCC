import { expect, test } from 'vitest'
import { evidenceDefaults, exportPreset, importPreset, isExperimentConfig, experimentRecipients } from './experimentConfig'
import { experimentCapabilities, analysisFixture } from '../testing/fixtures'
import { isAnalysis } from '../api/analysisApi'

test('migra presets antigos com opções desligadas e valida novos campos', () => {
  const { semantic_evidence_check: _s, jev_evidence_search: _j, evidence_existence_min: _e, ...old } = experimentCapabilities.defaults
  expect(importPreset(exportPreset(old), experimentCapabilities)).toEqual({ ...old, ...evidenceDefaults })
  for (const field of ['semantic_evidence_check', 'jev_evidence_search']) {
    expect(isExperimentConfig({ ...old, [field]: 'true' })).toBe(false)
    expect(isExperimentConfig({ ...old, [field]: true })).toBe(true)
  }
  expect(isExperimentConfig({ ...old, evidence_existence_min: NaN })).toBe(false)
  expect(isExperimentConfig({ ...old, evidence_existence_min: 1.1 })).toBe(false)
  expect(isExperimentConfig({ ...old, secret: 'not-allowed' })).toBe(false)
})

test('checagem semântica no modo alto informa TypeSafe e provedor LLM', () => {
  const config = { ...experimentCapabilities.defaults, llm_model: 'gemini-3.7-flash', semantic_evidence_check: true }
  expect(experimentRecipients('high', config, experimentCapabilities)).toBe('Google Gemini e TypeSafe (checagem de evidências)')
  expect(experimentRecipients('high', { ...config, semantic_evidence_check: false }, experimentCapabilities)).toBe('Google Gemini')
})

test('auditorias persistidas validam probabilidades, chunks e offsets Unicode', () => {
  const text = '😀 Defendemos ampliar os serviços públicos.'
  const result = analysisFixture('low', text)
  result.axes[0].evidence_audit = [{ chunk_index: 0, kind: 'search', status: 'found', level: 1,
    quote: text, sentence_id: 'S000', start: 0, end: Array.from(text).length, existence_probability: .9, confidence: .8 }]
  expect(isAnalysis(result)).toBe(true)
  result.axes[0].evidence_audit[0].end = text.length
  expect(isAnalysis(result)).toBe(false)
  result.axes[0].evidence_audit[0].end = Array.from(text).length
  result.axes[0].evidence_audit[0].confidence = NaN
  expect(isAnalysis(result)).toBe(false)
  result.axes[0].evidence_audit[0].confidence = .8
  result.axes[0].evidence_audit[0].chunk_index = 10
  expect(isAnalysis(result)).toBe(false)
})
