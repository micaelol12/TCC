import type { ExperimentFieldProps } from './experimentFieldTypes'

/** Edita busca de citações, checagem semântica e o limiar de existência de evidência. */
export default function ExperimentEvidenceFields({ config, mode, busy, onChange }: ExperimentFieldProps) {
  return <fieldset disabled={busy}><legend>Evidências experimentais</legend>
      <label><input id="lab-semantic_evidence_check" type="checkbox" checked={config.semantic_evidence_check ?? false} onChange={e => onChange({ ...config, semantic_evidence_check: e.target.checked })} /> Verificar apoio semântico da citação</label>
      <p className="small muted">O JEV avalia se a citação sustenta, contradiz ou não comprova a posição e sua intensidade. O parecer fica registrado e não altera a pontuação. Exige TypeSafe também no modo alto.</p>
      <label><input id="lab-jev_evidence_search" type="checkbox" checked={config.jev_evidence_search ?? false} disabled={mode === 'high'} onChange={e => onChange({ ...config, jev_evidence_search: e.target.checked })} /> Buscar citações do JEV por ID</label>
      <p className="small muted">Nos modos baixo e médio, procura uma passagem original para cada decisão final do JEV. Só apresenta a citação quando o teste de existência passa. A média continua usando todos os trechos válidos.</p>
      <label htmlFor="lab-evidence_existence_min">Limiar de existência de evidência</label>
      <input id="lab-evidence_existence_min" type="number" min="0" max="1" step="0.01" value={Number.isFinite(config.evidence_existence_min ?? 0.7) ? (config.evidence_existence_min ?? 0.7) : ''} disabled={!config.jev_evidence_search || mode === 'high'} onChange={e => onChange({ ...config, evidence_existence_min: e.target.value === '' ? NaN : Number(e.target.value) })} />
      <p className="small muted">Até duas chamadas JEV adicionais por trecho com as duas opções ativas. Confiança do modelo não é probabilidade de acerto.</p>
    </fieldset>
}
