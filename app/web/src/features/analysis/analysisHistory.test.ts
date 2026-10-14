import { afterEach, expect, test, vi } from 'vitest'
import type { Entry } from './analysisHistory'
import { analysisFixture } from '../../../../shared/src/testing/fixtures'

afterEach(() => vi.unstubAllGlobals())

test('mantém o histórico ao recriar a tela e limpa os dados locais', async () => {
  const data = new Map<string, string>()
  vi.stubGlobal('sessionStorage', {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => { data.set(key, value) },
    removeItem: (key: string) => { data.delete(key) },
  })
  const entry: Entry = {
    id: 1, title: 'Texto de exemplo', text: 'Conteúdo', mode: 'low',
    analysis: analysisFixture('low', 'Conteúdo'),
  }
  const { saveAnalysisHistory } = await import('./analysisHistory')
  saveAnalysisHistory([entry])
  vi.resetModules()
  const reloaded = await import('./analysisHistory')
  expect(reloaded.readAnalysisHistory()).toEqual([entry])
  reloaded.clearAnalysisHistory()
  expect(reloaded.readAnalysisHistory()).toEqual([])
})
