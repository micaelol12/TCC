import { useState } from 'react'
import type { AnalysisEntry } from '../api/analysisApi'
import { modeLabels } from '../api/analysisApi'
import { configLabels, numericFields } from '../domain/experimentConfig'
import { AXES, axisOrder } from '../domain/axes'

export default function ExperimentComparison({ entry, entries }: { entry: AnalysisEntry<number | string>; entries: AnalysisEntry<number | string>[] }) {
  const [otherId, setOtherId] = useState('')
  const candidates = entries.filter(other => other.id !== entry.id && other.text === entry.text)
  const other = candidates.find(item => String(item.id) === otherId)
  const config = entry.analysis.effective_config
  return <section className="experimentComparison" aria-label="Comparar experimentos">
    <h3>Comparar experimentos</h3><p className="small muted">Selecione outra análise do mesmo texto. As respostas dos modelos podem variar entre execuções.</p>
    {candidates.length ? <><label htmlFor="lab-compare">Outra análise</label><select id="lab-compare" value={other?.id ?? ''} onChange={e => setOtherId(e.target.value)}><option value="">Selecione um resultado</option>{candidates.map(item => <option key={item.id} value={item.id}>{item.title} · {modeLabels[item.mode]} · {item.analysis.config_hash?.slice(0, 8) ?? 'configuração não registrada'}</option>)}</select></> : <p className="small">Reanalise este texto com outra configuração para comparar os resultados.</p>}
    {other && <>
      {(entry.mode !== other.mode || entry.analysis.models_used.join(',') !== other.analysis.models_used.join(',')) && <p className="notice small">As análises usam modos ou modelos diferentes.</p>}
      <div className="experimentTable"><table><caption>Resultado atual e outra análise</caption><thead><tr><th scope="col">Medida</th><th scope="col">Atual</th><th scope="col">Outra</th></tr></thead><tbody>
        <tr><th scope="row">Modo</th><td>{modeLabels[entry.mode]}</td><td>{modeLabels[other.mode]}</td></tr>
        <tr><th scope="row">Modelos retornados</th><td>{entry.analysis.models_used.join(', ')}</td><td>{other.analysis.models_used.join(', ')}</td></tr>
        <tr><th scope="row">Chamadas lógicas JEV / LLM</th><td>{entry.analysis.logical_calls.jev} / {entry.analysis.logical_calls.llm}</td><td>{other.analysis.logical_calls.jev} / {other.analysis.logical_calls.llm}</td></tr>
        {axisOrder.map(axis => { const a = entry.analysis.axes.find(item => item.axis === axis)!, b = other.analysis.axes.find(item => item.axis === axis)!
          const label = (value: typeof a) => `${value.pole_a === null ? 'Sem estimativa' : value.pole_a.toFixed(1)} · cobertura ${(value.coverage * 100).toFixed(0)}%`
          return <tr key={axis}><th scope="row">{AXES[axis].title} · polo A</th><td>{label(a)}</td><td>{label(b)}</td></tr>
        })}
        {[...numericFields, 'jev_model', 'llm_model'].map(name => <tr key={name}><th scope="row">{configLabels[name as keyof typeof configLabels]}</th><td>{config?.[name as keyof typeof configLabels] ?? 'Não registrada'}</td><td>{other.analysis.effective_config?.[name as keyof typeof configLabels] ?? 'Não registrada'}</td></tr>)}
      </tbody></table></div>
    </>}
  </section>
}
