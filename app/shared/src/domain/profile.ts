import { axisOrder } from './axes'
import { QUESTION_HASH, type Scores } from './quizScoring'
export type Profile = { schema_version: 1; question_hash: string; completed_at: string; scores: Scores }
export function validateProfile(data: unknown): Profile | null {
  if (!data || typeof data !== 'object') return null
  const p = data as Partial<Profile>
  if (p.schema_version !== 1 || p.question_hash !== QUESTION_HASH || typeof p.completed_at !== 'string' || !Number.isFinite(Date.parse(p.completed_at))) return null
  const scores = p.scores
  if (!scores || axisOrder.some(axis => typeof scores[axis] !== 'number' || !Number.isFinite(scores[axis]) || scores[axis] < 0 || scores[axis] > 100)) return null
  return { schema_version: 1, question_hash: QUESTION_HASH, completed_at: p.completed_at, scores: Object.fromEntries(axisOrder.map(axis => [axis, scores[axis]])) as Scores }
}
export function downloadProfile(profile: Profile) {
  const validated = validateProfile(profile)
  if (!validated) throw new Error('Perfil inválido.')
  const url = URL.createObjectURL(new Blob([JSON.stringify(validated, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url; link.download = '8values-perfil.json'; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
