import { useState } from 'react'
import type { Profile } from '../../storage/localProfile'
import { sendProfileToExtension } from './sendProfileToExtension'

export default function ExtensionTransfer({ profile }: { profile: Profile }) {
  const [permanent, setPermanent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  async function send() {
    setBusy(true); setStatus(''); setError('')
    try {
      await sendProfileToExtension(profile, permanent)
      setStatus(permanent ? 'Resultado salvo na extensão! Abra a aba Comparação para usá-lo.' : 'Resultado enviado para esta sessão da extensão! Abra a aba Comparação para usá-lo.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível enviar o resultado.') }
    finally { setBusy(false) }
  }
  return <section className="flow" aria-label="Enviar resultado para a extensão">
    <h2>Compare na extensão</h2>
    <p className="muted small">Envie seus quatro resultados diretamente para a extensão instalada neste navegador.</p>
    <label className="check"><input type="checkbox" checked={permanent} disabled={busy} onChange={event => { setPermanent(event.target.checked); setStatus('') }} />Manter meu resultado salvo na extensão</label>
    <button disabled={busy} onClick={() => void send()}>{busy ? 'Enviando resultado…' : 'Usar resultado na extensão'}</button>
    {status && <p className="notice" role="status">{status}</p>}
    {error && <p className="error" role="alert">{error}</p>}
    <p className="muted small">Sem marcar a opção, o perfil fica apenas nesta sessão. O envio substitui o perfil anterior da extensão e não passa pelo servidor.</p>
  </section>
}
