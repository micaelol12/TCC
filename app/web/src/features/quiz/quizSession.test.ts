import { afterEach, expect, test, vi } from 'vitest'
import { QUESTION_HASH, QUESTIONS } from '../../domain/quizScoring'
import { DRAFT_KEY } from '../../storage/localProfile'
import { initialQuizState, readQuizDraft, reduceQuizSession, removeQuizDraft, saveQuizDraft } from './quizSession'

afterEach(() => vi.unstubAllGlobals())

function mockStorage() {
  const values = new Map<string, string>()
  vi.stubGlobal('sessionStorage', {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
  })
  return values
}

test('editar uma resposta preserva as demais e permite voltar à revisão', () => {
  const firstQuestion = QUESTIONS[0].id
  const secondQuestion = QUESTIONS[1].id
  let state = reduceQuizSession(initialQuizState, { type: 'answer', id: firstQuestion, value: 1 })
  state = reduceQuizSession(state, { type: 'answer', id: secondQuestion, value: -.5 })
  state = reduceQuizSession(state, { type: 'review' })
  state = reduceQuizSession(state, { type: 'index', index: 0 })
  state = reduceQuizSession(state, { type: 'answer', id: firstQuestion, value: 0 })
  expect(state.answers).toEqual({ [firstQuestion]: 0, [secondQuestion]: -.5 })
  expect(state.review).toBe(false)
  expect(state.reviewVisited).toBe(true)
  expect(initialQuizState.answers).toEqual({})
})

test('restaura o rascunho com a revisão e filtra respostas inválidas', () => {
  const storage = mockStorage()
  storage.set(DRAFT_KEY, JSON.stringify({
    question_hash: QUESTION_HASH, index: 1, review: true, reviewVisited: true,
    answers: { [QUESTIONS[0].id]: .5, [QUESTIONS[1].id]: '1', [QUESTIONS[2].id]: 4 },
  }))
  expect(readQuizDraft()).toEqual({
    index: 1, answers: { [QUESTIONS[0].id]: .5 }, review: true, reviewVisited: true,
  })
})

test.each(['{', JSON.stringify({ question_hash: 'outro-questionário', index: 0, answers: {} })])(
  'ignora um rascunho corrompido ou de outro questionário: %s', raw => {
    mockStorage().set(DRAFT_KEY, raw)
    expect(readQuizDraft()).toEqual(initialQuizState)
  },
)

test('salva e descarta somente o rascunho do questionário', () => {
  const storage = mockStorage()
  storage.set('outros-dados', 'preservados')
  expect(saveQuizDraft(initialQuizState)).toBe(true)
  expect(JSON.parse(storage.get(DRAFT_KEY)!)).toEqual({ question_hash: QUESTION_HASH, ...initialQuizState })
  removeQuizDraft()
  expect(storage.has(DRAFT_KEY)).toBe(false)
  expect(storage.get('outros-dados')).toBe('preservados')
})

test('armazenamento bloqueado mantém a página utilizável e sinaliza falha ao salvar', () => {
  vi.stubGlobal('sessionStorage', {
    getItem: () => { throw new Error('bloqueado') },
    setItem: () => { throw new Error('bloqueado') },
  })
  expect(readQuizDraft()).toEqual(initialQuizState)
  expect(saveQuizDraft(initialQuizState)).toBe(false)
})
