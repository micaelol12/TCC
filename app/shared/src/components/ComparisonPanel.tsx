import type { ReactNode } from 'react'
import { AXES, axisOrder, formatScore } from '../domain/axes'
import { compareAxis } from '../domain/compareAxes'
import type { Profile } from '../domain/profile'
import type { Analysis } from '../api/analysisApi'
import ComparisonRadar from './ComparisonRadar'
import styles from '../styles/Cards.module.css'

export default function ComparisonPanel({ profile, analysis, analysisTitle, profileAction }: { profile: Profile | null; analysis: Analysis | null; analysisTitle?: string; profileAction?: ReactNode }) {
  return <aside className={styles.card} aria-label="Comparação pessoal"><h2>Comparação</h2>
    {analysisTitle && <p className="small muted">Análise selecionada: <strong>{analysisTitle}</strong></p>}
    {!profile ? <><p className="muted">Adicione seu resultado do teste para comparar os quatro eixos.</p>{profileAction}</> : !analysis ? <p className="muted">Selecione uma análise para comparar os quatro eixos.</p> : <>
      <p className="muted small">Comparação descritiva na mesma escala. As duas medidas têm métodos diferentes; não há porcentagem global de compatibilidade.</p>
      <ComparisonRadar profile={profile} analysis={analysis} />
      {axisOrder.map(axis => {
        const result = analysis.axes.find(item => item.axis === axis)
        if (!result) return <p key={axis}>{AXES[axis].title}: sem base para comparar este eixo.</p>
        const comparison = compareAxis(profile.scores, result)
        return <div className="comparisonAxis" key={axis}><h3>{AXES[axis].title}</h3>
          {!comparison ? <p className="muted">Sem base para comparar este eixo.</p> : <>
            <div className="compareLine" role="img" aria-label={`Você: ${formatScore(profile.scores[axis])}; texto: ${formatScore(result.pole_a!)}`}><span className="youMarker" style={{ left: `${profile.scores[axis]}%` }} /><span className="textMarker" style={{ left: `${result.pole_a}%` }} /></div>
            <div className="legend"><span>● Você: {formatScore(profile.scores[axis])}</span><span>◆ Texto: {formatScore(result.pole_a!)}</span></div>
            <p className="small">Diferença de {formatScore(comparison.distance)} pontos; texto {comparison.direction}.</p>{!result.sufficient_evidence && <p className="small muted">Comparação exploratória — evidência limitada.</p>}
          </>}</div>
      })}</>}
  </aside>
}
