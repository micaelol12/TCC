import { QUESTIONS, QUESTION_HASH, type Answer, type Answers } from '../../domain/quizScoring'
import { DRAFT_KEY } from '../../storage/localProfile'

export type QuizState = { index: number; answers: Answers; review: boolean; reviewVisited: boolean }
export type QuizAction = { type: 'answer'; id: number; value: Answer } | { type: 'index'; index: number } | { type: 'review' } | { type: 'reset' }
export const initialQuizState: QuizState = { index: 0, answers: {}, review: false, reviewVisited: false }
export function reduceQuizSession(state: QuizState, action: QuizAction): QuizState {
  if (action.type === 'answer') return { ...state, answers: { ...state.answers, [action.id]: action.value } }
  if (action.type === 'index') return { ...state, index: action.index, review: false }
  if (action.type === 'review') return { ...state, review: true, reviewVisited: true }
  return initialQuizState
}
export function readQuizDraft(): QuizState {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY)
    if (!raw) return initialQuizState
    const value = JSON.parse(raw)
    if (value.question_hash !== QUESTION_HASH || !Number.isInteger(value.index) || value.index < 0 || value.index >= QUESTIONS.length || !value.answers || typeof value.answers !== 'object') return initialQuizState
    const answers: Answers = {}
    for (const question of QUESTIONS) if ([-1, -.5, 0, .5, 1].includes(value.answers[question.id])) answers[question.id] = value.answers[question.id]
    return { index: value.index, answers, review: value.review === true, reviewVisited: value.reviewVisited === true }
  } catch { return initialQuizState }
}

export function saveQuizDraft(state: QuizState): boolean {
  try {
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ question_hash: QUESTION_HASH, ...state }))
    return true
  } catch {
    return false
  }
}

export function removeQuizDraft(): void {
  sessionStorage.removeItem(DRAFT_KEY)
}
