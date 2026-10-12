import { Link } from 'react-router-dom'
import { AXES, axisOrder, formatScore } from '../../domain/axes'
import { compareAxis } from '../../domain/compareAxes'
import type { Profile } from '../../storage/localProfile'
import type { Analysis } from '../../services/analysisApi'
import styles from '../../components/Cards.module.css'

export default function ComparisonPanel({ profile, analysis }: { profile: Profile | null; analysis: Analysis | null }) {
  return <aside className={styles.card} aria-label="Comparação pessoal">
    <h2>Comparação</h2>
    {!profile ? <><p className="muted">Faça o teste para comparar seus valores com o texto.</p><Link to="/teste" className="button">Fazer meu teste</Link></> : !analysis ? <p className="muted">Selecione uma análise para comparar os quatro eixos.</p> : <>
      <p className="muted small">Comparação descritiva na mesma escala. As duas medidas têm métodos diferentes; não há porcentagem global de compatibilidade.</p>
      {axisOrder.map(axis => {
        const result = analysis.axes.find(item => item.axis === axis)
        if (!result) return <p key={axis}>{AXES[axis].title}: sem base para comparar este eixo.</p>
        const comparison = compareAxis(profile.scores, result)
        return <div className="comparisonAxis" key={axis}>
          <h3>{AXES[axis].title}</h3>
          {!comparison ? <p className="muted">Sem base para comparar este eixo.</p> : <>
            <div className="compareLine" role="img" aria-label={`Você: ${formatScore(profile.scores[axis])}; texto: ${formatScore(result.pole_a!)}`}>
              <span className="youMarker" style={{ left: `${profile.scores[axis]}%` }} /><span className="textMarker" style={{ left: `${result.pole_a}%` }} />
            </div>
            <div className="legend"><span>● Você: {formatScore(profile.scores[axis])}</span><span>◆ Texto: {formatScore(result.pole_a!)}</span></div>
            <p className="small">Diferença de {formatScore(comparison.distance)} pontos; texto {comparison.direction}.</p>
            {!result.sufficient_evidence && <p className="small muted">Comparação exploratória — evidência limitada.</p>}
          </>}
        </div>
      })}
    </>}
  </aside>
}
