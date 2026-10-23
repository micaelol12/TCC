import { expect, test } from 'vitest'
import { isOrdinalScale, sameContent } from './ordinalScale'
import { scaleFixtures } from '../testing/scaleFixtures'
import { experimentCapabilities, analysisFixture } from '../testing/fixtures'
import { exportPreset, importPreset } from './experimentConfig'
import { isAnalysis, createAnalysisClient } from '../api/analysisApi'

const [five, nine] = scaleFixtures
test('valida escalas completas e rejeita chaves/códigos/polos/âncoras inválidos', () => {
  expect(isOrdinalScale(five)).toBe(true); expect(isOrdinalScale(nine)).toBe(true)
  for (const mutate of [
    (s: typeof five) => { s.niveis[0].valor = NaN },
    (s: typeof five) => { s.niveis[0].codigo = 0 },
    (s: typeof five) => { s.niveis[0].chave = 'sem_posicao' },
    (s: typeof five) => { s.niveis[0].polo = 'A' },
    (s: typeof five) => { s.niveis[2].valor = .4 },
    (s: typeof five) => { delete s.rubricas_por_eixo.state.sem_posicao },
    (s: typeof five) => { s.rubricas_por_eixo.state.sem_posicao.situacao = ' ' },
  ]) {
    const broken = structuredClone(five); mutate(broken); expect(isOrdinalScale(broken)).toBe(false)
  }
})

test('presets v2 preservam rubricas e v1 migra para o padrão histórico de nove níveis', () => {
  const caps = { ...experimentCapabilities, scales: scaleFixtures }
  const config = { ...caps.defaults, escala: five }
  const preset = exportPreset(config)
  expect(preset.format_version).toBe(2)
  expect(importPreset(JSON.parse(JSON.stringify(preset)), caps)).toEqual(config)
  expect(importPreset(exportPreset(caps.defaults), caps).escala).toEqual(nine)
  expect(() => importPreset({ ...preset, config: caps.defaults }, caps)).toThrow('snapshot')
})

function current(scale = five) {
  const analysis = analysisFixture()
  analysis.schema_version = '3'; analysis.escala = structuredClone(scale); analysis.escala_hash = 'a'.repeat(64)
  analysis.axes.forEach(a => { a.level_counts_by_key = Object.fromEntries(scale.niveis.map(n => [n.chave, n.codigo === 1 ? a.valid_chunks : 0])) })
  return analysis
}
test('resposta dinâmica exige snapshot e contagens correspondentes sem reconfigurar históricos', () => {
  expect(isAnalysis(current())).toBe(true)
  const unknown = current(); delete unknown.escala; expect(isAnalysis(unknown)).toBe(false)
  const missing = current(); delete missing.axes[0].level_counts_by_key!.sem_posicao; expect(isAnalysis(missing)).toBe(false)
  const totals = current(); totals.axes[0].level_counts_by_key!.sem_posicao = 1; expect(isAnalysis(totals)).toBe(false)
  const audit = current(); audit.axes[0].evidence_audit = [{ chunk_index: 0, kind: 'semantic', status: 'sustenta', level: 3 }]; expect(isAnalysis(audit)).toBe(false)
  const legacy = analysisFixture(); expect(isAnalysis(legacy)).toBe(true)
  legacy.escala = nine; expect(isAnalysis(legacy)).toBe(false)
})

test('confirma conteúdo da escala enviada, sem depender da identidade do objeto', async () => {
  const config = { ...experimentCapabilities.defaults, escala: five }
  const response = { ...current(), effective_config: structuredClone(config), config_version: '1', config_hash: 'b'.repeat(64), environment: 'lab' }
  const client = createAnalysisClient('', async () => Response.json(response))
  await expect(client.analyze('texto', 'medium', new AbortController().signal, 120, config)).resolves.toBeDefined()
  await expect(client.analyze('texto', 'medium', new AbortController().signal, 120, { ...config, escala: nine })).rejects.toThrow('confirmou')
  expect(sameContent(five, JSON.parse(JSON.stringify(five)))).toBe(true)
})
