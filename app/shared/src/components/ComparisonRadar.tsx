import { useId } from 'react'
import type { Analysis } from '../api/analysisApi'
import { AXES, axisOrder, formatScore } from '../domain/axes'
import type { Profile } from '../domain/profile'
import styles from '../styles/ComparisonRadar.module.css'

const center = 160
const radius = 100
function point(index: number, value: number) {
  const angle = index * Math.PI / 2 - Math.PI / 2
  const distance = radius * Math.max(0, Math.min(100, value)) / 100
  return { x: center + Math.cos(angle) * distance, y: center + Math.sin(angle) * distance }
}
const coordinates = (index: number, value: number) => {
  const { x, y } = point(index, value)
  return `${x},${y}`
}

export default function ComparisonRadar({ profile, analysis }: { profile: Profile; analysis: Analysis }) {
  const headingId = useId()
  const values = axisOrder.map(axis => analysis.axes.find(result => result.axis === axis)?.pole_a ?? null)
  const complete = values.every(value => value !== null)
  const description = axisOrder.map((axis, index) => `${AXES[axis].title} (${AXES[axis].a}): teste pessoal ${formatScore(profile.scores[axis])}; texto ${values[index] === null ? 'sem posição identificada' : formatScore(values[index])}`).join('; ')

  return <section className={styles.section} aria-labelledby={headingId}>
    <h3 id={headingId}>Radar comparativo</h3>
    <ul className={styles.legend} aria-label="Legenda do radar">
      <li><span className={styles.profileSwatch} aria-hidden="true" />Teste pessoal</li>
      <li><span className={styles.textSwatch} aria-hidden="true" />Texto analisado</li>
    </ul>
    <svg className={styles.chart} viewBox="0 0 320 320" role="img" aria-label={`Radar comparativo. ${description}`}>
      {[25, 50, 75, 100].map(level => <polygon key={level} className={styles.grid} points={axisOrder.map((_, index) => coordinates(index, level)).join(' ')} />)}
      {axisOrder.map((axis, index) => {
        const end = point(index, 100)
        const label = point(index, 131)
        return <g key={axis}>
          <line className={styles.spoke} x1={center} y1={center} x2={end.x} y2={end.y} />
          <text className={styles.label} x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle">{AXES[axis].a}</text>
        </g>
      })}
      {[25, 50, 75, 100].map(level => <text key={level} className={styles.tick} x={center + 5} y={center - radius * level / 100 + 4}>{level}</text>)}
      <polygon className={styles.profileArea} points={axisOrder.map((axis, index) => coordinates(index, profile.scores[axis])).join(' ')} />
      {complete && <polygon className={styles.textArea} points={values.map((value, index) => coordinates(index, value!)).join(' ')} />}
      {axisOrder.map((axis, index) => {
        const { x, y } = point(index, profile.scores[axis])
        return <circle key={axis} className={styles.profilePoint} cx={x} cy={y} r="4" />
      })}
      {values.map((value, index) => {
        if (value === null) return null
        const { x, y } = point(index, value)
        return <rect key={axisOrder[index]} className={styles.textPoint} x={x - 3.5} y={y - 3.5} width="7" height="7" transform={`rotate(45 ${x} ${y})`} />
      })}
    </svg>
    <p className="small muted">Escala de 0 a 100 para o primeiro polo de cada eixo: Igualdade, Globo, Liberdade e Progresso.</p>
    {!complete && <p className="small muted">Eixos sem posição no texto ficam sem ponto; a área do texto só aparece quando os quatro eixos têm resultado.</p>}
  </section>
}
