import { afterEach, expect, test, vi } from 'vitest'
import { QUESTION_HASH } from '@8values/shared/domain/quizScoring'
import { saveMode, saveProfile, readPreferences, MODE_KEY, LOCAL_PROFILE_KEY, TEMP_PROFILE_KEY } from './preferences'
afterEach(() => vi.unstubAllGlobals())
test('perfil fica salvo entre leituras e só é removido ao apagar, sem alterar o modo', async () => {
  const local: Record<string, unknown> = {}, session: Record<string, unknown> = {}
  vi.stubGlobal('chrome', { storage: {
    local: { get: async () => local, set: async (values: Record<string, unknown>) => Object.assign(local, values) },
    session: { get: async () => session, remove: async (key: string) => { delete session[key] } },
  } })
  const profile = { schema_version: 1 as const, question_hash: QUESTION_HASH, completed_at: '2026-10-13T12:00:00Z', scores: { economic: 50, diplomatic: 50, state: 50, society: 50 } }
  session[TEMP_PROFILE_KEY] = profile
  await Promise.all([saveProfile(profile), saveMode('high')])
  expect(local[MODE_KEY]).toBe('high'); expect(local[LOCAL_PROFILE_KEY]).toEqual(profile)
  expect(await readPreferences()).toEqual({ mode: 'high', profile })
  expect(session[TEMP_PROFILE_KEY]).toBeUndefined()
  await saveProfile(null)
  expect(local[LOCAL_PROFILE_KEY]).toBeNull()
  expect(await readPreferences()).toEqual({ mode: 'high', profile: null })
})

test('migra o perfil temporário ativo de uma versão anterior e não o restaura após apagar', async () => {
  const profile = { schema_version: 1 as const, question_hash: QUESTION_HASH, completed_at: '2026-10-13T12:00:00Z', scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
  const local: Record<string, unknown> = { [LOCAL_PROFILE_KEY]: { ...profile, scores: { ...profile.scores, economic: 75 } } }
  const session: Record<string, unknown> = { [TEMP_PROFILE_KEY]: profile }
  vi.stubGlobal('chrome', { storage: {
    local: { get: async () => local, set: async (values: Record<string, unknown>) => Object.assign(local, values) },
    session: { get: async () => session, remove: async (key: string) => { delete session[key] } },
  } })
  expect((await readPreferences()).profile).toEqual(profile)
  expect(local[LOCAL_PROFILE_KEY]).toEqual(profile)
  expect(session[TEMP_PROFILE_KEY]).toBeUndefined()
  await saveProfile(null)
  expect((await readPreferences()).profile).toBeNull()
})
