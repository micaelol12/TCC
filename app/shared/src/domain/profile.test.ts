import { expect, test } from 'vitest'
import { validateProfile } from './profile'
import { QUESTION_HASH } from './quizScoring'
const profile = { schema_version: 1, question_hash: QUESTION_HASH, completed_at: '2026-10-13T12:00:00Z', scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
test('importa apenas o perfil agregado e elimina campos extras', () => {
  expect(validateProfile({ ...profile, answers: ['privado'], url: 'privado' })).toEqual(profile)
})
test('recusa outra versão, outro questionário e pontuações fora da escala', () => {
  expect(validateProfile({ ...profile, question_hash: 'old' })).toBeNull()
  expect(validateProfile({ ...profile, schema_version: 2 })).toBeNull()
  expect(validateProfile({ ...profile, scores: { ...profile.scores, state: -1 } })).toBeNull()
  expect(validateProfile({ ...profile, scores: { ...profile.scores, society: NaN } })).toBeNull()
  expect(validateProfile({ ...profile, completed_at: 123 })).toBeNull()
})
