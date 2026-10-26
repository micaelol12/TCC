import type { ReactNode } from 'react'
import { modeLabels, type AnalysisEntry } from '../api/analysisApi'
import { AXES, axisOrder } from '../domain/axes'
import type { Scores } from '../domain/quizScoring'
import AxisBar from './AxisBar'
import AnalysisRadar from './AnalysisRadar'
import IdeologyMatch from './IdeologyMatch'
import styles from '../styles/Cards.module.css'
import ReportDialog from './ReportDialog'
import type { ReportClient, ReportRequest } from '../api/reportApi'
import { historicalLevels } from '../domain/ordinalScale'
const warningLabels: Record<string, string> = { falha_autenticacao_jev: 'A API não conseguiu autenticar no TypeSafe. Confira a chave no servidor.', falha_autenticacao_llm: 'A API não conseguiu autenticar no provedor LLM selecionado. Confira sua chave.', evidencia_nao_verificada: 'O modelo retornou uma citação que não confere com o texto. A estimativa correspondente foi descartada.' }
const auditLabels: Record<string, string> = { found: 'Passagem encontrada', not_selected: 'Nenhuma passagem selecionada pelo critério configurado', not_literal: 'Citação literal inválida', sustenta: 'Sustenta a posição e intensidade', contradiz: 'Contradiz a posição atribuída', insuficiente: 'Evidência insuficiente para a posição ou intensidade', uncertain: 'Parecer empatado', failed: 'Falha ao consultar o verificador', invalid: 'Resposta inválida do verificador' }
const percent = (value: number) => `${(value * 100).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`

export default function AnalysisResult({ entry, reportClient, reportOrigin, compact = false, children }: { entry: AnalysisEntry<number | string>; reportClient: ReportClient; reportOrigin: ReportRequest['client']; compact?: boolean; children?: ReactNode }) {
  const analysis = entry.analysis
  const levelConfidenceMin = analysis.effective_config?.level_confidence_min
  const scores = Object.fromEntries(analysis.axes.map(axis => [axis.axis, axis.pole_a])) as Scores
  const complete = axisOrder.every(axis => Number.isFinite(scores[axis]))
  return <section className={styles.card} aria-label="Análise selecionada">
    <div className="cardTop"><span className={styles.chip}>{modeLabels[analysis.processing_level]} · {analysis.models_used.join(', ') || 'Serviço externo'}</span><span className="muted small">{analysis.chunks.length} trechos</span></div>
    <h2>{entry.title}</h2>{entry.source && <p className="muted small sourceOrigin">Trecho selecionado em {entry.source}</p>}
    <p className="muted small">O resultado descreve somente o trecho enviado.</p>
    <p className="muted small">Escala: {analysis.escala ? `${analysis.escala.niveis.length} níveis · ${analysis.escala.id} · v${analysis.escala.versao}` : `${analysis.schema_version === '1' ? 5 : 9} níveis · histórica`}.</p>
    {analysis.lab_execution_id && <p className="small configHash" role="status">Execução gravada no banco: {analysis.lab_execution_id}</p>}
    <details className="sourceDetails"><summary>Ver texto analisado</summary><p className="sourceText">{entry.text}</p></details>
    {analysis.effective_config ? <details className="experimentSnapshot"><summary>Configuração utilizada{analysis.environment === 'lab' ? ' · versão de teste' : ''}</summary>
      <p className="small muted">Ambiente: {analysis.environment}. Pipeline: {analysis.pipeline_version}. Configuração v{analysis.config_version}.</p>
      <pre className="reportSnapshot">{JSON.stringify(analysis.effective_config, null, 2)}</pre><p className="small configHash">Identificador: {analysis.config_hash}</p>
    </details> : <p className="muted small">Configuração não registrada nesta análise.</p>}
    {analysis.warnings.length > 0 && <p className="notice">Há limitações nesta análise: {analysis.warnings.map(reason => warningLabels[reason] ?? reason).join(' ')}.</p>}
    {!compact && <AnalysisRadar analysis={analysis} />}
    <div className="sectionHeading detailHeading"><div><div className="eyebrow">Detalhamento</div><h3>Quatro eixos</h3></div></div>
    {axisOrder.map(axis => {
      const result = analysis.axes.find(item => item.axis === axis)
      return result ? <div key={axis}><AxisBar axis={axis} score={result.pole_a} headingLevel={4} showInterpretation />
        {result.reason_codes.includes('intensidade_ambigua') && !result.methods_used.includes('llm') && <p className="notice small">Intensidade incerta no JEV. Em pelo menos um trecho, houve empate entre intensidades do polo mais provável ou o suporte do nível ficou abaixo do limiar configurado. Como não houve revisão por LLM, a pontuação é preliminar. Consulte os valores na distribuição dos níveis por trecho abaixo.</p>}
        {result.reason_codes.includes('direcao_ambigua') && analysis.effective_config?.regra_decisao === 'polo_primeiro' && !result.methods_used.includes('llm') && <p className="notice small">Direção incerta no JEV. Os grupos estão próximos; a pontuação é preliminar.</p>}
        <details><summary>Distribuição e evidências de {AXES[axis].title}</summary>
          <p className="small muted">Cobertura: {result.valid_chunks} de {result.total_chunks} trechos. {result.sufficient_evidence ? '' : 'Evidência limitada.'} {result.status === 'abstained' ? 'Classificação indeterminada.' : result.status === 'no_evidence' ? 'Sem posição identificada.' : ''}</p>
          <p className="small">Níveis: {(analysis.escala?.niveis ?? historicalLevels(analysis.schema_version)).map(n => `${n.codigo > 0 ? '+' : ''}${n.codigo} (${n.rotulo}): ${analysis.escala ? result.level_counts_by_key?.[n.chave] ?? 0 : result.level_counts[n.chave as keyof typeof result.level_counts] ?? 0}`).join('; ')}.</p>
          {!!result.jev_diagnostics?.length && <div aria-label={`Decisão JEV de ${AXES[axis].title}`}>
            <h5>Decisão do JEV por trecho</h5><p className="small muted">Distribuições retornadas pelo modelo, antes de eventual revisão pelo LLM. Os valores abaixo não são percentuais ideológicos nem probabilidades de acerto. A certeza é a confiança do nível informada pelo JEV.</p>
            <ul>{result.jev_diagnostics.map(d => {
              const checksIntensity = d.relevante && d.regra_decisao === 'polo_primeiro' && (d.grupo_mais_provavel === 'A' || d.grupo_mais_provavel === 'B')
              return <li key={d.chunk_index}>
              Trecho {d.chunk_index + 1} · {d.regra_decisao === 'polo_primeiro' ? 'Polo primeiro (experimental)' : 'Nível mais provável'}{!d.relevante && ' · sem relevância identificada'}.
              {' '}{AXES[axis].a}: {(d.probabilities_abc.A * 100).toFixed(1)}%; {AXES[axis].b}: {(d.probabilities_abc.B * 100).toFixed(1)}%; sem posição: {(d.probabilities_abc.C * 100).toFixed(1)}%.
              {' '}Nível mais provável global: {d.nivel_jev_bruto ?? 'empate'}; nível selecionado: {d.nivel ?? 'indeterminado'}.
              <details><summary>Ver distribuição dos níveis</summary>
                <p className="small"><strong>Certeza do JEV (confiança do nível): {percent(d.confianca_nivel)}.</strong> Essa medida é diferente do suporte do nível dentro do polo.</p>
                {d.probabilidade_nivel_condicional !== null && <p className="small">Suporte do nível dentro do polo: {percent(d.probabilidade_nivel_condicional)}. É a probabilidade do nível dividida pela probabilidade total do polo.</p>}
                {checksIntensity && <p className="small muted">
                  No modo Polo primeiro, a intensidade é avaliada pelo suporte dentro do polo.
                  {levelConfidenceMin !== undefined && ` Limiar desta execução: ${percent(levelConfidenceMin)}.`}
                  {d.probabilidade_nivel_condicional === null
                    ? ' Intensidade incerta neste trecho: houve empate entre os níveis mais prováveis dentro do polo, sem uma intensidade única selecionada.'
                    : levelConfidenceMin !== undefined && d.probabilidade_nivel_condicional < levelConfidenceMin
                      ? ` Intensidade incerta neste trecho: o suporte de ${percent(d.probabilidade_nivel_condicional)} ficou abaixo do limiar de ${percent(levelConfidenceMin)}.`
                      : levelConfidenceMin !== undefined ? ' O suporte deste trecho atingiu o limiar de intensidade.' : ' O limiar não foi registrado nesta análise.'}
                </p>}
                <ul>{analysis.escala?.niveis.map(n => <li key={n.chave}>{n.rotulo}: {percent(d.probabilities_nivel[n.chave] ?? 0)}</li>)}</ul>
              </details>
            </li>})}</ul>
          </div>}
          {result.ci95 && <p className="small">Intervalo entre trechos (95%): {result.ci95[0].toFixed(1)}–{result.ci95[1].toFixed(1)}. Não representa probabilidade de acerto.</p>}
          {result.evidence.length ? <><p className="small muted">Citações localizadas no texto. Presença literal não comprova apoio à classificação.</p><ul>{result.evidence.map((ev, i) => <li key={i}>Trecho {ev.chunk_index + 1}: “{ev.quote}”</li>)}</ul></> : <p className="small muted">Sem citação literal disponível.</p>}
          {!!result.evidence_audit?.length && <div aria-label={`Auditoria de evidências de ${AXES[axis].title}`}>
            <h5>Evidências experimentais</h5><p className="small muted">Pareceres do JEV registrados para revisão. A pontuação permanece igual; confiança não representa probabilidade de acerto.</p>
            <ul>{result.evidence_audit.map((audit, i) => <li key={i}>
              Trecho {audit.chunk_index + 1} · nível {audit.level > 0 ? '+' : ''}{audit.level} · {audit.kind === 'search' ? 'Busca por ID' : 'Checagem semântica'}: <strong>{auditLabels[audit.status]}</strong>.
              {audit.sentence_id && ` ID ${audit.sentence_id}, caracteres ${audit.start}–${audit.end}.`}
              {audit.quote && <blockquote>{audit.quote}</blockquote>}
              {audit.existence_probability != null && ` Existência: ${audit.existence_probability.toFixed(2)}.`}
              {audit.confidence != null && ` Confiança: ${audit.confidence.toFixed(2)}.`}
              {audit.model && ` Modelo: ${audit.model}.`}
            </li>)}</ul>
          </div>}
          {result.reason_codes.length > 0 && <p className="small muted">Motivos: {result.reason_codes.join(', ')}.</p>}
        </details></div> : <AxisBar key={axis} axis={axis} score={null} headingLevel={4} />
    })}
    {compact && <details><summary>Ver radar e detalhes gerais</summary><AnalysisRadar analysis={analysis} /></details>}
    {complete && <IdeologyMatch scores={scores} source="analysis" />}
    <ReportDialog key={entry.id} entry={entry} client={reportClient} origin={reportOrigin} />{children}
  </section>
}
