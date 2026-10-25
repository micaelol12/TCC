import { modes, type Mode } from '@8values/shared/api'
import { validateProfile, type Profile } from '@8values/shared/profile'
import { storagePrefix } from '@8values/shared/domain/experimentConfig'
export const MODE_KEY = `${storagePrefix}-mode-v1`
export const LOCAL_PROFILE_KEY = `${storagePrefix}-profile-local-v1`
export const TEMP_PROFILE_KEY = `${storagePrefix}-profile-session-v1`
export type Preferences = { mode: Mode; profile: Profile | null }
export async function readPreferences(): Promise<Preferences> {
  return write(async () => {
    const [saved, session] = await Promise.all([
      chrome.storage.local.get([MODE_KEY, LOCAL_PROFILE_KEY]),
      chrome.storage.session.get(TEMP_PROFILE_KEY),
    ])
    const mode = saved[MODE_KEY]
    // Preserve the active profile from versions that supported temporary use.
    const temporary = validateProfile(session[TEMP_PROFILE_KEY])
    if (temporary) await chrome.storage.local.set({ [LOCAL_PROFILE_KEY]: temporary })
    if (TEMP_PROFILE_KEY in session) await chrome.storage.session.remove(TEMP_PROFILE_KEY)
    return { mode: modes.includes(mode as Mode) ? mode as Mode : 'medium', profile: temporary ?? validateProfile(saved[LOCAL_PROFILE_KEY]) }
  })
}
let queue: Promise<unknown> = Promise.resolve()
function write<T>(action: () => Promise<T>) {
  const current = queue.catch(() => undefined).then(action)
  queue = current
  return current
}
export async function saveMode(mode: Mode) {
  return write(async () => {
    await chrome.storage.local.set({ [MODE_KEY]: mode })
  })
}
export async function saveProfile(profile: Profile | null) {
  return write(async () => {
    await chrome.storage.local.set({ [LOCAL_PROFILE_KEY]: profile })
    await chrome.storage.session.remove(TEMP_PROFILE_KEY)
  })
}
