import type { Profile } from '../../storage/localProfile'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

/** Envia o perfil pela ponte local e aguarda uma resposta da mesma origem, edição e tentativa. */
export function sendProfileToExtension(profile: Profile): Promise<void> {
  return new Promise((resolve, reject) => {
    const requestId = crypto.randomUUID()
    const origin = window.location.origin
    /** Cancela o prazo e remove o ouvinte de resposta ao encerrar a transferência. */
    const cleanup = () => { clearTimeout(timer); window.removeEventListener('message', receive) }
    /** Aceita somente a confirmação correspondente ao identificador desta transferência. */
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
    // Keep the persistence flag for compatibility with older installed extensions.
    window.postMessage({ type: '8values:save-profile', requestId, profile, permanent: true, ...(isLabBuild ? { variant: 'lab' } : {}) }, origin)
  })
}
