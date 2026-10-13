import type { ReactNode } from 'react'
import { modeLabels, type AnalysisEntry } from '../api/analysisApi'
import { AXES, axisOrder } from '../domain/axes'
import type { Scores } from '../domain/quizScoring'
import AxisBar from './AxisBar'
import AnalysisRadar from './AnalysisRadar'
import IdeologyMatch from './IdeologyMatch'
import styles from '../styles/Cards.module.css'

export default function AnalysisResult({ entry, compact = false, children }: { entry: AnalysisEntry<number | string>; compact?: boolean; children?: ReactNode }) {
  const analysis = entry.analysis
  const scores = Object.fromEntries(analysis.axes.map(axis => [axis.axis, axis.pole_a])) as Scores
  const complete = axisOrder.every(axis => Number.isFinite(scores[axis]))
  return <section className={styles.card} aria-label="Análise selecionada">
    <div className="cardTop"><span className={styles.chip}>{modeLabels[analysis.processing_level]} · {analysis.models_used.join(', ') || 'Serviço externo'}</span><span className="muted small">{analysis.chunks.length} trechos</span></div>
    <h2>{entry.title}</h2>{entry.source && <p className="muted small sourceOrigin">Trecho selecionado em {entry.source}</p>}
    <p className="muted small">O resultado descreve somente o trecho enviado.</p>
    <details className="sourceDetails"><summary>Ver texto analisado</summary><p className="sourceText">{entry.text}</p></details>
    {analysis.warnings.length > 0 && <p className="notice">Há limitações nesta análise: {analysis.warnings.join(', ')}.</p>}
    {!compact && <AnalysisRadar analysis={analysis} />}
    <div className="sectionHeading detailHeading"><div><div className="eyebrow">Detalhamento</div><h3>Quatro eixos</h3></div></div>
    {axisOrder.map(axis => {
      const result = analysis.axes.find(item => item.axis === axis)
      return result ? <div key={axis}><AxisBar axis={axis} score={result.pole_a} headingLevel={4} />
        <details><summary>Distribuição e evidências de {AXES[axis].title}</summary>
          <p className="small muted">Cobertura: {result.valid_chunks} de {result.total_chunks} trechos. {result.sufficient_evidence ? '' : 'Evidência limitada.'} {result.status === 'abstained' ? 'Classificação indeterminada.' : result.status === 'no_evidence' ? 'Sem posição identificada.' : ''}</p>
          <p className="small">Níveis: −2: {result.level_counts.minus2}, −1: {result.level_counts.minus1}, 0: {result.level_counts.zero}, +1: {result.level_counts.plus1}, +2: {result.level_counts.plus2}.</p>
          {result.ci95 && <p className="small">Intervalo entre trechos (95%): {result.ci95[0].toFixed(1)}–{result.ci95[1].toFixed(1)}. Não representa probabilidade de acerto.</p>}
          {result.evidence.length ? <ul>{result.evidence.map((ev, i) => <li key={i}>Trecho {ev.chunk_index + 1}: “{ev.quote}”</li>)}</ul> : <p className="small muted">Sem citação literal disponível.{result.methods_used.includes('jev') && ' JEV classifica trechos sem devolver citações.'}</p>}
          {result.reason_codes.length > 0 && <p className="small muted">Motivos: {result.reason_codes.join(', ')}.</p>}
        </details></div> : <AxisBar key={axis} axis={axis} score={null} headingLevel={4} />
    })}
    {compact && <details><summary>Ver radar e detalhes gerais</summary><AnalysisRadar analysis={analysis} /></details>}
    {complete && <IdeologyMatch scores={scores} source="analysis" />}{children}
  </section>
}
