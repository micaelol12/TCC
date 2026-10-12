import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import AxisBar from '../../components/AxisBar'
import IdeologyMatch from '../../components/IdeologyMatch'
import { AXES, axisOrder } from '../../domain/axes'
import type { Scores } from '../../domain/quizScoring'
import type { Profile } from '../../storage/localProfile'
import { analyze, getCapabilities } from '../../services/analysisApi'
import type { Analysis, Capabilities, Mode } from '../../services/analysisApi'
import ComparisonPanel from '../comparison/ComparisonPanel'
import styles from '../../components/Cards.module.css'
import AnalysisRadar from './AnalysisRadar'
import { readAnalysisHistory, saveAnalysisHistory } from './analysisHistory'
import type { Entry } from './analysisHistory'

const modeLabels: Record<Mode, string> = { low: 'Baixo', medium: 'Médio', high: 'Alto' }
const modeDescriptions: Record<Mode, string> = { low: 'Análise com JEV', medium: 'JEV com revisão por LLM quando necessária', high: 'Análise diretamente com LLM' }
const recipients: Record<Mode, string> = { low: 'TypeSafe (JEV)', medium: 'TypeSafe (JEV) e, quando necessário, Maritaca (Sabiá)', high: 'Maritaca (Sabiá)' }

function scoresForAnalysis(analysis: Analysis): Scores | null {
  const scores = {} as Scores
  for (const axis of axisOrder) {
    const score = analysis.axes.find(result => result.axis === axis)?.pole_a
    if (score == null || !Number.isFinite(score)) return null
    scores[axis] = score
  }
  return scores
}

export default function AnalysisPage({ profile }: { profile: Profile | null }) {
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [mode, setMode] = useState<Mode>('medium')
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [capsError, setCapsError] = useState('')
  const [entries, setEntries] = useState<Entry[]>(readAnalysisHistory)
  const [selectedId, setSelectedId] = useState<number | null>(() => readAnalysisHistory().at(-1)?.id ?? null)
  const [showComposer, setShowComposer] = useState(() => readAnalysisHistory().length === 0)
  const [mobileTab, setMobileTab] = useState<'analysis' | 'comparison'>('analysis')
  const [busy, setBusy] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [error, setError] = useState('')
  const abortRef = useRef<AbortController | null>(null)
  const idRef = useRef(Math.max(0, ...readAnalysisHistory().map(entry => entry.id)))
  useEffect(() => { getCapabilities().then(setCaps).catch(() => setCapsError('API indisponível. Inicie o servidor para analisar textos.')) }, [])
  useEffect(() => { saveAnalysisHistory(entries) }, [entries])
  useEffect(() => { if (!busy) return; const timer = window.setInterval(() => setSeconds(s => s + 1), 1000); return () => clearInterval(timer) }, [busy])
  useEffect(() => () => abortRef.current?.abort(), [])
  const selected = entries.find(entry => entry.id === selectedId) ?? null
  const selectedScores = selected ? scoresForAnalysis(selected.analysis) : null
  const limit = caps?.max_chars ?? 60000
  const tooLong = text.length > limit
  const enabled = caps?.modes[mode] ?? false

  async function send(inputText = text, inputTitle = title) {
    if (!inputText.trim() || inputText.length > limit || busy || !enabled) return
    const controller = new AbortController()
    abortRef.current = controller
    setBusy(true); setSeconds(0); setError('')
    try {
      const result = await analyze(inputText, mode, controller.signal)
      const entry: Entry = { id: ++idRef.current, title: inputTitle.trim() || `Análise ${idRef.current}`, text: inputText, analysis: result, mode }
      setEntries(current => [...current, entry]); setSelectedId(entry.id); setMobileTab('analysis'); setShowComposer(false)
      setText(''); setTitle('')
    } catch (err) {
      setError(controller.signal.aborted ? 'Análise cancelada. O texto foi preservado.' : err instanceof Error ? err.message : 'Falha na análise.')
    } finally { setBusy(false); abortRef.current = null }
  }

  return <main className="analysisShell">
    <header className="analysisHeading"><div><div className="eyebrow">Análise de textos</div><h1>Leia posições em quatro eixos</h1><p className="muted">Cada envio é independente. O histórico fica nesta sessão do navegador.</p></div>{!profile && <Link className="button secondary" to="/teste">Fazer meu teste</Link>}</header>
    <p className="aiDisclaimer">A análise é realizada por IA e pode cometer erros. Confira o texto original, a cobertura e as evidências antes de interpretar os resultados.</p>
    <div className="analysisGrid">
      <aside className="history" aria-label="Histórico desta sessão">{entries.length > 0 && <button className="newAnalysisButton" onClick={() => { setShowComposer(true); setMobileTab('analysis') }}>+ Nova análise</button>}<h2>Histórico</h2>{entries.length === 0 ? <p className="muted small">Nenhuma análise nesta sessão.</p> : <ul>{entries.map(entry => <li key={entry.id}><button aria-pressed={selectedId === entry.id && !showComposer} className={selectedId === entry.id && !showComposer ? 'historyButton active' : 'historyButton'} onClick={() => { setSelectedId(entry.id); setShowComposer(false); setMobileTab('analysis') }}>{entry.title}<span>{modeLabels[entry.mode]}</span></button></li>)}</ul>}</aside>
      <div className="conversation">
        <div className="mobileTabs" role="group" aria-label="Visualização"><button aria-pressed={mobileTab === 'analysis'} className={mobileTab === 'analysis' ? 'tab active' : 'tab'} onClick={() => setMobileTab('analysis')}>Análise</button><button aria-pressed={mobileTab === 'comparison'} className={mobileTab === 'comparison' ? 'tab active' : 'tab'} onClick={() => setMobileTab('comparison')}>Comparação</button></div>
        <div className={mobileTab === 'analysis' ? 'analysisContent' : 'analysisContent mobileHidden'}>
          {!showComposer && selected && <section className={styles.card} aria-label="Análise selecionada">
            <div className="cardTop"><span className={styles.chip}>{modeLabels[selected.analysis.processing_level]} · {selected.analysis.models_used.join(', ') || 'Serviço externo'}</span><span className="muted small">{selected.analysis.chunks.length} trechos</span></div>
            <h2>{selected.title}</h2><details className="sourceDetails"><summary>Ver texto analisado</summary><p className="sourceText">{selected.text}</p></details>
            {selected.analysis.warnings.length > 0 && <p className="notice">Há limitações nesta análise: {selected.analysis.warnings.join(', ')}.</p>}
            <AnalysisRadar analysis={selected.analysis} />
            <div className="sectionHeading detailHeading"><div><div className="eyebrow">Detalhamento</div><h3>Quatro eixos</h3></div></div>
            {axisOrder.map(axis => {
              const result = selected.analysis.axes.find(item => item.axis === axis)
              return result ? <div key={axis}><AxisBar axis={axis} score={result.pole_a} headingLevel={4} />
                <details><summary>Distribuição e evidências de {AXES[axis].title}</summary><p className="small muted">Cobertura: {result.valid_chunks} de {result.total_chunks} trechos. {result.sufficient_evidence ? '' : 'Evidência limitada.'} {result.status === 'abstained' ? 'Classificação indeterminada.' : result.status === 'no_evidence' ? 'Sem posição identificada.' : ''}</p><p className="small">Níveis: −2: {result.level_counts.minus2}, −1: {result.level_counts.minus1}, 0: {result.level_counts.zero}, +1: {result.level_counts.plus1}, +2: {result.level_counts.plus2}.</p>{result.ci95 && <p className="small">Intervalo entre trechos (95%): {result.ci95[0].toFixed(1)}–{result.ci95[1].toFixed(1)}. Não representa probabilidade de acerto.</p>}{result.evidence.length ? <ul>{result.evidence.map((ev, i) => <li key={i}>Trecho {ev.chunk_index + 1}: “{ev.quote}”</li>)}</ul> : <p className="small muted">Sem citação literal disponível. JEV classifica trechos sem devolver citações.</p>}{result.reason_codes.length > 0 && <p className="small muted">Motivos: {result.reason_codes.join(', ')}.</p>}</details>
              </div> : null
            })}
            {selectedScores && <IdeologyMatch scores={selectedScores} source="analysis" />}
            <div className="actions"><button className="secondary" onClick={() => { setText(selected.text); setTitle(selected.title); setShowComposer(true) }}>Usar este texto em nova análise</button><button className="secondary" onClick={() => setMobileTab('comparison')}>Comparar comigo</button></div>
          </section>}
          {showComposer && <section className={styles.card} aria-label="Novo texto"><div className="sectionHeading"><div><div className="eyebrow">Novo texto</div><h2>Nova análise</h2></div>{entries.length > 0 && <button className="textButton" onClick={() => setShowComposer(false)}>Fechar</button>}</div>
            <label htmlFor="local-title">Título local <span className="muted">(opcional)</span></label><input id="local-title" value={title} onChange={e => setTitle(e.target.value)} placeholder="Ex.: proposta de transporte" />
            <label htmlFor="text-input">Texto em português</label><textarea id="text-input" rows={7} value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); void send() } }} placeholder="Cole ou digite um texto político para analisar..." aria-describedby="text-help" />
            <p id="text-help" className={tooLong ? 'error small' : 'muted small'}>{text.length.toLocaleString('pt-BR')} de {limit.toLocaleString('pt-BR')} caracteres. Ctrl/Cmd + Enter envia. {tooLong && 'Reduza o texto para continuar.'}</p>
            <fieldset className="modeGroup"><legend>Processamento</legend>{(['low', 'medium', 'high'] as Mode[]).map(value => <label key={value} className="modeOption"><input type="radio" name="mode" value={value} checked={mode === value} onChange={() => setMode(value)} /><span><strong>{modeLabels[value]}</strong><small>{modeDescriptions[value]}{caps && !caps.modes[value] ? ' · indisponível' : ''}</small></span></label>)}</fieldset>
            <p className="privacyNote">Seu resultado do teste fica neste navegador. Este texto será enviado a {recipients[mode]}.</p>
            {capsError && <p className="error" role="status">{capsError}</p>}{error && <p className="error" role="alert">{error}</p>}
            <div className="actions"><button onClick={() => void send()} disabled={busy || !text.trim() || tooLong || !enabled}>Analisar texto</button>{busy && <button className="secondary" onClick={() => abortRef.current?.abort()}>Cancelar</button>}</div>
            <div role="status" aria-live="polite">{busy ? `Analisando o texto há ${seconds} segundos. O tempo varia conforme o tamanho e o modo escolhido.` : !enabled && caps ? 'Modo indisponível neste servidor.' : ''}</div>
          </section>}
        </div>
      </div>
      <div className={mobileTab === 'comparison' ? 'comparisonContent' : 'comparisonContent mobileHidden'}><ComparisonPanel profile={profile} analysis={selected?.analysis ?? null} /></div>
    </div>
  </main>
}
