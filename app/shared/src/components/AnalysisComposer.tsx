import type { ReactNode } from 'react'
import { modes, modeLabels, modeDescriptions, recipients, type Capabilities, type Mode } from '../api/analysisApi'
import styles from '../styles/Cards.module.css'
import { isLabBuild } from '../domain/experimentConfig'
import ConfirmAction from './ConfirmAction'
import HelperText from './HelperText'
import Actions from './Actions'
import Button from './Button'

type Props = {
  text: string; title: string; mode: Mode; caps: Capabilities | null;
  busy: boolean; seconds: number; error: string; capsError: string;
  onText: (text: string) => void; onTitle: (title: string) => void; onMode: (mode: Mode) => void;
  onSend: () => void; onCancel: () => void; onRetry?: () => void; onClose?: () => void; onDiscard?: () => void; source?: string; children?: ReactNode;
  experimentPanel?: ReactNode; configBlocked?: boolean; recipient?: string; draftNotice?: string
}

/** Reúne texto, modo e controles de envio com limites, estado de conexão e cancelamento. */
export default function AnalysisComposer(props: Props) {
  const { text, title, mode, caps, busy, seconds, error, capsError, onText, onTitle, onMode, onSend, onCancel, onRetry, onClose, source, children } = props
  const limit = caps?.max_chars ?? 60000
  // Match Python's Unicode code-point count, including characters outside the BMP.
  const length = Array.from(text).length
  const tooLong = length > limit
  const enabled = (caps?.modes[mode] ?? false) && !props.configBlocked

  return <section className={styles.card} aria-label="Novo texto">
    <div className="sectionHeading"><div><div className="eyebrow">Novo texto</div><h2>Nova análise</h2></div>{onClose && <Button variant="text" onClick={onClose} disabled={busy}>Fechar</Button>}</div>
    {source && <HelperText className="sourceOrigin">Selecionado em {source}</HelperText>}{children}
    <label htmlFor="local-title">Título local <span className="muted">(opcional)</span></label>
    <input id="local-title" value={title} onChange={e => onTitle(e.target.value)} placeholder="Ex.: proposta de transporte" disabled={busy} />
    <label htmlFor="text-input">Texto em português</label>
    <textarea id="text-input" rows={7} value={text} disabled={busy} onChange={e => onText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !busy && text.trim() && !tooLong && enabled) { e.preventDefault(); onSend() } }} placeholder="Selecione na página ou cole um texto político..." aria-describedby="text-help" />
    <HelperText id="text-help" error={tooLong}>{length.toLocaleString('pt-BR')} de {limit.toLocaleString('pt-BR')} caracteres. Ctrl/Cmd + Enter envia. {tooLong && 'Reduza o texto para continuar.'}</HelperText>
    {props.draftNotice && <HelperText role="status">{props.draftNotice}</HelperText>}
    <fieldset className="modeGroup" disabled={busy}><legend>Processamento</legend>{modes.map(value => <label key={value} className="modeOption"><input type="radio" name="mode" value={value} checked={mode === value} disabled={!!caps && !caps.modes[value]} onChange={() => onMode(value)} /><span><strong>{modeLabels[value]}</strong><small>{modeDescriptions[value]}{caps && !caps.modes[value] ? ' · indisponível neste serviço' : ''}</small></span></label>)}</fieldset>
    <details className="processingHelp"><summary>Como escolher o processamento?</summary>
      <p>Escolha entre a avaliação de um classificador, a classificação com revisão quando necessária ou a avaliação direta de um modelo de linguagem. Os métodos são diferentes; nenhum modo garante uma classificação correta. Compare o resultado com as evidências do texto.</p>
      <HelperText>Nos detalhes técnicos, JEV identifica o classificador e LLM significa modelo de linguagem. O tempo de análise varia com o texto e os serviços disponíveis. Os modos indisponíveis não podem ser selecionados; use “Verificar conexão e modos” para atualizar a disponibilidade.</HelperText>
    </details>
    <p className="privacyNote">Somente o texto será enviado a {props.recipient ?? recipients[mode]}. Seu perfil e histórico ficam neste navegador.</p>
    {isLabBuild && <p className="notice small">Toda execução do Lab é gravada automaticamente no banco da API, incluindo o texto enviado, parâmetros, resultado e status. As chaves de API não são gravadas.</p>}
    {props.experimentPanel}
    {capsError && <p className="error" role="status">{capsError}</p>}{onRetry && <Button variant="text" onClick={onRetry} disabled={busy}>Verificar conexão e modos</Button>}
    {error && <p className="error" role="alert">{error}</p>}
    <Actions><Button onClick={onSend} disabled={busy || !text.trim() || tooLong || !enabled}>{busy ? 'Analisando…' : 'Analisar texto'}</Button>{busy && <Button variant="secondary" onClick={onCancel}>Cancelar</Button>}
      {props.onDiscard && !!(text || title) && <ConfirmAction label="Descartar rascunho" title="Descartar este rascunho?" description="O título e o texto ainda não enviados serão apagados. As análises do histórico serão mantidas. Esta ação não pode ser desfeita." confirmLabel="Sim, descartar rascunho" disabled={busy} onConfirm={props.onDiscard} />}
    </Actions>
    <div role="status" aria-live="polite">{busy ? <div className={styles.analysisProgress}>
      <div className={styles.progressHeading}><span className={styles.spinner} aria-hidden="true" /><strong>Analisando seu texto</strong></div>
      <p>{seconds >= 30 ? 'A análise continua em andamento. Textos maiores e alguns modos podem levar mais tempo.' : 'Aguardando a análise dos modelos. O tempo varia conforme o tamanho do texto e o modo escolhido.'}</p>
      <div className={styles.progressTrack} aria-hidden="true"><span /></div>
      <span className="small muted">Você pode cancelar a qualquer momento. O texto será preservado.</span>
    </div> : !enabled && caps ? (isLabBuild ? 'Confira a configuração e cadastre suas chaves na aba API keys para usar o modo e modelo escolhidos.' : modes.some(value => caps.modes[value]) ? 'Escolha um modo disponível para continuar.' : 'Nenhum modo está disponível no momento. Verifique a conexão ou tente mais tarde. Você pode continuar preparando seu texto.') : !caps && !capsError ? 'Consultando modos disponíveis…' : ''}</div>
    {busy && <p className={styles.elapsedTime} role="timer" aria-live="off">Tempo decorrido: {Math.floor(seconds / 60).toString().padStart(2, '0')}:{(seconds % 60).toString().padStart(2, '0')}</p>}
  </section>
}
