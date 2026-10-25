import type { Axis } from '../domain/axes'
import { AXES, formatScore } from '../domain/axes'
import { interpretAxisScore } from '../domain/axisInterpretation'
import styles from '../styles/Cards.module.css'

export default function AxisBar({ axis, score, headingLevel = 3, showInterpretation = false }: { axis: Axis; score: number | null; headingLevel?: 3 | 4; showInterpretation?: boolean }) {
  const item = AXES[axis]
  const Heading = headingLevel === 4 ? 'h4' : 'h3'
  const shownA = score === null ? null : Math.round((score + Number.EPSILON) * 10) / 10
  const shownB = shownA === null ? null : 100 - shownA
  const interpretation = showInterpretation ? interpretAxisScore(axis, shownA) : null
  return <div className={styles.axis}>
    <div className={styles.axisHeader}><Heading>{item.title}</Heading>{shownA === null && <span>Sem estimativa</span>}</div>
    <div className={styles.poles}>
      <span className={shownA === null ? undefined : styles.poleA}>{item.a}{shownA !== null && <strong>{formatScore(shownA)}%</strong>}</span>
      <span className={shownB === null ? undefined : styles.poleB}>{shownB !== null && <strong>{formatScore(shownB)}%</strong>}{item.b}</span>
    </div>
    <div className={styles.bar} role="img" aria-label={shownA === null ? `${item.title}: sem estimativa` : `${item.title}: ${formatScore(shownA)}% em ${item.a} e ${formatScore(shownB!)}% em ${item.b}`}>
      {shownA !== null && <>
        <div className={styles.fillA} style={{ width: `${shownA}%` }} />
        <div className={styles.fillB} style={{ width: `${shownB}%` }} />
      </>}
    </div>
    {interpretation
      ? <p className="muted small"><strong>{interpretation.label}.</strong> {interpretation.description}</p>
      : <p className="muted small">{item.explanation}</p>}
  </div>
}
