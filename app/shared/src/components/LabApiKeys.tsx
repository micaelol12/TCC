import { useState } from 'react'
import type { createAnalysisClient, LabProvider } from '../api/analysisApi'
import type { ExperimentCapabilities } from '../domain/experimentConfig'
import HelperText from './HelperText'
import Actions from './Actions'
import Button from './Button'

const emptyKeys = { typesafe: '', maritaca: '', gemini: '' }
const providerNames = { typesafe: 'TypeSafe', maritaca: 'Maritaca', gemini: 'Gemini' }
const providerHelp = {
  typesafe: 'Libera JEV no modo baixo. O modo médio também exige a chave do provedor LLM selecionado.',
  maritaca: 'Libera sabia-4 e sabiazinho-4.',
  gemini: 'Libera gemini-3.1-flash-lite e gemini-3.7-flash.',
}

/** Permite configurar provedores da sessão Lab e atualiza os modos disponíveis após cada mudança. */
export default function LabApiKeys({ client, caps, busy, onUpdated }: {
  client: ReturnType<typeof createAnalysisClient>; caps: ExperimentCapabilities; busy: boolean; onUpdated: () => Promise<void>
}) {
  const [keys, setKeys] = useState(emptyKeys)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  /** Salva ou remove a chave do provedor e limpa o campo após a confirmação da API. */
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

  /** Encerra a sessão de chaves e atualiza a disponibilidade dos provedores na interface. */
  async function reset() {
    setSaving(true); setError('')
    try { await client.clearLabSession(); setKeys(emptyKeys); await onUpdated(); setMessage('Sessão encerrada. Cadastre suas chaves para voltar a analisar.') }
    catch (err) { setError(err instanceof Error ? err.message : 'Falha ao encerrar a sessão.') }
    finally { setSaving(false) }
  }

  return <section className="labApiKeys" aria-label="API keys">
    <h3>API keys</h3><p>O Lab exige suas próprias chaves. Cadastre os provedores necessários para o modo escolhido. Não há chaves pré-cadastradas no servidor.</p>
    <HelperText>As chaves ficam somente na memória da API por até 8 horas ou até seu reinício. O navegador guarda apenas o identificador da sessão; na extensão, ele é preservado ao fechar e reabrir o painel. As chaves não são gravadas no banco, histórico ou presets.</HelperText>
    <fieldset disabled={busy || saving}><legend>Chaves dos provedores</legend>
      {(['typesafe', 'maritaca', 'gemini'] as const).map(provider => <div className="labKeyProvider" key={provider}>
        <label htmlFor={`lab-key-${provider}`}>{providerNames[provider]} · {caps.providers[provider] ? 'configurado' : 'ausente'}</label>
        <input id={`lab-key-${provider}`} type="password" autoComplete="off" spellCheck={false} value={keys[provider]} onChange={event => setKeys(current => ({ ...current, [provider]: event.target.value }))} placeholder="Cole a chave do provedor" />
        <HelperText>{providerHelp[provider]}</HelperText>
        <Actions><Button variant="secondary" disabled={!keys[provider].trim()} onClick={() => void update(provider)}>Salvar chave {providerNames[provider]}</Button><Button variant="secondary" onClick={() => void update(provider, true)}>Desabilitar {providerNames[provider]}</Button></Actions>
      </div>)}
      <Button variant="secondary" onClick={() => void reset()}>Limpar chaves da sessão</Button>
    </fieldset>
    <HelperText>Cadastrar a chave não faz uma chamada ao provedor. A validade será conferida na próxima análise.</HelperText>
    {error && <p role="alert" className="error">{error}</p>}{message && <p role="status" className="small">{message}</p>}
  </section>
}
