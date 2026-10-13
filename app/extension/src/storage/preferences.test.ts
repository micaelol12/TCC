import { afterEach, expect, test, vi } from 'vitest'
import { QUESTION_HASH } from '@8values/shared/domain/quizScoring'
import { saveMode, saveProfile, readPreferences, MODE_KEY, LOCAL_PROFILE_KEY, TEMP_PROFILE_KEY } from './preferences'
afterEach(() => vi.unstubAllGlobals())
test('modo e perfil usam chaves independentes e perfil temporário apaga a cópia permanente', async () => {
  const local: Record<string, unknown> = {}, session: Record<string, unknown> = {}
  vi.stubGlobal('chrome', { storage: {
    local: { get: async () => local, set: async (values: Record<string, unknown>) => Object.assign(local, values) },
    session: { set: async (values: Record<string, unknown>) => Object.assign(session, values), remove: async (key: string) => { delete session[key] } },
  } })
  const profile = { schema_version: 1 as const, question_hash: QUESTION_HASH, completed_at: '2026-10-13T12:00:00Z', scores: { economic: 50, diplomatic: 50, state: 50, society: 50 } }
  await Promise.all([saveProfile(profile, true), saveMode('high')])
  expect(local[MODE_KEY]).toBe('high'); expect(local[LOCAL_PROFILE_KEY]).toEqual(profile)
  expect(await readPreferences()).toEqual({ mode: 'high', profile })
  await saveProfile(profile, false)
  expect(local[LOCAL_PROFILE_KEY]).toBeNull(); expect(session[TEMP_PROFILE_KEY]).toEqual(profile)
  await saveProfile(null, false)
  expect(session[TEMP_PROFILE_KEY]).toBeUndefined()
})
