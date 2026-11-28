import type { Capture } from '../../platform/selection'
import Actions from '@8values/shared/components/Actions'
import Button from '@8values/shared/components/Button'

type PendingCaptureNoticeProps = {
  capture: Capture
  busy: boolean
  onUseCapture: () => void
  onKeepDraft: () => void
}

/** Permite usar ou ignorar uma seleção recebida enquanto já existe um rascunho. */
export default function PendingCaptureNotice({ capture, busy, onUseCapture, onKeepDraft }: PendingCaptureNoticeProps) {
  return <section className="notice" aria-label="Nova seleção"><strong>Você selecionou outro trecho.</strong><p className="pendingPreview">{capture.text.slice(0, 180)}{capture.text.length > 180 ? '…' : ''}</p><Actions><Button disabled={busy} onClick={onUseCapture}>Usar nova seleção</Button><Button variant="secondary" onClick={onKeepDraft}>Manter rascunho</Button></Actions>{busy && <p className="small">A análise em andamento mantém o trecho anterior.</p>}</section>
}
