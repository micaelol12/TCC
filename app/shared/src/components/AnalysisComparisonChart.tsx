import { useId } from 'react'
import type { AnalysisEntry, AxisResult } from '../api/analysisApi'
import { AXES, axisOrder, formatScore } from '../domain/axes'
import styles from '../styles/AnalysisComparisonChart.module.css'

type Entry = AnalysisEntry<number | string>
const position = (value: number) => 14 + Math.max(0, Math.min(100, value)) * 3.12
const scoreLabel = (result?: AxisResult) => result?.pole_a == null ? 'Sem estimativa' : formatScore(result.pole_a)

function ResultLabel({ result, title, symbol }: { result?: AxisResult; title: string; symbol: string }) {
  return <div className={styles.result}>
    <span>{symbol} {title}: <strong>{scoreLabel(result)}</strong></span>
    {result && <span className={styles.coverage}>Cobertura {(result.coverage * 100).toFixed(0)}%{result.pole_a !== null && !result.sufficient_evidence ? ' · evidência limitada' : ''}</span>}
  </div>
}

export default function AnalysisComparisonChart({ entry, other }: { entry: Entry; other: Entry }) {
  const headingId = useId()
  return <section className={styles.summary} aria-labelledby={headingId}>
    <h3 id={headingId}>Resumo comparativo dos resultados</h3>
    <ul className={styles.legend} aria-label="Legenda do gráfico">
      <li><span className={styles.currentSwatch} aria-hidden="true" />Atual · {entry.title}</li>
      <li><span className={styles.otherSwatch} aria-hidden="true" />Outra · {other.title}</li>
    </ul>
    <p className="small muted">Cada gráfico mostra as duas posições na escala de 0 a 100 do primeiro polo. Pontos mais próximos indicam resultados mais semelhantes. Eixos sem estimativa ficam sem marcador.</p>
    <div className={styles.axes}>
      {axisOrder.map(axis => {
        const a = entry.analysis.axes.find(result => result.axis === axis)
        const b = other.analysis.axes.find(result => result.axis === axis)
        const delta = a?.pole_a != null && b?.pole_a != null ? Math.abs(a.pole_a - b.pole_a) : null
        return <div className={styles.axis} key={axis}>
          <div className={styles.heading}><h4>{AXES[axis].title}</h4><span>{delta === null ? 'Sem base para comparar' : `Diferença de ${formatScore(delta)} pontos`}</span></div>
          <svg className={styles.chart} viewBox="0 0 340 83" role="img" aria-label={`${AXES[axis].title} · ${AXES[axis].a}: ${entry.title}, ${scoreLabel(a)}; ${other.title}, ${scoreLabel(b)}. ${delta === null ? 'Sem base para comparar.' : `Diferença de ${formatScore(delta)} pontos.`}`}>
            {[0, 25, 50, 75, 100].map(value => <g key={value}>
              <line className={styles.grid} x1={position(value)} x2={position(value)} y1="25" y2="67" />
              <text className={styles.tick} x={position(value)} y="16" textAnchor="middle">{value}</text>
            </g>)}
            <line className={styles.track} x1="14" x2="326" y1="46" y2="46" />
            {a?.pole_a != null && b?.pole_a != null && <line className={styles.connector} x1={position(a.pole_a)} y1="38" x2={position(b.pole_a)} y2="54" />}
            {a?.pole_a != null && <circle className={styles.currentPoint} cx={position(a.pole_a)} cy="38" r="6"><title>{entry.title}: {formatScore(a.pole_a)}</title></circle>}
            {b?.pole_a != null && <rect className={styles.otherPoint} x={position(b.pole_a) - 5} y="49" width="10" height="10" transform={`rotate(45 ${position(b.pole_a)} 54)`}><title>{other.title}: {formatScore(b.pole_a)}</title></rect>}
          </svg>
          <div className={styles.poles}><span>{AXES[axis].b}</span><span>{AXES[axis].a}</span></div>
          <div className={styles.values}><ResultLabel result={a} title="Atual" symbol="●" /><ResultLabel result={b} title="Outra" symbol="◆" /></div>
        </div>
      })}
    </div>
    <p className="small muted">Comparação descritiva por eixo, sem porcentagem global de compatibilidade.</p>
  </section>
}
