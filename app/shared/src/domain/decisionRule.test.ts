import { expect, test } from 'vitest'
import { isAnalysis, type JevDiagnostic } from '../api/analysisApi'
import { analysisFixture, experimentCapabilities } from '../testing/fixtures'
import { scaleFixtures } from '../testing/scaleFixtures'

function result() {
  const scale = structuredClone(scaleFixtures[1])
  const a = analysisFixture('low')
  a.schema_version = '3'; a.escala = scale; a.escala_hash = 'a'.repeat(64)
  a.effective_config = { ...experimentCapabilities.defaults, regra_decisao: 'polo_primeiro', escala: scale }
  a.config_version = '1'; a.config_hash = 'b'.repeat(64); a.environment = 'lab'
  a.axes.forEach(axis => { axis.level_counts_by_key = Object.fromEntries(scale.niveis.map(n => [n.chave, n.codigo === 1 ? axis.valid_chunks : 0])) })
  const diagnostic: JevDiagnostic = { chunk_index: 0, regra_decisao: 'polo_primeiro', relevante: true,
    nivel_jev_bruto: 0, nivel: -3, grupo_mais_provavel: 'B', probabilities_abc: { A: 0, B: .68, C: .32 },
    probabilities_nivel: Object.fromEntries(scale.niveis.map((n, i) => [n.chave, [.26, .28, .13, .01, .32, 0, 0, 0, 0][i]])),
    margem_grupo: .36, probabilidade_nivel_condicional: .28 / .68, confianca_nivel: .24 }
  a.axes[0].jev_diagnostics = [diagnostic]
  return a
}

test('valida o diagnóstico preservado com a escala e regra da execução', () => {
  expect(isAnalysis(result())).toBe(true)
  const historical = result(); delete historical.axes[0].jev_diagnostics
  expect(isAnalysis(historical)).toBe(true)
})

test('rejeita diagnósticos incompatíveis, distribuições inválidas e regras diferentes', () => {
  for (const mutate of [
    (d: JevDiagnostic) => { d.chunk_index = 99 },
    (d: JevDiagnostic) => { d.nivel = 99 },
    (d: JevDiagnostic) => { d.regra_decisao = 'nivel' },
    (d: JevDiagnostic) => { d.probabilities_abc.B = 1 },
    (d: JevDiagnostic) => { d.probabilities_nivel.sem_posicao = NaN },
    (d: JevDiagnostic) => { d.probabilidade_nivel_condicional = 1.1 },
  ]) {
    const a = result(); mutate(a.axes[0].jev_diagnostics![0]); expect(isAnalysis(a)).toBe(false)
  }
})
