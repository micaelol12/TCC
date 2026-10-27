import { expect, test } from 'vitest'
import { configError, exportPreset, importPreset, isExperimentCapabilities, isExperimentConfig } from './experimentConfig'
import { experimentCapabilities, labCapabilities, analysisFixture } from '../testing/fixtures'
import { createAnalysisClient, isAnalysis, isCapabilities } from '../api/analysisApi'

const defaults = experimentCapabilities.defaults
test('preserva segmentação por sentenças e importa presets antigos com tokens', () => {
  const sentences = { ...defaults, chunk_strategy: 'sentencas' as const }
  expect(importPreset(exportPreset(sentences), experimentCapabilities)).toEqual(sentences)
  const { chunk_strategy: _s, ...historical } = defaults
  expect(isExperimentConfig(historical)).toBe(true)
  expect(importPreset(exportPreset(historical), experimentCapabilities).chunk_strategy).toBe('tokens')
  for (const invalid of ['other', '', null, true, 1]) expect(isExperimentConfig({ ...defaults, chunk_strategy: invalid })).toBe(false)
})
test('preserva Choice nos presets e usa Score para configurações históricas', () => {
  const choice = { ...defaults, primitiva_polaridade: 'choice' as const }
  expect(importPreset(exportPreset(choice), experimentCapabilities)).toEqual(choice)
  const { primitiva_polaridade: _p, ...historical } = defaults
  expect(isExperimentConfig(historical)).toBe(true)
  expect(importPreset(exportPreset(historical), { ...experimentCapabilities, defaults: choice }).primitiva_polaridade).toBe('score')
  for (const invalid of ['noul', '', null, true, 1]) expect(isExperimentConfig({ ...defaults, primitiva_polaridade: invalid })).toBe(false)
})
test('regra experimental acompanha presets e configurações históricas mantêm nível global', () => {
  const grouped = { ...defaults, regra_decisao: 'polo_primeiro' as const }
  expect(importPreset(exportPreset(grouped), experimentCapabilities)).toEqual(grouped)
  const { regra_decisao: _r, ...historical } = defaults
  expect(importPreset(exportPreset(historical), { ...experimentCapabilities, defaults: grouped }).regra_decisao).toBe('nivel')
  for (const invalid of ['other', '', null, true, 1]) expect(isExperimentConfig({ ...defaults, regra_decisao: invalid })).toBe(false)
})
test('presets são estritos e revalidados contra os modelos e limites atuais', () => {
  const preset = exportPreset(defaults)
  expect(importPreset(JSON.parse(JSON.stringify(preset)), experimentCapabilities)).toEqual(defaults)
  expect(() => importPreset({ ...preset, MARITACA_API_KEY: 'secret' }, experimentCapabilities)).toThrow()
  expect(() => importPreset({ ...preset, config: { ...defaults, api_key: 'secret' } }, experimentCapabilities)).toThrow()
  expect(() => importPreset({ ...preset, environment: 'production' }, experimentCapabilities)).toThrow()
  expect(() => importPreset(preset, { ...experimentCapabilities, allowed_models: { jev: ['new'], llm: ['new'] } })).toThrow('modelos')
  expect(configError({ ...defaults, min_valid_chunks: 21 }, experimentCapabilities)).toContain('entre 1 e 20')
})
test.each([{ ...defaults, bootstrap_samples: NaN }, { ...defaults, chunk_tokens: 99 }, { ...defaults, bootstrap_seed: 1.5 }, { ...defaults, direction_margin_min: Infinity }, { ...defaults, level_confidence_min: '0.5' }])('rejeita parâmetros inválidos', value => {
  expect(isExperimentConfig(value)).toBe(false)
})
test('valida capacidades Lab e metadados sem impedir resultados anteriores', () => {
  expect(isExperimentCapabilities(experimentCapabilities)).toBe(true)
  expect(isCapabilities(labCapabilities)).toBe(true)
  expect(isCapabilities({ ...labCapabilities, environment: 'production' })).toBe(false)
  expect(isExperimentCapabilities({ ...experimentCapabilities, defaults: { ...defaults, chunk_tokens: 50 } })).toBe(false)
  expect(isAnalysis(analysisFixture())).toBe(true)
  expect(isAnalysis({ ...analysisFixture(), effective_config: defaults })).toBe(false)
  expect(isAnalysis({ ...analysisFixture(), effective_config: defaults, config_version: '1', config_hash: 'a'.repeat(64), environment: 'lab' })).toBe(true)
})
test('envia o snapshot do Lab e exige confirmação da configuração utilizada', async () => {
  let body = ''
  const response = { ...analysisFixture(), effective_config: defaults, config_version: '1', config_hash: 'a'.repeat(64), environment: 'lab' }
  const client = createAnalysisClient('', async (_url, options) => { body = options?.body as string; return Response.json(response) })
  await client.analyze('texto', 'medium', new AbortController().signal, 120, defaults)
  expect(JSON.parse(body).experiment_config).toEqual(defaults)
  await expect(client.analyze('texto', 'medium', new AbortController().signal, 120, { ...defaults, chunk_tokens: 400 })).rejects.toThrow('confirmou')
  await expect(client.analyze('texto', 'medium', new AbortController().signal, 120, { ...defaults, primitiva_polaridade: 'choice' })).rejects.toThrow('confirmou')
  await expect(client.analyze('texto', 'medium', new AbortController().signal, 120, { ...defaults, regra_decisao: 'polo_primeiro' })).rejects.toThrow('confirmou')
  await expect(client.analyze('texto', 'medium', new AbortController().signal, 120, { ...defaults, chunk_strategy: 'tokens' })).rejects.toThrow('confirmou')
})
