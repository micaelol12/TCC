import { expect, test } from 'vitest'
import { emptySession, hydrateSession, reduceSession, fitSession, MAX_SESSION_BYTES, type Request } from './sessionState'
import { analysisFixture } from '../../../shared/src/testing/fixtures'
import { makeCapture } from '../platform/selection'
const request: Request = { id: 'request-1', owner: 'panel-1', text: 'Primeiro texto.', title: 'Primeiro', source: 'example.org', mode: 'medium', startedAt: 1 }

test('nova seleção durante análise não altera o snapshot enviado', () => {
  let state = reduceSession(emptySession(), { type: 'edit', draft: { text: request.text, title: request.title } })
  state = reduceSession(state, { type: 'begin', request })
  const capture = makeCapture('Novo texto.', 1, 2, 'https://example.org/artigo?private=1#token')
  state = reduceSession(state, { type: 'capture', capture })
  expect(state.request?.text).toBe(request.text)
  expect(state.pending?.source).toBe('example.org')
  state = reduceSession(state, { type: 'success', id: request.id, analysis: analysisFixture('medium', request.text) })
  expect(state.entries[0].text).toBe(request.text)
  expect(state.pending?.text).toBe('Novo texto.')
  expect(reduceSession(state, { type: 'use-pending' }).draft.text).toBe('Novo texto.')
})
test('edição não enviada precisa de escolha explícita e captura antiga não sobrescreve a nova', () => {
  let state = reduceSession(emptySession(), { type: 'edit', draft: { text: 'Edição do usuário' } })
  const first = { ...makeCapture('Primeiro', 1, 1), createdAt: 100 }
  const second = { ...makeCapture('Segundo', 1, 1), createdAt: 101 }
  state = reduceSession(state, { type: 'capture', capture: second })
  state = reduceSession(state, { type: 'capture', capture: first })
  expect(state.pending?.id).toBe(second.id)
  expect(state.draft.text).toBe('Edição do usuário')
  state = reduceSession(state, { type: 'ignore-pending' })
  expect(reduceSession(state, { type: 'capture', capture: second })).toBe(state)
})
test('reabrir recupera texto em andamento e marca interrupção sem requisição ativa', () => {
  const recovered = hydrateSession({ ...emptySession(), request })
  expect(recovered.request).toBeNull()
  expect(recovered.draft.text).toBe(request.text)
  expect(recovered.notice).toContain('interrompida')
  expect(recovered.showComposer).toBe(true)
})
test('resposta antiga não encerra a requisição atual e falha preserva o texto', () => {
  let state = { ...emptySession(), draft: { text: request.text, title: request.title } }
  state = reduceSession(state, { type: 'begin', request })
  expect(reduceSession(state, { type: 'success', id: 'old', analysis: analysisFixture() })).toBe(state)
  state = reduceSession(state, { type: 'failure', id: request.id, message: 'cancelada' })
  expect(state.draft.text).toBe(request.text)
  expect(state.request).toBeNull()
})
test('histórico respeita quantidade e orçamento, sem descartar rascunhos silenciosamente', () => {
  const entries = Array.from({ length: 12 }, (_, index) => ({ id: String(index), text: 'x'.repeat(90000), title: 'Título', mode: 'medium' as const, analysis: analysisFixture() }))
  const fitted = fitSession({ ...emptySession(), entries, selectedId: '11' })
  expect(fitted.trimmed).toBe(true)
  expect(fitted.state.entries.length).toBeLessThan(10)
  expect(fitted.state.selectedId).toBe('11')
  expect(new TextEncoder().encode(JSON.stringify(fitted.state)).length).toBeLessThanOrEqual(MAX_SESSION_BYTES)
  expect(() => fitSession({ ...emptySession(), draft: { text: 'x'.repeat(MAX_SESSION_BYTES + 1), title: '' } })).toThrow('Reduza')
})
test('dados corrompidos e limpeza não restauram seleção descartada', () => {
  const state = hydrateSession({ ...emptySession(), entries: [null, { id: 'bad' }] })
  expect(state.entries).toEqual([])
  const capture = makeCapture('Selecionado', 1, 1)
  const cleared = reduceSession(reduceSession(state, { type: 'capture', capture }), { type: 'clear' })
  expect(reduceSession(cleared, { type: 'capture', capture }).draft.text).toBe('')
})
