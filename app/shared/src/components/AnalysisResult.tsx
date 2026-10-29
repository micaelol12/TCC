import type { ReactNode } from 'react'
import { modeLabels, type AnalysisEntry } from '../api/analysisApi'
import { axisOrder } from '../domain/axes'
import type { Scores } from '../domain/quizScoring'
import AxisBar from './AxisBar'
import AnalysisRadar from './AnalysisRadar'
import IdeologyMatch from './IdeologyMatch'
import styles from '../styles/Cards.module.css'
import ReportDialog from './ReportDialog'
import type { ReportClient, ReportRequest } from '../api/reportApi'
import AnalysisEvidence from './AnalysisEvidence'
import { isLabBuild } from '../domain/experimentConfig'
import { describeAnalysisReason } from '../domain/analysisMessages'

export default function AnalysisResult({ entry, reportClient, reportOrigin, compact = false, children }: { entry: AnalysisEntry<number | string>; reportClient: ReportClient; reportOrigin: ReportRequest['client']; compact?: boolean; children?: ReactNode }) {
  const analysis = entry.analysis
  const scores = Object.fromEntries(analysis.axes.map(axis => [axis.axis, axis.pole_a])) as Scores
  const complete = axisOrder.every(axis => Number.isFinite(scores[axis]))
  return <section className={styles.card} aria-label="Análise selecionada">
    <div className="cardTop"><span className={styles.chip}>{modeLabels[analysis.processing_level]} · {analysis.models_used.join(', ') || 'Serviço externo'}</span><span className="muted small">{analysis.chunks.length} trechos</span></div>
    <h2>{entry.title}</h2>{entry.source && <p className="muted small sourceOrigin">Trecho selecionado em {entry.source}</p>}
    <p className="muted small">O resultado descreve somente o trecho enviado.</p>
    <p className="muted small">Escala de classificação: {analysis.escala?.niveis.length ?? (analysis.schema_version === '1' ? 5 : 9)} níveis de posição política.</p>
    {analysis.escala && <details><summary>Identificação técnica da escala</summary><p className="small">{analysis.escala.id} · versão {analysis.escala.versao}</p></details>}
    {isLabBuild && analysis.lab_execution_id && <p className="small configHash" role="status">Execução gravada no banco: {analysis.lab_execution_id}</p>}
    <details className="sourceDetails"><summary>Ver texto analisado</summary><p className="sourceText">{entry.text}</p></details>
    {isLabBuild && (analysis.effective_config ? <details className="experimentSnapshot"><summary>Configuração utilizada{analysis.environment === 'lab' ? ' · versão de teste' : ''}</summary>
      <p className="small muted">Ambiente: {analysis.environment}. Pipeline: {analysis.pipeline_version}. Configuração v{analysis.config_version}.</p>
      <pre className="reportSnapshot">{JSON.stringify(analysis.effective_config, null, 2)}</pre><p className="small configHash">Identificador: {analysis.config_hash}</p>
    </details> : <p className="muted small">Configuração não registrada nesta análise.</p>)}
    {analysis.warnings.length > 0 && <div className="notice"><strong>Limitações desta análise</strong><ul>{[...new Set(analysis.warnings.map(describeAnalysisReason))].map(message => <li key={message}>{message}</li>)}</ul></div>}
    {!compact && <AnalysisRadar analysis={analysis} />}
    <div className="sectionHeading detailHeading"><div><div className="eyebrow">Detalhamento</div><h3>Quatro eixos</h3></div></div>
    {axisOrder.map(axis => {
      const result = analysis.axes.find(item => item.axis === axis)
      return <div key={axis}><AxisBar axis={axis} score={result?.pole_a ?? null} status={result?.status} headingLevel={4} showInterpretation />
        {result && !result.methods_used.includes('llm') && (result.reason_codes.includes('intensidade_ambigua') || result.reason_codes.includes('direcao_ambigua')) && <p className="notice small">Pontuação preliminar: o classificador teve incerteza sobre a direção ou intensidade da posição. Consulte este eixo em Distribuição e evidências.</p>}
      </div>
    })}
    <AnalysisEvidence key={entry.id} analysis={analysis} />
    {compact && <details><summary>Ver radar e detalhes gerais</summary><AnalysisRadar analysis={analysis} /></details>}
    {complete && <IdeologyMatch scores={scores} source="analysis" />}
    <ReportDialog key={entry.id} entry={entry} client={reportClient} origin={reportOrigin} />{children}
  </section>
}
