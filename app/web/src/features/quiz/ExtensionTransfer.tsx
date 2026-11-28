import { useState } from 'react'
import type { Profile } from '../../storage/localProfile'
import { sendProfileToExtension } from './sendProfileToExtension'
import HelperText from '@8values/shared/components/HelperText'
import Button from '@8values/shared/components/Button'

/** Exibe o envio do perfil à extensão e acompanha sua confirmação ou falha. */
export default function ExtensionTransfer({ profile }: { profile: Profile }) {
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  /** Transfere o perfil e só indica sucesso após a confirmação da extensão. */
  async function send() {
    setBusy(true); setStatus(''); setError('')
    try {
      await sendProfileToExtension(profile)
      setStatus('Resultado salvo na extensão! Abra a aba Comparação para usá-lo.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível enviar o resultado.') }
    finally { setBusy(false) }
  }

  return <section className="flow" aria-label="Enviar resultado para a extensão">
    <h2>Compare na extensão</h2>
    <HelperText>Envie seus quatro resultados diretamente para a extensão instalada neste navegador.</HelperText>
    <Button disabled={busy} onClick={() => void send()}>{busy ? 'Enviando resultado…' : 'Usar resultado na extensão'}</Button>
    {status && <p className="notice" role="status">{status}</p>}
    {error && <p className="error" role="alert">{error}</p>}
    <HelperText>O perfil fica salvo na extensão até você usar “Apagar perfil”. O envio substitui o perfil anterior e não passa pelo servidor.</HelperText>
  </section>
}
