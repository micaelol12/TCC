import questions from '../data/questions.json'
import type { Axis } from './axes'

export type Answer = -1 | -0.5 | 0 | 0.5 | 1
export type Answers = Record<number, Answer>
export type Scores = Record<Axis, number>
export type Question = { id: number; question: string; effect: { econ: number; dipl: number; govt: number; scty: number } }
export const QUESTIONS = questions as Question[]
export const QUESTION_HASH = '0a908fc283dbf7daa5b24712f4614644661cd2430c488a6ed902c00616a21fe8'
const effectKey: Record<Axis, keyof Question['effect']> = { economic: 'econ', diplomatic: 'dipl', state: 'govt', society: 'scty' }
export const maximums = Object.fromEntries(Object.entries(effectKey).map(([axis, key]) => [axis, QUESTIONS.reduce((sum, q) => sum + Math.abs(q.effect[key]), 0)])) as Scores

export function scoreAnswers(answers: Answers): Scores {
  if (QUESTIONS.length !== 70 || QUESTIONS.some(q => !Object.hasOwn(answers, q.id))) throw new Error('Responda às 70 perguntas.')
  return Object.fromEntries(Object.entries(effectKey).map(([axis, key]) => {
    const max = maximums[axis as Axis]
    const sum = QUESTIONS.reduce((acc, q) => acc + answers[q.id] * q.effect[key], 0)
    return [axis, 100 * (max + sum) / (2 * max)]
  })) as Scores
}
