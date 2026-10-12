import { axisOrder } from '../domain/axes'
import type { Scores } from '../domain/quizScoring'
import { QUESTION_HASH } from '../domain/quizScoring'

export const PROFILE_KEY = 'values-profile-v1'
export const DRAFT_KEY = 'values-draft-v1'
export type Profile = { schema_version: 1; question_hash: string; completed_at: string; scores: Scores }

export function readProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    if (!raw) return null
    const data: unknown = JSON.parse(raw)
    if (!data || typeof data !== 'object') return null
    const p = data as Profile
    if (p.schema_version !== 1 || p.question_hash !== QUESTION_HASH || !Number.isFinite(Date.parse(p.completed_at))) return null
    if (!p.scores || axisOrder.some(axis => typeof p.scores[axis] !== 'number' || !Number.isFinite(p.scores[axis]) || p.scores[axis] < 0 || p.scores[axis] > 100)) return null
    return p
  } catch { return null }
}

export function saveProfile(profile: Profile): boolean {
  try { localStorage.setItem(PROFILE_KEY, JSON.stringify(profile)); return true } catch { return false }
}

export function removeLocalData() {
  try { localStorage.removeItem(PROFILE_KEY) } catch { /* storage unavailable */ }
  try { sessionStorage.removeItem(DRAFT_KEY) } catch { /* storage unavailable */ }
}
