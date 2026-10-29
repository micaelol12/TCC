import { experimentRecipients } from '@8values/shared/domain/experimentConfig'
import { configuredRecipients } from '@8values/shared/api'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Profile } from '../../storage/localProfile'
import { createAnalysisClient, modeLabels } from '../../services/analysisApi'
import AnalysisResult from '@8values/shared/components/AnalysisResult'
import AnalysisComposer from '@8values/shared/components/AnalysisComposer'
import { useAnalysisRequest } from '@8values/shared/hooks/useAnalysisRequest'
import type { Capabilities } from '../../services/analysisApi'
import ComparisonPanel from '../comparison/ComparisonPanel'
import { readAnalysisHistory, saveAnalysisHistory } from './analysisHistory'
import type { Entry } from './analysisHistory'
import { createReportClient } from '@8values/shared/reports'
import ExperimentPanel from '@8values/shared/components/ExperimentPanel'
import ExperimentComparison from '@8values/shared/components/ExperimentComparison'
import { useExperimentConfig } from '@8values/shared/hooks/useExperimentConfig'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'
import { readAnalysisDraft, saveAnalysisDraft } from './analysisDraft'
import type { AnalysisDraft } from './analysisDraft'
import { CONNECTION_ERROR } from '@8values/shared/domain/analysisMessages'
import ConfirmAction from '@8values/shared/components/ConfirmAction'

const client = createAnalysisClient()
const reportClient = createReportClient()

export default function AnalysisPage({ profile }: { profile: Profile | null }) {
  const [draft, setDraft] = useState(readAnalysisDraft)
  const { title, text, mode } = draft
  const [draftStored, setDraftStored] = useState(true)
  const [historyStored, setHistoryStored] = useState(true)
  function updateDraft(change: Partial<AnalysisDraft>) { setDraft(current => ({ ...current, ...change })) }
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [capsError, setCapsError] = useState('')
  const [entries, setEntries] = useState<Entry[]>(readAnalysisHistory)
  const [selectedId, setSelectedId] = useState<number | null>(() => readAnalysisHistory().at(-1)?.id ?? null)
  const [showComposer, setShowComposer] = useState(() => !!(readAnalysisDraft().text || readAnalysisDraft().title) || readAnalysisHistory().length === 0)
  const [view, setView] = useState<'analysis' | 'comparison' | 'experiments'>('analysis')
  const { busy, seconds, error, run, cancel, clearError } = useAnalysisRequest(client)
  const experiment = useExperimentConfig(caps, window.location.origin, mode)
  const idRef = useRef(Math.max(0, ...readAnalysisHistory().map(entry => entry.id)))
  useEffect(() => { client.getCapabilities().then(setCaps).catch(() => setCapsError(CONNECTION_ERROR)) }, [])
  useEffect(() => { setHistoryStored(saveAnalysisHistory(entries)) }, [entries])
  useEffect(() => { setDraftStored(saveAnalysisDraft(draft)) }, [draft])
  useEffect(() => {
    if (draftStored || !(text || title)) return
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [draftStored, text, title])
  const selected = entries.find(entry => entry.id === selectedId) ?? null
  const replacesDraft = !!selected && !!(text || title) && (text !== selected.text || title !== selected.title)
  function reuseSelected() {
    if (!selected) return
    updateDraft({ text: selected.text, title: selected.title, mode: selected.mode }); clearError(); setShowComposer(true)
  }
  const limit = caps?.max_chars ?? 60000
  const enabled = caps?.modes[mode] ?? false

  async function send(inputText = text, inputTitle = title) {
    if (!inputText.trim() || Array.from(inputText).length > limit || busy || !enabled || !caps || experiment.blocked) return
    try {
      const result = await run(inputText, mode, caps, experiment.requestConfig)
      const entry: Entry = { id: ++idRef.current, title: inputTitle.trim() || `Análise ${idRef.current}`, text: inputText, analysis: result, mode }
      setEntries(current => [...current, entry]); setSelectedId(entry.id); setView('analysis'); setShowComposer(false)
      updateDraft({ text: '', title: '' })
    } catch { /* useAnalysisRequest preserves and presents the error */ }
  }

  return <main className="analysisShell">
    {isLabBuild && <p className="labBadge">8values Lab · Versão de teste</p>}
    <header className="analysisHeading"><div><div className="eyebrow">Análise de textos</div><h1>Leia posições em quatro eixos</h1><p className="muted">Cada envio é independente. O histórico fica nesta sessão do navegador.</p></div>{!profile && <Link className="button secondary" to="/teste">Fazer meu teste</Link>}</header>
    <p className="aiDisclaimer">A análise é realizada por IA e pode cometer erros. Confira o texto original, a cobertura e as evidências antes de interpretar os resultados.</p>
    {!draftStored && <p className="notice" role="status">Não foi possível guardar o rascunho nesta aba. Você pode navegar pelo app, mas recarregar ou fechar a página pode apagar o texto. Copie-o antes de sair.</p>}
    {!historyStored && <p className="notice" role="status">Não foi possível guardar o histórico nesta aba. As análises continuam disponíveis enquanto o app estiver aberto, mas podem ser perdidas ao recarregar ou fechar a página.</p>}
    <div className="analysisGrid singleAnalysisView">
      <aside className="history" aria-label="Histórico desta sessão">{entries.length > 0 && <button className="newAnalysisButton" disabled={busy} onClick={() => { clearError(); setShowComposer(true); setView('analysis') }}>+ Nova análise</button>}<h2>Histórico</h2>{entries.length === 0 ? <p className="muted small">Nenhuma análise nesta sessão.</p> : <ul>{entries.map(entry => <li key={entry.id}><button disabled={busy} aria-pressed={selectedId === entry.id && !showComposer} className={selectedId === entry.id && !showComposer ? 'historyButton active' : 'historyButton'} onClick={() => { setSelectedId(entry.id); setShowComposer(false) }}>{entry.title}<span>{modeLabels[entry.mode]}</span></button></li>)}</ul>}</aside>
      <div className="conversation">
        <div className="analysisViewTabs" role="group" aria-label="Visualização"><button aria-pressed={view === 'analysis'} className={view === 'analysis' ? '' : 'secondary'} onClick={() => setView('analysis')}>Análise</button><button aria-pressed={view !== 'analysis'} className={view !== 'analysis' ? '' : 'secondary'} onClick={() => setView('comparison')}>Comparação</button></div>
        {view === 'analysis' ? <div className="analysisContent">
          {!showComposer && selected && <AnalysisResult entry={selected} reportClient={reportClient} reportOrigin="web">
            <div className="actions">{replacesDraft ? <ConfirmAction label="Editar e reanalisar" className="secondary" title="Substituir o rascunho atual?" description="O rascunho ainda não enviado será substituído pelo texto desta análise. Cancele para manter seu rascunho." confirmLabel="Sim, substituir rascunho" onConfirm={reuseSelected} /> : <button className="secondary" onClick={reuseSelected}>Editar e reanalisar</button>}<button className="secondary" onClick={() => setView('comparison')}>Comparar comigo</button><button className="secondary" onClick={() => setView('experiments')}>Comparar análises</button></div>
          </AnalysisResult>}
          {showComposer && <AnalysisComposer text={text} title={title} mode={mode} caps={caps} busy={busy} seconds={seconds} error={error} capsError={capsError}
            recipient={experiment.available ? experimentRecipients(mode, experiment.config, experiment.available) : configuredRecipients(mode, caps)}
            configBlocked={experiment.blocked} experimentPanel={experiment.available ? <ExperimentPanel caps={experiment.available} config={experiment.config} onChange={experiment.setConfig} mode={mode} busy={busy} error={experiment.error} notice={experiment.notice} onNotice={experiment.setNotice} client={client} onKeysUpdated={async () => setCaps(await client.getCapabilities())} /> : isLabBuild ? <p className="notice small">Conecte a API Lab com a configuração experimental habilitada para editar parâmetros.</p> : undefined}
            onText={text => updateDraft({ text })} onTitle={title => updateDraft({ title })} onMode={mode => updateDraft({ mode })} onSend={() => void send()} onCancel={cancel}
            draftNotice={draftStored && (text || title) ? 'Rascunho guardado nesta aba. Você pode navegar e voltar ou recarregar a página. Fechar a aba encerra esta sessão.' : undefined}
            onDiscard={() => { updateDraft({ text: '', title: '' }); clearError() }}
            onRetry={() => { setCapsError(''); setCaps(null); void client.getCapabilities().then(setCaps).catch(() => setCapsError(CONNECTION_ERROR)) }}
            onClose={entries.length ? () => setShowComposer(false) : undefined} />}
        </div> : <div className="analysisContent">
          <nav className="comparisonModes" aria-label="Tipo de comparação"><button className={view === 'comparison' ? '' : 'secondary'} aria-pressed={view === 'comparison'} onClick={() => setView('comparison')}>Com meu perfil</button><button className={view === 'experiments' ? '' : 'secondary'} aria-pressed={view === 'experiments'} disabled={!selected} onClick={() => setView('experiments')}>Entre análises</button></nav>
          {view === 'experiments' && selected ? <ExperimentComparison key={selected.id} entry={selected} entries={entries} /> : <ComparisonPanel profile={profile} analysis={selected?.analysis ?? null} analysisTitle={selected?.title} />}
        </div>}
      </div>
    </div>
  </main>
}
