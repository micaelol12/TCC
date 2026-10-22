import { AXES, axisOrder, formatScore } from '../domain/axes'
import type { Analysis } from '../api/analysisApi'

const center = 120
const radius = 86
const point = (index: number, value: number) => {
  const angle = index * Math.PI / 2 - Math.PI / 2
  const distance = radius * Math.max(0, Math.min(100, value)) / 100
  return `${center + Math.cos(angle) * distance},${center + Math.sin(angle) * distance}`
}

export default function AnalysisRadar({ analysis }: { analysis: Analysis }) {
  const results = axisOrder.map(axis => analysis.axes.find(result => result.axis === axis))
  const available = results.map((result, index) => result?.pole_a == null ? null : { index, value: result.pole_a })
  const complete = available.every(Boolean)
  const description = axisOrder.map((axis, index) => {
    const value = results[index]?.pole_a
    return `${AXES[axis].title}: ${value == null ? 'sem posição identificada' : `${formatScore(value)}% ${AXES[axis].a}`}`
  }).join('; ')

  return <section className="radarSection" aria-labelledby="radar-heading">
    <div className="sectionHeading"><div><div className="eyebrow">Visão geral</div><h3 id="radar-heading">Posições do texto</h3></div><span className="muted small">Escala de 0 a 100</span></div>
    <div className="radarLayout">
      <svg className="radarChart" viewBox="0 0 240 240" role="img" aria-label={description}>
        {[25, 50, 75, 100].map(level => <polygon key={level} className="radarGrid" points={axisOrder.map((_, index) => point(index, level)).join(' ')} />)}
        {axisOrder.map((axis, index) => <line key={axis} className="radarSpoke" x1={center} y1={center} x2={point(index, 100).split(',')[0]} y2={point(index, 100).split(',')[1]} />)}
        {complete && <polygon className="radarArea" points={available.map(item => point(item!.index, item!.value)).join(' ')} />}
        {available.filter(item => item !== null).map(item => <circle key={item.index} className="radarPoint" cx={point(item.index, item.value).split(',')[0]} cy={point(item.index, item.value).split(',')[1]} r="4" />)}
      </svg>
      <div className="radarLegend">
        {axisOrder.map((axis, index) => {
          const result = results[index]
          return <div className="radarLegendRow" key={axis}><strong>{AXES[axis].title}</strong><span>{result?.pole_a == null || result.pole_b == null ? 'Sem posição identificada' : `${AXES[axis].a} ${formatScore(result.pole_a)} · ${AXES[axis].b} ${formatScore(result.pole_b)}`}</span></div>
        })}
        <p className="muted small">Os pontos mostram o primeiro polo de cada eixo. Eixos sem posição não formam área no gráfico.</p>
      </div>
    </div>
  </section>
}
