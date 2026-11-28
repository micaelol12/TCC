import { type Axis } from '../../domain/axes'
import type { ScaleLevel } from '../../domain/ordinalScale'
import { formatLevelName, formatProbability } from './evidenceFormatting'
import styles from '../../styles/Evidence.module.css'

/** Renderiza contagens ou probabilidades de cada nível com rótulos do eixo correspondente. */
export default function LevelDistribution({ axis, levels, values, unit, label, total = 1 }: { axis: Axis; levels: ScaleLevel[]; values: Record<string, number>; unit: 'count' | 'probability'; label: string; total?: number }) {
  return <ul className={styles.levelList} aria-label={label}>{levels.map(level => {
    const value = values[level.chave] ?? 0
    const proportion = value / Math.max(1, total)

    return <li key={level.chave}><span>{formatLevelName(level, axis)}</span><strong className={styles.levelValue}>
      <span aria-hidden="true" className={`${styles.levelFill} ${level.polo === 'A' ? styles.poleA : level.polo === 'B' ? styles.poleB : styles.poleNeutral}`} style={{ width: `${proportion * 100}%` }} />
      <span className={styles.levelText}><span>{formatProbability(proportion)}</span>{unit === 'count' && <small>{value} {value === 1 ? 'trecho' : 'trechos'}</small>}</span>
    </strong></li>
  })}</ul>
}
