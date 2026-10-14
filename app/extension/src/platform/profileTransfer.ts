import { validateProfile } from '@8values/shared/profile'
import { saveProfile } from '../storage/preferences'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

export function registerProfileTransfer(webOrigin: string) {
  chrome.runtime.onMessage.addListener((message: unknown, sender, respond) => {
    if (!message || typeof message !== 'object' || !('type' in message) || message.type !== '8values:save-profile') return
    if (((message as { variant?: string }).variant ?? 'standard') !== (isLabBuild ? 'lab' : 'standard')) { respond({ ok: false, error: 'Edição da extensão incompatível com o site.' }); return }
    // Only the top-level document of our configured website may write a profile.
    let allowed = false
    try { allowed = sender.id === chrome.runtime.id && sender.frameId === 0 && sender.tab?.id !== undefined && new URL(sender.url ?? '').origin === webOrigin && sender.origin === webOrigin } catch { /* invalid sender */ }
    if (!allowed) { respond({ ok: false, error: 'Site não autorizado a enviar o perfil.' }); return }
    const data = message as { profile?: unknown; permanent?: unknown }
    const profile = validateProfile(data.profile)
    if (!profile || typeof data.permanent !== 'boolean') {
      respond({ ok: false, error: 'Perfil inválido ou de outra versão do questionário. Atualize o site e a extensão.' })
      return
    }
    void saveProfile(profile, data.permanent).then(
      () => respond({ ok: true }),
      () => respond({ ok: false, error: 'Não foi possível salvar o perfil na extensão. Tente novamente.' }),
    )
    return true
  })
}
