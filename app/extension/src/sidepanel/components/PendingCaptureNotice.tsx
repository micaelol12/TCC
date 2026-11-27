import type { Capture } from '../../platform/selection'

type PendingCaptureNoticeProps = {
  capture: Capture
  busy: boolean
  onUseCapture: () => void
  onKeepDraft: () => void
}

export default function PendingCaptureNotice({ capture, busy, onUseCapture, onKeepDraft }: PendingCaptureNoticeProps) {
  return <section className="notice" aria-label="Nova seleção"><strong>Você selecionou outro trecho.</strong><p className="pendingPreview">{capture.text.slice(0, 180)}{capture.text.length > 180 ? '…' : ''}</p><div className="actions"><button disabled={busy} onClick={onUseCapture}>Usar nova seleção</button><button className="secondary" onClick={onKeepDraft}>Manter rascunho</button></div>{busy && <p className="small">A análise em andamento mantém o trecho anterior.</p>}</section>
}
