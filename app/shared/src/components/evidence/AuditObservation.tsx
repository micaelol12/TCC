import type { EvidenceAudit } from '../../api/analysisApi'
import { formatLevelCode, formatProbability } from './evidenceFormatting'
import styles from '../../styles/Evidence.module.css'

const auditLabels: Record<EvidenceAudit['status'], string> = {
  found: 'Citação literal localizada', not_selected: 'Nenhuma passagem selecionada', not_literal: 'Citação literal inválida',
  sustenta: 'Sustenta a posição e intensidade', contradiz: 'Contradiz a posição atribuída', insuficiente: 'Evidência insuficiente',
  uncertain: 'Parecer empatado', failed: 'Falha ao consultar o verificador', invalid: 'Resposta inválida do verificador',
}

export default function AuditObservation({ audit, showQuote }: { audit: EvidenceAudit; showQuote: boolean }) {
  const tone = audit.status === 'sustenta' ? styles.supported : ['contradiz', 'insuficiente', 'not_literal', 'failed', 'invalid', 'uncertain'].includes(audit.status) ? styles.caution : styles.neutral
  return <div className={styles.audit}>
    <span className={styles.caption}>{audit.kind === 'search' ? 'Busca de citação' : 'Checagem semântica'} · nível {formatLevelCode(audit.level)}</span>
    <strong className={`${styles.badge} ${tone}`}>{auditLabels[audit.status]}</strong>
    {showQuote && audit.quote && <blockquote>{audit.quote}</blockquote>}
    <details><summary>Dados da verificação</summary><dl className={styles.facts}>
      {audit.sentence_id && <div><dt>Passagem</dt><dd>{audit.sentence_id} · caracteres {audit.start}–{audit.end}</dd></div>}
      {audit.existence_probability != null && <div><dt>Existência informada pelo JEV</dt><dd>{formatProbability(audit.existence_probability)}</dd></div>}
      {audit.confidence != null && <div><dt>Confiança do verificador</dt><dd>{formatProbability(audit.confidence)}</dd></div>}
      {audit.model && <div><dt>Modelo</dt><dd>{audit.model}</dd></div>}
    </dl><p className={styles.caption}>Parecer experimental; não altera a pontuação. Confiança não representa probabilidade de acerto.</p></details>
  </div>
}
