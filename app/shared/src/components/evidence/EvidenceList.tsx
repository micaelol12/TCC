import type { Analysis, AxisResult } from '../../api/analysisApi'
import AuditObservation from './AuditObservation'
import styles from '../../styles/Evidence.module.css'

/** Associa cada citação ao trecho original e às observações de auditoria disponíveis. */
export default function EvidenceList({ analysis, result }: { analysis: Analysis; result: AxisResult }) {
  const indices = [...new Set([...result.evidence.map(ev => ev.chunk_index), ...(result.evidence_audit ?? []).map(audit => audit.chunk_index)])].sort((a, b) => a - b)
  if (result.status === 'no_evidence' && !indices.length) return <p className={styles.help}>Não há evidências relevantes a exibir neste eixo.{result.jev_diagnostics?.length ? ' Consulte a avaliação por trecho na aba Modelo JEV.' : ''}</p>
  return <>
    <p className={styles.help}>Encontrar uma citação no texto e verificar se ela sustenta a classificação são etapas diferentes.</p>
    {indices.length ? <div className={styles.evidenceList}>{indices.map(index => {
      const evidence = result.evidence.filter(ev => ev.chunk_index === index)
      const audits = (result.evidence_audit ?? []).filter(audit => audit.chunk_index === index)
      const chunk = analysis.chunks.find(chunk => chunk.index === index)
      return <article key={index} className={styles.evidenceCard} aria-label={`Evidências do trecho ${index + 1}`}>
        <div className={styles.cardHeader}><h5>Trecho {index + 1}</h5>{evidence.length > 0 && <span className={`${styles.badge} ${styles.neutral}`}>Citação localizada</span>}</div>
        {evidence.map((ev, i) => <blockquote key={i}>“{ev.quote}”</blockquote>)}
        {!evidence.length && !audits.some(audit => audit.quote) && <p className={styles.caption}>Sem citação literal disponível para este trecho.</p>}
        {audits.length > 0 ? <div className={styles.auditList}>{audits.map((audit, i) => <AuditObservation key={i} audit={audit} showQuote={!!audit.quote && !evidence.some(ev => ev.quote === audit.quote) && audits.findIndex(item => item.quote === audit.quote) === i} />)}</div> : <p className={styles.caption}>Sem parecer semântico registrado. A presença literal não comprova apoio à classificação.</p>}
        {chunk && <details className={styles.context}><summary>Ver trecho completo</summary><p>{chunk.text}</p></details>}
      </article>
    })}</div> : <div className={styles.empty}><strong>Sem citação literal disponível.</strong><p>Consulte a distribuição{result.jev_diagnostics?.length ? ' e os detalhes do modelo' : ''} para entender os dados registrados neste eixo.</p></div>}
  </>
}
