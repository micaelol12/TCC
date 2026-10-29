import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import type { AnalysisDraft } from './analysisDraft'

const first: AnalysisDraft = { title: 'Mobilidade', text: 'Texto ainda não enviado.', mode: 'low' }
beforeEach(() => vi.resetModules())
afterEach(() => vi.unstubAllGlobals())

function storage() {
  const data = new Map<string, string>()
  const api = {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: vi.fn((key: string, value: string) => { data.set(key, value) }),
    removeItem: (key: string) => { data.delete(key) },
  }
  vi.stubGlobal('sessionStorage', api)
  return { data, api }
}

test('restaura título, texto e modo após recarregar e limpa somente o rascunho de análise', async () => {
  const { data } = storage()
  const session = await import('./analysisDraft')
  expect(session.saveAnalysisDraft(first)).toBe(true)
  data.set('other-data', 'preservar')
  vi.resetModules()
  const restored = await import('./analysisDraft')
  expect(restored.readAnalysisDraft()).toEqual(first)
  restored.clearAnalysisDraft()
  expect(restored.readAnalysisDraft()).toEqual({ title: '', text: '', mode: 'medium' })
  expect([...data.entries()]).toEqual([['other-data', 'preservar']])
})

test('quota excedida mantém o rascunho mais recente em memória sem restaurar a cópia antiga', async () => {
  const { api } = storage()
  const session = await import('./analysisDraft')
  session.saveAnalysisDraft(first)
  api.setItem.mockImplementation(() => { throw new Error('quota') })
  const newer = { ...first, text: 'Texto atualizado que não pode ser perdido.' }
  expect(session.saveAnalysisDraft(newer)).toBe(false)
  expect(session.readAnalysisDraft()).toEqual(newer)
  api.setItem.mockImplementation(() => undefined)
  expect(session.saveAnalysisDraft(newer)).toBe(true)
})

test('armazenamento bloqueado mantém o texto em memória e sinaliza falha de persistência', async () => {
  vi.stubGlobal('sessionStorage', { getItem: () => { throw new Error('blocked') }, setItem: () => { throw new Error('blocked') } })
  const session = await import('./analysisDraft')
  expect(session.readAnalysisDraft().text).toBe('')
  expect(session.saveAnalysisDraft(first)).toBe(false)
  expect(session.readAnalysisDraft()).toEqual(first)
})

test.each(['null', '{"text":', '{"title":"x","text":"y","mode":"unsupported"}'])('ignora um rascunho inválido: %s', async raw => {
  const { data } = storage()
  data.set('8values-analysis-draft-v1', raw)
  const session = await import('./analysisDraft')
  expect(session.readAnalysisDraft()).toEqual({ title: '', text: '', mode: 'medium' })
})
