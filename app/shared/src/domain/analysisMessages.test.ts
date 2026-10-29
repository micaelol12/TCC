import { expect, test } from 'vitest'
import { describeAnalysisReason } from './analysisMessages'

test('descreve limitações do resultado e oferece uma mensagem segura para códigos desconhecidos', () => {
  expect(describeAnalysisReason('evidencia_limitada')).toContain('Poucos trechos válidos')
  expect(describeAnalysisReason('falha_autenticacao_jev')).toContain('equipe responsável')
  for (const code of ['novo_codigo', '__proto__', 'toString']) {
    expect(describeAnalysisReason(code)).toContain('limitação adicional')
    expect(describeAnalysisReason(code)).not.toContain(code)
  }
})
