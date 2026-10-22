import { useState } from 'react'
import type { createAnalysisClient, LabProvider } from '../api/analysisApi'
import type { ExperimentCapabilities } from '../domain/experimentConfig'

const emptyKeys = { typesafe: '', maritaca: '', gemini: '' }
const providerNames = { typesafe: 'TypeSafe', maritaca: 'Maritaca', gemini: 'Gemini' }
const providerHelp = {
  typesafe: 'Libera JEV no modo baixo. O modo médio também exige a chave do provedor LLM selecionado.',
  maritaca: 'Libera sabia-4 e sabiazinho-4.',
  gemini: 'Libera gemini-3.1-flash-lite e gemini-3.7-flash.',
}

export default function LabApiKeys({ client, caps, busy, onUpdated }: {
  client: ReturnType<typeof createAnalysisClient>; caps: ExperimentCapabilities; busy: boolean; onUpdated: () => Promise<void>
}) {
  const [keys, setKeys] = useState(emptyKeys)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  async function update(provider: LabProvider, remove = false) {
    setSaving(true); setError(''); setMessage('')
    try {
      if (remove) await client.removeLabKey(provider)
      else await client.saveLabKey(provider, keys[provider].trim())
      setKeys(current => ({ ...current, [provider]: '' }))
      await onUpdated()
      setMessage(remove ? 'Provedor desabilitado nesta sessão.' : 'Chave configurada nesta sessão. Os modelos do provedor foram liberados.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Falha ao configurar a chave.') }
    finally { setSaving(false) }
  }
  async function reset() {
    setSaving(true); setError('')
    try { await client.clearLabSession(); setKeys(emptyKeys); await onUpdated(); setMessage('Sessão encerrada. Cadastre suas chaves para voltar a analisar.') }
    catch (err) { setError(err instanceof Error ? err.message : 'Falha ao encerrar a sessão.') }
    finally { setSaving(false) }
  }
  return <section className="labApiKeys" aria-label="API keys">
    <h3>API keys</h3><p>O Lab exige suas próprias chaves. Cadastre os provedores necessários para o modo escolhido. Não há chaves pré-cadastradas no servidor.</p>
    <p className="small muted">As chaves ficam somente na memória da API por até 8 horas ou até seu reinício. O navegador guarda apenas o identificador da sessão. As chaves não são gravadas no banco, histórico ou presets.</p>
    <fieldset disabled={busy || saving}><legend>Chaves dos provedores</legend>
      {(['typesafe', 'maritaca', 'gemini'] as const).map(provider => <div className="labKeyProvider" key={provider}>
        <label htmlFor={`lab-key-${provider}`}>{providerNames[provider]} · {caps.providers[provider] ? 'configurado' : 'ausente'}</label>
        <input id={`lab-key-${provider}`} type="password" autoComplete="off" spellCheck={false} value={keys[provider]} onChange={event => setKeys(current => ({ ...current, [provider]: event.target.value }))} placeholder="Cole a chave do provedor" />
        <p className="small muted">{providerHelp[provider]}</p>
        <div className="actions"><button className="secondary" disabled={!keys[provider].trim()} onClick={() => void update(provider)}>Salvar chave {providerNames[provider]}</button><button className="secondary" onClick={() => void update(provider, true)}>Desabilitar {providerNames[provider]}</button></div>
      </div>)}
      <button className="secondary" onClick={() => void reset()}>Limpar chaves da sessão</button>
    </fieldset>
    <p className="small muted">Cadastrar a chave não faz uma chamada ao provedor. A validade será conferida na próxima análise.</p>
    {error && <p role="alert" className="error">{error}</p>}{message && <p role="status" className="small">{message}</p>}
  </section>
}
