import type { Axis } from '../domain/axes'
import { AXES, formatScore } from '../domain/axes'
import styles from '../styles/Cards.module.css'

export default function AxisBar({ axis, score, headingLevel = 3 }: { axis: Axis; score: number | null; headingLevel?: 3 | 4 }) {
  const item = AXES[axis]
  const Heading = headingLevel === 4 ? 'h4' : 'h3'
  const shownA = score === null ? null : Math.round((score + Number.EPSILON) * 10) / 10
  const shownB = shownA === null ? null : 100 - shownA
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
    <p className="muted small">{item.explanation}</p>
  </div>
}
