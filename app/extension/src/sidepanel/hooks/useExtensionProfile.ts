import { useEffect, useState } from 'react'
import { validateProfile, type Profile } from '@8values/shared/profile'
import { readPreferences, saveProfile, LOCAL_PROFILE_KEY } from '../../storage/preferences'

export function useExtensionProfile() {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [profileError, setProfileError] = useState('')
  const [profileBusy, setProfileBusy] = useState(false)
  useEffect(() => {
    let generation = 0
    let mounted = true
    const syncProfile = async (changes: Record<string, chrome.storage.StorageChange>, area: string) => {
      if (area !== 'local' || !changes[LOCAL_PROFILE_KEY]) return
      const revision = ++generation
      try {
        const preferences = await readPreferences()
        if (!mounted || revision !== generation) return
        setProfile(preferences.profile)
      } catch { /* keep the last usable profile until storage recovers */ }
    }
    chrome.storage.onChanged.addListener(syncProfile)
    return () => { mounted = false; generation++; chrome.storage.onChanged.removeListener(syncProfile) }
  }, [])

  async function importProfile(file?: File) {
    if (!file) return
    setProfileError(''); setProfileBusy(true)
    try {
      if (file.size > 10000) throw new Error('Arquivo de perfil acima do limite de 10 KB.')
      let contents: unknown
      try { contents = JSON.parse(await file.text()) }
      catch { throw new Error('Não foi possível ler este arquivo de resultado. No site, abra “Meu resultado”, use “Baixar resultado” e selecione o arquivo baixado.') }
      const parsed = validateProfile(contents)
      if (!parsed) throw new Error('Resultado inválido ou de outra versão do questionário. Baixe o resultado novamente pelo site.')
      await saveProfile(parsed)
      setProfile(parsed)
    } catch (err) { setProfileError(err instanceof Error ? err.message : 'Não foi possível importar o perfil.') }
    finally { setProfileBusy(false) }
  }
  async function deleteProfile() {
    setProfileBusy(true); setProfileError('')
    try { await saveProfile(null); setProfile(null) }
    catch { throw new Error('Não foi possível apagar o perfil guardado. Tente novamente.') }
    finally { setProfileBusy(false) }
  }

  return { profile, setProfile, profileError, profileBusy, importProfile, deleteProfile }
}
