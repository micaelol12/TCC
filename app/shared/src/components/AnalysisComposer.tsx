import type { ReactNode } from 'react'
import { modes, modeLabels, modeDescriptions, recipients, type Capabilities, type Mode } from '../api/analysisApi'
import styles from '../styles/Cards.module.css'

type Props = {
  text: string; title: string; mode: Mode; caps: Capabilities | null;
  busy: boolean; seconds: number; error: string; capsError: string;
  onText: (text: string) => void; onTitle: (title: string) => void; onMode: (mode: Mode) => void;
  onSend: () => void; onCancel: () => void; onRetry?: () => void; onClose?: () => void; source?: string; children?: ReactNode
}
export default function AnalysisComposer(props: Props) {
  const { text, title, mode, caps, busy, seconds, error, capsError, onText, onTitle, onMode, onSend, onCancel, onRetry, onClose, source, children } = props
  const limit = caps?.max_chars ?? 60000
  // Match Python's Unicode code-point count, including characters outside the BMP.
  const length = Array.from(text).length
  const tooLong = length > limit
  const enabled = caps?.modes[mode] ?? false
  return <section className={styles.card} aria-label="Novo texto">
    <div className="sectionHeading"><div><div className="eyebrow">Novo texto</div><h2>Nova análise</h2></div>{onClose && <button className="textButton" onClick={onClose} disabled={busy}>Fechar</button>}</div>
    {source && <p className="muted small sourceOrigin">Selecionado em {source}</p>}{children}
    <label htmlFor="local-title">Título local <span className="muted">(opcional)</span></label>
    <input id="local-title" value={title} onChange={e => onTitle(e.target.value)} placeholder="Ex.: proposta de transporte" disabled={busy} />
    <label htmlFor="text-input">Texto em português</label>
    <textarea id="text-input" rows={7} value={text} disabled={busy} onChange={e => onText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !busy && text.trim() && !tooLong && enabled) { e.preventDefault(); onSend() } }} placeholder="Selecione na página ou cole um texto político..." aria-describedby="text-help" />
    <p id="text-help" className={tooLong ? 'error small' : 'muted small'}>{length.toLocaleString('pt-BR')} de {limit.toLocaleString('pt-BR')} caracteres. Ctrl/Cmd + Enter envia. {tooLong && 'Reduza o texto para continuar.'}</p>
    <fieldset className="modeGroup" disabled={busy}><legend>Processamento</legend>{modes.map(value => <label key={value} className="modeOption"><input type="radio" name="mode" value={value} checked={mode === value} onChange={() => onMode(value)} /><span><strong>{modeLabels[value]}</strong><small>{modeDescriptions[value]}{caps && !caps.modes[value] ? ' · indisponível' : ''}</small></span></label>)}</fieldset>
    <p className="privacyNote">Somente o texto será enviado a {recipients[mode]}. Seu perfil e histórico ficam neste navegador.</p>
    {capsError && <p className="error" role="status">{capsError}</p>}{onRetry && <button className="textButton" onClick={onRetry} disabled={busy}>Verificar conexão e modos</button>}
    {error && <p className="error" role="alert">{error}</p>}
    <div className="actions"><button onClick={onSend} disabled={busy || !text.trim() || tooLong || !enabled}>Analisar texto</button>{busy && <button className="secondary" onClick={onCancel}>Cancelar</button>}</div>
    <div role="status" aria-live="polite">{busy ? `Analisando o texto há ${seconds} segundos. O tempo varia conforme o tamanho e o modo escolhido.` : !enabled && caps ? 'Escolha um modo disponível neste servidor.' : !caps && !capsError ? 'Consultando modos disponíveis…' : ''}</div>
  </section>
}
