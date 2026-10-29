import { afterEach, expect, test, vi } from 'vitest'
import type { Entry } from './analysisHistory'
import { analysisFixture } from '../../../../shared/src/testing/fixtures'

afterEach(() => { vi.unstubAllGlobals(); vi.resetModules() })

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

test('falha de gravação é sinalizada e não restaura uma versão anterior do histórico', async () => {
  const data = new Map<string, string>()
  const setItem = vi.fn((key: string, value: string) => { data.set(key, value) })
  vi.stubGlobal('sessionStorage', {
    getItem: (key: string) => data.get(key) ?? null, setItem,
    removeItem: (key: string) => { data.delete(key) },
  })
  const session = await import('./analysisHistory')
  const entry: Entry = { id: 1, title: 'Primeira análise', text: 'Conteúdo', mode: 'low', analysis: analysisFixture('low', 'Conteúdo') }
  expect(session.saveAnalysisHistory([entry])).toBe(true)
  setItem.mockImplementation(() => { throw new Error('quota') })
  const updated = [entry, { ...entry, id: 2, title: 'Segunda análise' }]
  expect(session.saveAnalysisHistory(updated)).toBe(false)
  expect(session.readAnalysisHistory()).toEqual(updated)
  session.clearAnalysisHistory()
  expect(session.readAnalysisHistory()).toEqual([])
})
