import type { Axis } from '../domain/axes'
import { AXES, formatScore } from '../domain/axes'
import styles from '../styles/Cards.module.css'

export default function AxisBar({ axis, score, headingLevel = 3 }: { axis: Axis; score: number | null; headingLevel?: 3 | 4 }) {
  const item = AXES[axis]
  const Heading = headingLevel === 4 ? 'h4' : 'h3'
  const shownA = score === null ? null : Math.round((score + Number.EPSILON) * 10) / 10
  const shownB = shownA === null ? null : 100 - shownA
  return <div className={styles.axis}>
    <div className={styles.axisHeader}><Heading>{item.title}</Heading><span>{shownA === null ? 'Sem estimativa' : `${formatScore(shownA)} ${item.a} · ${formatScore(shownB!)} ${item.b}`}</span></div>
    <div className={styles.bar} role="img" aria-label={shownA === null ? `${item.title}: sem estimativa` : `${item.title}: ${formatScore(shownA)} em ${item.a} e ${formatScore(shownB!)} em ${item.b}`}>
      {score !== null && <div className={styles.fill} style={{ width: `${score}%` }} />}
    </div>
    <div className={styles.poles}><span>{item.a}</span><span>{item.b}</span></div>
    <p className="muted small">{item.explanation}</p>
  </div>
}
