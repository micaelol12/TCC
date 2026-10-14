import { modes, type Mode } from '@8values/shared/api'
import { validateProfile, type Profile } from '@8values/shared/profile'
import { storagePrefix } from '@8values/shared/domain/experimentConfig'
export const MODE_KEY = `${storagePrefix}-mode-v1`
export const LOCAL_PROFILE_KEY = `${storagePrefix}-profile-local-v1`
export const TEMP_PROFILE_KEY = `${storagePrefix}-profile-session-v1`
export type Preferences = { mode: Mode; profile: Profile | null }
export async function readPreferences(): Promise<Preferences> {
  const saved = await chrome.storage.local.get([MODE_KEY, LOCAL_PROFILE_KEY])
  const mode = saved[MODE_KEY]
  return { mode: modes.includes(mode as Mode) ? mode as Mode : 'medium', profile: validateProfile(saved[LOCAL_PROFILE_KEY]) }
}
let queue: Promise<void> = Promise.resolve()
function write(action: () => Promise<void>) {
  const current = queue.catch(() => undefined).then(action)
  queue = current
  return current
}
export async function saveMode(mode: Mode) {
  return write(async () => {
    await chrome.storage.local.set({ [MODE_KEY]: mode })
  })
}
export async function saveProfile(profile: Profile | null, permanent: boolean) {
  return write(async () => {
    // Delete a previous permanent copy even when switching to temporary use.
    await chrome.storage.local.set({ [LOCAL_PROFILE_KEY]: permanent ? profile : null })
    if (profile && !permanent) await chrome.storage.session.set({ [TEMP_PROFILE_KEY]: profile })
    else await chrome.storage.session.remove(TEMP_PROFILE_KEY)
  })
}
