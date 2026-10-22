import type { Profile } from '../../storage/localProfile'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

export function sendProfileToExtension(profile: Profile, permanent: boolean): Promise<void> {
  return new Promise((resolve, reject) => {
    const requestId = crypto.randomUUID()
    const origin = window.location.origin
    const cleanup = () => { clearTimeout(timer); window.removeEventListener('message', receive) }
    const receive = (event: MessageEvent) => {
      if (event.source !== window || event.origin !== origin || event.data?.type !== '8values:save-profile-result' || event.data.requestId !== requestId || (event.data.variant ?? 'standard') !== (isLabBuild ? 'lab' : 'standard')) return
      cleanup()
      if (event.data.ok === true) resolve()
      else reject(new Error(typeof event.data.error === 'string' ? event.data.error : 'Não foi possível enviar o perfil. Tente novamente.'))
    }
    const timer = setTimeout(() => {
      cleanup()
      reject(new Error('A extensão não respondeu. Instale ou recarregue a extensão, abra o site pelo link na aba Comparação e tente novamente.'))
    }, 5000)
    window.addEventListener('message', receive)
    window.postMessage({ type: '8values:save-profile', requestId, profile, permanent, ...(isLabBuild ? { variant: 'lab' } : {}) }, origin)
  })
}
