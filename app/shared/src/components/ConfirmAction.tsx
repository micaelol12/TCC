import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

type Props = {
  label: string; title: string; description: string; confirmLabel: string;
  onConfirm: () => void | Promise<void>; disabled?: boolean; className?: string
}

/** Keep destructive actions behind an explicit, keyboard-accessible choice. */
export default function ConfirmAction({ label, title, description, confirmLabel, onConfirm, disabled, className = 'danger' }: Props) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  const cancel = useRef<HTMLButtonElement>(null)
  const pending = useRef(false)
  const mounted = useRef(true)
  const id = useId()
  useEffect(() => { mounted.current = true; return () => { mounted.current = false } }, [])
  useEffect(() => {
    if (open && dialog.current && !dialog.current.open) { dialog.current.showModal(); cancel.current?.focus() }
  }, [open])
  function close() {
    if (pending.current) return
    dialog.current?.close(); setOpen(false); trigger.current?.focus()
  }
  async function confirm() {
    if (pending.current || disabled) return
    pending.current = true; setBusy(true); setError('')
    try {
      await onConfirm()
      if (mounted.current) { dialog.current?.close(); setOpen(false); trigger.current?.focus() }
    } catch (err) {
      if (mounted.current) setError(err instanceof Error ? err.message : 'Não foi possível concluir. Tente novamente.')
    } finally {
      pending.current = false
      if (mounted.current) setBusy(false)
    }
  }
  return <>
    <button ref={trigger} type="button" className={className} disabled={disabled} aria-haspopup="dialog" onClick={() => { setError(''); setOpen(true) }}>{label}</button>
    {open && createPortal(<dialog ref={dialog} className="confirmDialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`}
      onCancel={event => { event.preventDefault(); close() }} onClose={() => setOpen(false)}>
      <h2 id={`${id}-title`}>{title}</h2><p id={`${id}-description`}>{description}</p>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="actions"><button ref={cancel} type="button" className="secondary" disabled={busy} onClick={close}>Cancelar</button><button type="button" className="danger" disabled={busy || disabled} onClick={() => void confirm()}>{busy ? 'Aguarde…' : confirmLabel}</button></div>
    </dialog>, document.body)}
  </>
}
