import { useRef } from 'react'
import { AXES, axisOrder } from '../../domain/axes'

export default function AxisGuide() {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)

  function open() {
    dialogRef.current?.showModal()
    closeRef.current?.focus()
  }

  return <>
    <button type="button" className="secondary axisGuideTrigger" onClick={open} aria-haspopup="dialog">Entenda os eixos</button>
    <dialog ref={dialogRef} className="axisGuideDialog" aria-labelledby="axis-guide-title" aria-describedby="axis-guide-intro">
      <div className="axisGuideHeader"><div><div className="eyebrow">Guia do teste</div><h2 id="axis-guide-title">Os quatro eixos do 8values</h2></div><button ref={closeRef} type="button" className="textButton" onClick={() => dialogRef.current?.close()}>Fechar</button></div>
      <p id="axis-guide-intro" className="muted">O teste mede oito valores em quatro eixos independentes. Cada resposta altera um pouco os percentuais dos polos opostos.</p>
      <div className="axisGuideList">{axisOrder.map(axis => <section key={axis} aria-label={`Eixo ${AXES[axis].title}`}><h3>{AXES[axis].title}</h3><dl><div><dt>{AXES[axis].a}</dt><dd>{AXES[axis].aDescription}</dd></div><div><dt>{AXES[axis].b}</dt><dd>{AXES[axis].bDescription}</dd></div></dl></section>)}</div>
      <p className="muted small">Descrições adaptadas do <a href="https://8values.github.io/">site oficial do 8values</a>.</p>
    </dialog>
  </>
}
