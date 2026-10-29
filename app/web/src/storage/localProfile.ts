import { validateProfile, type Profile } from '@8values/shared/profile'
export { validateProfile } from '@8values/shared/profile'
export type { Profile } from '@8values/shared/profile'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

export const PROFILE_KEY = isLabBuild ? 'values-lab-profile-v1' : 'values-profile-v1'
export const DRAFT_KEY = isLabBuild ? 'values-lab-draft-v1' : 'values-draft-v1'

export function readProfile(): Profile | null {
  try {
    const raw = localStorage.getItem(PROFILE_KEY)
    if (!raw) return null
    return validateProfile(JSON.parse(raw))
  } catch { return null }
}

export function saveProfile(profile: Profile): boolean {
  try { localStorage.setItem(PROFILE_KEY, JSON.stringify(profile)); return true } catch { return false }
}

export function removeLocalData(strict = false) {
  let failed = false
  try { localStorage.removeItem(PROFILE_KEY) } catch { failed = true }
  try { sessionStorage.removeItem(DRAFT_KEY) } catch { failed = true }
  if (strict && failed) throw new Error('Não foi possível apagar os dados salvos no navegador.')
}
