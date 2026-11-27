import { useId, useState, type KeyboardEvent } from 'react'
import type { Analysis } from '../api/analysisApi'
import { AXES, axisOrder, type Axis } from '../domain/axes'
import { historicalLevels } from '../domain/ordinalScale'
import styles from '../styles/Evidence.module.css'
import { describeAnalysisReason } from '../domain/analysisMessages'
import EvidenceList from './evidence/EvidenceList'
import FinalLevelDistribution from './evidence/FinalLevelDistribution'
import JevModelDiagnostic from './evidence/JevModelDiagnostic'

type View = 'evidence' | 'distribution' | 'model'

export default function AnalysisEvidence({ analysis }: { analysis: Analysis }) {
  const id = useId()
  const [axis, setAxis] = useState<Axis>('economic')
  const [view, setView] = useState<View>('evidence')
  const [chunkIndex, setChunkIndex] = useState<number | null>(null)
  const result = analysis.axes.find(item => item.axis === axis)
  const levels = analysis.escala?.niveis ?? historicalLevels(analysis.schema_version)
  const tabs: { key: View; label: string }[] = [{ key: 'evidence', label: 'Evidências' }, { key: 'distribution', label: 'Distribuição' }, ...(result?.jev_diagnostics?.length ? [{ key: 'model' as const, label: 'Modelo JEV' }] : [])]
  const activeView = tabs.some(tab => tab.key === view) ? view : 'evidence'
  const diagnostic = result?.jev_diagnostics?.find(d => d.chunk_index === chunkIndex) ?? result?.jev_diagnostics?.[0]
  const limited = result?.status === 'estimated' && result.valid_chunks > 0 && !result.sufficient_evidence
  const minimum = analysis.effective_config?.min_valid_chunks
  function navigateTabs(event: KeyboardEvent<HTMLButtonElement>) {
    const offset = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    if (!offset && event.key !== 'Home' && event.key !== 'End') return
    event.preventDefault()
    const index = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (tabs.findIndex(tab => tab.key === activeView) + offset + tabs.length) % tabs.length
    setView(tabs[index].key)
    document.getElementById(`${id}-${tabs[index].key}-tab`)?.focus()
  }
  return <section className={styles.explorer} aria-label="Distribuição e evidências">
    <div className={styles.heading}><div className="eyebrow">Entenda o resultado</div><h3>Distribuição e evidências</h3><p className={styles.help}>Escolha um eixo para conferir as citações e os dados que explicam a análise.</p></div>
    <div className={styles.axisPicker} role="group" aria-label="Eixo das evidências">{axisOrder.map(item => {
      const status = analysis.axes.find(result => result.axis === item)?.status
      const statusLabel = status === 'no_evidence' ? 'Sem relevância' : status === 'abstained' ? 'Indeterminado' : null
      return <button key={item} type="button" className={`secondary ${styles.axisButton}`} aria-label={AXES[item].title} aria-describedby={statusLabel ? `${id}-${item}-status` : undefined} aria-pressed={axis === item} onClick={() => { setAxis(item); setView('evidence'); setChunkIndex(null) }}><span>{AXES[item].title}</span>{statusLabel && <small id={`${id}-${item}-status`}>{statusLabel}</small>}</button>
    })}</div>
    {result ? <>
      <div className={styles.coverage}><strong>{AXES[axis].title}</strong><span>Cobertura: {result.valid_chunks} de {result.total_chunks} trechos válidos</span>{limited && <span className={`${styles.badge} ${styles.caution}`}>Poucos trechos válidos</span>}</div>
      {result.status === 'no_evidence' && <div className={styles.statusNotice}><strong>Sem relevância neste eixo</strong><p>Nenhum trecho analisado foi considerado relevante para o eixo {AXES[axis].title.toLocaleLowerCase('pt-BR')}. Não há pontuação a atribuir; isso não significa uma posição neutra.</p></div>}
      {result.status === 'abstained' && <div className={`${styles.statusNotice} ${styles.caution}`}><strong>Classificação indeterminada</strong><p>A análise não conseguiu obter uma estimativa válida para este eixo. Este estado é diferente de um eixo sem relevância e de uma posição neutra.</p></div>}
      {limited && <p className={styles.help}>{result.valid_chunks === 1 ? 'Há 1 trecho válido' : `Há ${result.valid_chunks} trechos válidos`} neste eixo.{minimum !== undefined ? ` O mínimo configurado nesta análise é ${minimum}.` : ' A quantidade ficou abaixo do mínimo exigido, cujo valor não foi registrado nesta análise.'} O aviso se refere à quantidade de trechos usados na estimativa.</p>}
      {result.reason_codes.includes('intensidade_ambigua') && !result.methods_used.includes('llm') && <p className="notice small">Intensidade incerta no JEV: houve empate ou suporte abaixo do limiar em pelo menos um trecho. Sem revisão pelo LLM, a pontuação é preliminar.{result.jev_diagnostics?.length ? ' Confira a aba Modelo JEV.' : ' Diagnósticos por trecho não registrados nesta análise.'}</p>}
      {result.reason_codes.includes('direcao_ambigua') && analysis.effective_config?.regra_decisao === 'polo_primeiro' && !result.methods_used.includes('llm') && <p className="notice small">Direção incerta no JEV. Os grupos estão próximos; a pontuação é preliminar.</p>}
      <div className={styles.tabs} role="tablist" aria-label={`Detalhamento de ${AXES[axis].title}`}>{tabs.map(tab => <button key={tab.key} type="button" id={`${id}-${tab.key}-tab`} role="tab" aria-selected={activeView === tab.key} aria-controls={`${id}-panel`} tabIndex={activeView === tab.key ? 0 : -1} className={`secondary ${styles.tab}`} onClick={() => setView(tab.key)} onKeyDown={navigateTabs}>{tab.label}</button>)}</div>
      <div id={`${id}-panel`} role="tabpanel" aria-labelledby={`${id}-${activeView}-tab`} className={styles.content}>
        {activeView === 'evidence' && <EvidenceList analysis={analysis} result={result} />}
        {activeView === 'distribution' && <FinalLevelDistribution analysis={analysis} result={result} levels={levels} />}
        {activeView === 'model' && diagnostic && <>
          <p className={styles.help}>Valores do JEV antes de eventual revisão pelo LLM. Não são percentuais ideológicos nem probabilidades de acerto.</p>
          <label className={styles.chunkLabel} htmlFor={`${id}-chunk`}>Examinar trecho</label><select className={styles.chunkSelect} id={`${id}-chunk`} value={diagnostic.chunk_index} onChange={event => setChunkIndex(Number(event.target.value))}>{result.jev_diagnostics!.map(d => <option key={d.chunk_index} value={d.chunk_index}>Trecho {d.chunk_index + 1}{!d.relevante ? ' · sem relevância' : ''}</option>)}</select>
          <details className={styles.context}><summary>Ver texto deste trecho</summary><p>{analysis.chunks.find(chunk => chunk.index === diagnostic.chunk_index)?.text}</p></details>
          <JevModelDiagnostic diagnostic={diagnostic} analysis={analysis} axis={axis} levels={levels} />
        </>}
      </div>
      {result.reason_codes.length > 0 && <details className={styles.reasons}><summary>Motivos registrados na análise</summary><ul>{[...new Set(result.reason_codes.map(describeAnalysisReason))].map(message => <li key={message}>{message}</li>)}</ul>
        <details><summary>Códigos para suporte técnico</summary><ul>{result.reason_codes.map(reason => <li key={reason}><code>{reason}</code></li>)}</ul></details>
      </details>}
    </> : <p className={styles.empty}>Sem dados registrados para este eixo.</p>}
  </section>
}
