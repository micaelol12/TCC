import { useId, useState, type KeyboardEvent } from 'react'
import type { Analysis, AxisResult, EvidenceAudit, JevDiagnostic } from '../api/analysisApi'
import { AXES, axisOrder, type Axis } from '../domain/axes'
import { historicalLevels, type ScaleLevel } from '../domain/ordinalScale'
import styles from '../styles/Evidence.module.css'

const percent = (value: number) => `${(value * 100).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`
const code = (value: number) => `${value > 0 ? '+' : ''}${value}`
const auditLabels: Record<EvidenceAudit['status'], string> = {
  found: 'Citação literal localizada', not_selected: 'Nenhuma passagem selecionada', not_literal: 'Citação literal inválida',
  sustenta: 'Sustenta a posição e intensidade', contradiz: 'Contradiz a posição atribuída', insuficiente: 'Evidência insuficiente',
  uncertain: 'Parecer empatado', failed: 'Falha ao consultar o verificador', invalid: 'Resposta inválida do verificador',
}
type View = 'evidence' | 'distribution' | 'model'

function levelName(level: ScaleLevel, axis: Axis) {
  const pole = level.polo === 'A' ? AXES[axis].a : level.polo === 'B' ? AXES[axis].b : 'Sem posição'
  const label = level.rotulo === String(level.codigo) ? pole : level.rotulo.replace(/polo A/gi, AXES[axis].a).replace(/polo B/gi, AXES[axis].b)
  return `${code(level.codigo)} · ${label}`
}

function LevelDistribution({ axis, levels, values, unit, label, total = 1 }: { axis: Axis; levels: ScaleLevel[]; values: Record<string, number>; unit: 'count' | 'probability'; label: string; total?: number }) {
  return <ul className={styles.levelList} aria-label={label}>{levels.map(level => {
    const value = values[level.chave] ?? 0
    const proportion = value / Math.max(1, total)
    return <li key={level.chave}><span>{levelName(level, axis)}</span><strong className={styles.levelValue}>
      <span aria-hidden="true" className={`${styles.levelFill} ${level.polo === 'A' ? styles.poleA : level.polo === 'B' ? styles.poleB : styles.poleNeutral}`} style={{ width: `${proportion * 100}%` }} />
      <span className={styles.levelText}><span>{percent(proportion)}</span>{unit === 'count' && <small>{value} {value === 1 ? 'trecho' : 'trechos'}</small>}</span>
    </strong></li>
  })}</ul>
}

function Audit({ audit, showQuote }: { audit: EvidenceAudit; showQuote: boolean }) {
  const tone = audit.status === 'sustenta' ? styles.supported : ['contradiz', 'insuficiente', 'not_literal', 'failed', 'invalid', 'uncertain'].includes(audit.status) ? styles.caution : styles.neutral
  return <div className={styles.audit}>
    <span className={styles.caption}>{audit.kind === 'search' ? 'Busca de citação' : 'Checagem semântica'} · nível {code(audit.level)}</span>
    <strong className={`${styles.badge} ${tone}`}>{auditLabels[audit.status]}</strong>
    {showQuote && audit.quote && <blockquote>{audit.quote}</blockquote>}
    <details><summary>Dados da verificação</summary><dl className={styles.facts}>
      {audit.sentence_id && <div><dt>Passagem</dt><dd>{audit.sentence_id} · caracteres {audit.start}–{audit.end}</dd></div>}
      {audit.existence_probability != null && <div><dt>Existência informada pelo JEV</dt><dd>{percent(audit.existence_probability)}</dd></div>}
      {audit.confidence != null && <div><dt>Confiança do verificador</dt><dd>{percent(audit.confidence)}</dd></div>}
      {audit.model && <div><dt>Modelo</dt><dd>{audit.model}</dd></div>}
    </dl><p className={styles.caption}>Parecer experimental; não altera a pontuação. Confiança não representa probabilidade de acerto.</p></details>
  </div>
}

function EvidenceList({ analysis, result }: { analysis: Analysis; result: AxisResult }) {
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
        {audits.length > 0 ? <div className={styles.auditList}>{audits.map((audit, i) => <Audit key={i} audit={audit} showQuote={!!audit.quote && !evidence.some(ev => ev.quote === audit.quote) && audits.findIndex(item => item.quote === audit.quote) === i} />)}</div> : <p className={styles.caption}>Sem parecer semântico registrado. A presença literal não comprova apoio à classificação.</p>}
        {chunk && <details className={styles.context}><summary>Ver trecho completo</summary><p>{chunk.text}</p></details>}
      </article>
    })}</div> : <div className={styles.empty}><strong>Sem citação literal disponível.</strong><p>Consulte a distribuição{result.jev_diagnostics?.length ? ' e os detalhes do modelo' : ''} para entender os dados registrados neste eixo.</p></div>}
  </>
}

function Distribution({ analysis, result, levels }: { analysis: Analysis; result: AxisResult; levels: ScaleLevel[] }) {
  if (!result.valid_chunks) return <div className={styles.empty}><strong>Sem distribuição final</strong><p>{result.status === 'no_evidence' ? 'Os trechos foram considerados sem relevância para este eixo, por isso não receberam níveis para compor o resultado.' : 'Nenhum trecho recebeu uma estimativa válida para compor a distribuição deste eixo.'}</p></div>
  const counts = Object.fromEntries(levels.map(level => [level.chave, analysis.escala ? result.level_counts_by_key?.[level.chave] ?? 0 : result.level_counts[level.chave as keyof typeof result.level_counts] ?? 0]))
  return <>
    <div className={styles.sectionHeading}><h5>Percentual de trechos por nível</h5><span className={styles.caption}>{result.valid_chunks} válidos de {result.total_chunks}</span></div>
    <p className={styles.help}>Níveis finais usados no resultado, após eventuais revisões pelo LLM. As porcentagens e barras mostram a proporção de cada nível entre os trechos válidos do eixo.</p>
    <LevelDistribution axis={result.axis} levels={levels} values={counts} unit="count" total={result.valid_chunks} label={`Distribuição final de ${AXES[result.axis].title}`} />
    <p className={styles.caption}>Trechos sem estimativa válida ficam fora desta contagem. O nível sem posição é uma classificação válida e não equivale a uma estimativa ausente.</p>
    {result.ci95 && <p className={styles.help}>Intervalo entre trechos (95%): {result.ci95[0].toLocaleString('pt-BR', { maximumFractionDigits: 1 })}–{result.ci95[1].toLocaleString('pt-BR', { maximumFractionDigits: 1 })}. Não representa probabilidade de acerto.</p>}
  </>
}

function ModelDiagnostic({ diagnostic: d, analysis, axis, levels }: { diagnostic: JevDiagnostic; analysis: Analysis; axis: Axis; levels: ScaleLevel[] }) {
  const threshold = analysis.effective_config?.level_confidence_min
  const checksIntensity = d.relevante && d.regra_decisao === 'polo_primeiro' && (d.grupo_mais_provavel === 'A' || d.grupo_mais_provavel === 'B')
  const selected = levels.find(level => level.codigo === d.nivel)
  return <div className={styles.diagnostic}>
    {!d.relevante && <div className={styles.statusNotice}><strong>Trecho sem relevância neste eixo</strong><p>A avaliação inicial do JEV considerou este trecho sem relevância para o eixo {AXES[axis].title.toLocaleLowerCase('pt-BR')}.</p></div>}
    <dl className={styles.facts}>
      <div><dt>Regra de decisão</dt><dd>{d.regra_decisao === 'polo_primeiro' ? 'Polo primeiro (experimental)' : 'Nível mais provável'}</dd></div>
      <div><dt>Nível selecionado pelo JEV</dt><dd>{selected ? levelName(selected, axis) : 'Indeterminado'}</dd></div>
      <div><dt>Nível mais provável global</dt><dd>{d.nivel_jev_bruto === null ? 'Empate' : code(d.nivel_jev_bruto)}</dd></div>
      <div><dt>Certeza do JEV (confiança do nível)</dt><dd>{percent(d.confianca_nivel)}</dd></div>
      {d.probabilidade_nivel_condicional !== null && <div><dt>Suporte do nível dentro do polo</dt><dd>{percent(d.probabilidade_nivel_condicional)}</dd></div>}
    </dl>
    {d.desempate_intensidade && <p className="notice small">Houve empate entre intensidades do mesmo polo. Foi selecionada a menor intensidade ({selected?.rotulo ?? d.nivel}); a intensidade permanece incerta.</p>}
    {checksIntensity && <p className="notice small">No modo Polo primeiro, a intensidade é avaliada pelo suporte dentro do polo, diferente da confiança do nível.
      {threshold !== undefined && ` Limiar desta execução: ${percent(threshold)}.`}
      {d.probabilidade_nivel_condicional === null ? ' Intensidade incerta: houve empate, sem uma intensidade única selecionada.'
        : threshold === undefined ? ' O limiar não foi registrado nesta análise.'
          : d.probabilidade_nivel_condicional < threshold ? ` Intensidade incerta: o suporte de ${percent(d.probabilidade_nivel_condicional)} ficou abaixo do limiar.`
            : ` O suporte atingiu o limiar.${d.desempate_intensidade ? ' A intensidade continua incerta pelo empate.' : ''}`}
    </p>}
    <h5>Distribuição dos polos · JEV</h5>
    <dl className={styles.poleValues}>{(['A', 'C', 'B'] as const).map(pole => <div key={pole}><dt>{pole === 'A' ? AXES[axis].a : pole === 'B' ? AXES[axis].b : 'Sem posição'}</dt><dd>{percent(d.probabilities_abc[pole])}</dd></div>)}</dl>
    <h5>Distribuição dos níveis · JEV</h5>
    <LevelDistribution axis={axis} levels={levels} values={d.probabilities_nivel} unit="probability" label={`Distribuição dos níveis JEV de ${AXES[axis].title}`} />
    <p className={styles.caption}>O suporte dentro do polo é a probabilidade do nível dividida pela probabilidade total do polo. Essas medidas não representam probabilidade de acerto.</p>
  </div>
}

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
        {activeView === 'distribution' && <Distribution analysis={analysis} result={result} levels={levels} />}
        {activeView === 'model' && diagnostic && <>
          <p className={styles.help}>Valores do JEV antes de eventual revisão pelo LLM. Não são percentuais ideológicos nem probabilidades de acerto.</p>
          <label className={styles.chunkLabel} htmlFor={`${id}-chunk`}>Examinar trecho</label><select className={styles.chunkSelect} id={`${id}-chunk`} value={diagnostic.chunk_index} onChange={event => setChunkIndex(Number(event.target.value))}>{result.jev_diagnostics!.map(d => <option key={d.chunk_index} value={d.chunk_index}>Trecho {d.chunk_index + 1}{!d.relevante ? ' · sem relevância' : ''}</option>)}</select>
          <details className={styles.context}><summary>Ver texto deste trecho</summary><p>{analysis.chunks.find(chunk => chunk.index === diagnostic.chunk_index)?.text}</p></details>
          <ModelDiagnostic diagnostic={diagnostic} analysis={analysis} axis={axis} levels={levels} />
        </>}
      </div>
      {result.reason_codes.length > 0 && <details className={styles.reasons}><summary>Motivos registrados na análise</summary><ul>{result.reason_codes.map(reason => <li key={reason}>{reason}</li>)}</ul></details>}
    </> : <p className={styles.empty}>Sem dados registrados para este eixo.</p>}
  </section>
}
