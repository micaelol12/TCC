import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import { createPortal } from 'react-dom'
import type { AnalysisEntry } from '../api/analysisApi'
import { buildReport, REPORT_COMMENT_LIMIT, REPORT_NOTICE, type ReportClient, type ReportRequest, type ReportResponse } from '../api/reportApi'
import { AXES } from '../domain/axes'

export default function ReportDialog({ entry, client, origin }: { entry: AnalysisEntry<number | string>; client: ReportClient; origin: ReportRequest['client'] }) {
  const [open, setOpen] = useState(false)
  const [consent, setConsent] = useState(false)
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [receipt, setReceipt] = useState<ReportResponse | null>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const controller = useRef<AbortController | null>(null)
  const attempt = useRef<ReportRequest | null>(null)
  const mounted = useRef(true)
  const id = useId()
  useEffect(() => {
    mounted.current = true
    return () => { mounted.current = false; controller.current?.abort() }
  }, [])
  useEffect(() => {
    if (open && dialog.current && !dialog.current.open) { dialog.current.showModal(); heading.current?.focus() }
  }, [open])

  function close() {
    if (controller.current || busy) return
    dialog.current?.close(); setOpen(false); setConsent(false)
  }
  function keepFocus(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== 'Tab') return
    const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), textarea:not(:disabled), summary'))
      .filter(element => element.getClientRects().length > 0)
    const first = controls[0], last = controls.at(-1)
    if (!first || !last) { event.preventDefault(); heading.current?.focus(); return }
    if (event.shiftKey && (document.activeElement === first || document.activeElement === heading.current)) { event.preventDefault(); last.focus() }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }
  async function send() {
    if (!consent || controller.current || receipt || Array.from(comment).length > REPORT_COMMENT_LIMIT) return
    // Preserve the UUID and snapshot on retries, including an uncertain network outcome.
    if (!attempt.current || attempt.current.comment !== comment) attempt.current = buildReport(entry, origin, comment, crypto.randomUUID())
    const current = new AbortController(); controller.current = current
    setBusy(true); setError('')
    try {
      const result = await client.report(attempt.current, current.signal)
      if (mounted.current) { setReceipt(result); dialog.current?.close(); setOpen(false); setConsent(false) }
    } catch (err) {
      if (mounted.current) setError(err instanceof Error ? err.message : 'Não foi possível confirmar o armazenamento. Tente novamente.')
    } finally { controller.current = null; if (mounted.current) setBusy(false) }
  }

  return <div className="reportAction">
    <button className="secondary" disabled={!!receipt} onClick={() => setOpen(true)} aria-haspopup="dialog">{receipt ? 'Report enviado' : 'Reportar classificação'}</button>
    {receipt && <p role="status" className="small reportReceipt">Report enviado. O trecho e a análise foram armazenados para avaliação. <span>Identificador: {receipt.report_id}</span></p>}
    {open && createPortal(<dialog ref={dialog} className="reportDialog analysisContent" aria-labelledby={`${id}-title`} aria-describedby={`${id}-notice`}
      onKeyDown={keepFocus} onCancel={event => { event.preventDefault(); close() }} onClose={() => { setOpen(false); setConsent(false) }}>
      <h2 id={`${id}-title`} ref={heading} tabIndex={-1}>Reportar classificação</h2>
      <p className="muted small">Envie sua discordância para posterior avaliação pela equipe responsável.</p>
      <p id={`${id}-notice`} className="privacyNote"><strong>{REPORT_NOTICE}</strong></p>
      <details className="sourceDetails"><summary>Ver trecho que será armazenado</summary><p className="sourceText">{entry.text}</p></details>
      <details><summary>Ver análise que será armazenada</summary>
        <p className="small">A análise completa inclui eixos, evidências, trechos, avisos, modelos utilizados, versões e a configuração registrada.</p>
        <ul>{entry.analysis.axes.map(axis => <li key={axis.axis}>{AXES[axis.axis].title}: {axis.pole_a === null || axis.pole_b === null ? 'Sem estimativa' : `${AXES[axis.axis].a} ${axis.pole_a.toFixed(1)}% · ${AXES[axis.axis].b} ${axis.pole_b.toFixed(1)}%`}</li>)}</ul>
        <pre className="reportSnapshot">{JSON.stringify(entry.analysis, null, 2)}</pre>
      </details>
      <label htmlFor={`${id}-comment`}>Por que você discorda dessa classificação? <span className="muted small">(opcional)</span></label>
      <textarea id={`${id}-comment`} rows={3} value={comment} disabled={busy} onChange={event => setComment(event.target.value)} aria-describedby={`${id}-limit`} />
      <p id={`${id}-limit`} className={Array.from(comment).length > REPORT_COMMENT_LIMIT ? 'error small' : 'muted small'}>{Array.from(comment).length} de {REPORT_COMMENT_LIMIT} caracteres.</p>
      <label className="check reportConsent"><input type="checkbox" checked={consent} disabled={busy} onChange={event => setConsent(event.target.checked)} /><span>Estou ciente e concordo com o envio e o armazenamento desses dados.</span></label>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="actions"><button className="secondary" disabled={busy} onClick={close}>Cancelar</button><button disabled={busy || !consent || Array.from(comment).length > REPORT_COMMENT_LIMIT} onClick={() => void send()}>{busy ? 'Enviando…' : 'Enviar report'}</button></div>
      <p className="small muted" role="status" aria-live="polite">{busy ? 'Enviando o report e aguardando confirmação de armazenamento…' : ''}</p>
    </dialog>, document.body)}
  </div>
}
