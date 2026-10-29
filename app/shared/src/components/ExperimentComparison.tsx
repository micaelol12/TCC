import { useState } from 'react'
import type { AnalysisEntry } from '../api/analysisApi'
import { modeLabels } from '../api/analysisApi'
import { configLabels, numericFields, evidenceFields, isLabBuild } from '../domain/experimentConfig'
import AnalysisComparisonChart from './AnalysisComparisonChart'

export default function ExperimentComparison({ entry, entries, initialOtherId }: { entry: AnalysisEntry<number | string>; entries: AnalysisEntry<number | string>[]; initialOtherId?: number | string | null }) {
  const [otherId, setOtherId] = useState(String(initialOtherId ?? ''))
  const candidates = entries.filter(other => String(other.id) !== String(entry.id))
  const other = candidates.find(item => String(item.id) === otherId)
  const config = entry.analysis.effective_config
  const configValue = (value: typeof config, name: string) => String(value?.[name as keyof NonNullable<typeof config>] ?? (value && name === 'primitiva_polaridade' ? 'score (padrão histórico)' : value && name === 'regra_decisao' ? 'nivel (padrão histórico)' : value && name === 'chunk_strategy' ? 'tokens (padrão histórico)' : 'Não registrada'))
  return <section className="experimentComparison" aria-label="Comparar análises">
    <h2>Comparar análises</h2><p className="small muted">Análise selecionada: <strong>{entry.title}</strong></p><p className="small muted">Selecione qualquer outra análise do histórico, do mesmo texto ou de textos diferentes. As respostas dos modelos podem variar entre execuções.</p>
    {candidates.length ? <><label htmlFor="analysis-compare">Outra análise</label><select id="analysis-compare" value={other?.id ?? ''} onChange={e => setOtherId(e.target.value)}><option value="">Selecione um resultado</option>{candidates.map(item => <option key={item.id} value={item.id}>{item.title} · {modeLabels[item.mode]}{isLabBuild ? ` · ${item.analysis.config_hash?.slice(0, 8) ?? 'configuração não registrada'}` : ''}</option>)}</select></> : <p className="small">Faça outra análise para comparar os resultados do histórico.</p>}
    {other && <>
      {(entry.mode !== other.mode || entry.analysis.models_used.join(',') !== other.analysis.models_used.join(',')) && <p className="notice small">As análises usam modos ou modelos diferentes.</p>}
      <AnalysisComparisonChart entry={entry} other={other} />
      {isLabBuild && <div className="experimentTable"><table><caption>Configurações utilizadas</caption><thead><tr><th scope="col">Parâmetro</th><th scope="col">Atual · {entry.title}</th><th scope="col">Outra · {other.title}</th></tr></thead><tbody>
        <tr><th scope="row">Modo</th><td>{modeLabels[entry.mode]}</td><td>{modeLabels[other.mode]}</td></tr>
        <tr><th scope="row">Modelos retornados</th><td>{entry.analysis.models_used.join(', ')}</td><td>{other.analysis.models_used.join(', ')}</td></tr>
        <tr><th scope="row">Escala utilizada</th><td>{entry.analysis.escala?.id ?? `Histórica ${entry.analysis.schema_version === '1' ? 5 : 9} níveis`} · {entry.analysis.escala_hash?.slice(0, 12)}</td><td>{other.analysis.escala?.id ?? `Histórica ${other.analysis.schema_version === '1' ? 5 : 9} níveis`} · {other.analysis.escala_hash?.slice(0, 12)}</td></tr>
        <tr><th scope="row">Chamadas lógicas JEV / LLM</th><td>{entry.analysis.logical_calls.jev} / {entry.analysis.logical_calls.llm}</td><td>{other.analysis.logical_calls.jev} / {other.analysis.logical_calls.llm}</td></tr>
        <tr><th scope="row">Identificador da configuração</th><td>{entry.analysis.config_hash ?? 'Não registrada'}</td><td>{other.analysis.config_hash ?? 'Não registrada'}</td></tr>
        {[...numericFields, ...evidenceFields, 'jev_model', 'llm_model', 'primitiva_polaridade', 'regra_decisao', 'chunk_strategy'].map(name => <tr key={name}><th scope="row">{configLabels[name as keyof typeof configLabels]}</th><td>{configValue(config, name)}</td><td>{configValue(other.analysis.effective_config, name)}</td></tr>)}
      </tbody></table></div>}
    </>}
  </section>
}
