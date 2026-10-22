import { experimentRecipients } from '@8values/shared/domain/experimentConfig'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Profile } from '../../storage/localProfile'
import { createAnalysisClient, modeLabels } from '../../services/analysisApi'
import AnalysisResult from '@8values/shared/components/AnalysisResult'
import AnalysisComposer from '@8values/shared/components/AnalysisComposer'
import { useAnalysisRequest } from '@8values/shared/hooks/useAnalysisRequest'
import type { Capabilities, Mode } from '../../services/analysisApi'
import ComparisonPanel from '../comparison/ComparisonPanel'
import { readAnalysisHistory, saveAnalysisHistory } from './analysisHistory'
import type { Entry } from './analysisHistory'
import { createReportClient } from '@8values/shared/reports'
import ExperimentPanel from '@8values/shared/components/ExperimentPanel'
import ExperimentComparison from '@8values/shared/components/ExperimentComparison'
import { useExperimentConfig } from '@8values/shared/hooks/useExperimentConfig'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'

const client = createAnalysisClient()
const reportClient = createReportClient()

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
  const { busy, seconds, error, run, cancel } = useAnalysisRequest(client)
  const experiment = useExperimentConfig(caps, window.location.origin, mode)
  const idRef = useRef(Math.max(0, ...readAnalysisHistory().map(entry => entry.id)))
  useEffect(() => { client.getCapabilities().then(setCaps).catch(() => setCapsError('API indisponível. Inicie o servidor para analisar textos.')) }, [])
  useEffect(() => { saveAnalysisHistory(entries) }, [entries])
  const selected = entries.find(entry => entry.id === selectedId) ?? null
  const limit = caps?.max_chars ?? 60000
  const enabled = caps?.modes[mode] ?? false

  async function send(inputText = text, inputTitle = title) {
    if (!inputText.trim() || Array.from(inputText).length > limit || busy || !enabled || !caps || experiment.blocked) return
    try {
      const result = await run(inputText, mode, caps, experiment.requestConfig)
      const entry: Entry = { id: ++idRef.current, title: inputTitle.trim() || `Análise ${idRef.current}`, text: inputText, analysis: result, mode }
      setEntries(current => [...current, entry]); setSelectedId(entry.id); setMobileTab('analysis'); setShowComposer(false)
      setText(''); setTitle('')
    } catch { /* useAnalysisRequest preserves and presents the error */ }
  }

  return <main className="analysisShell">
    {isLabBuild && <p className="labBadge">8values Lab · Versão de teste</p>}
    <header className="analysisHeading"><div><div className="eyebrow">Análise de textos</div><h1>Leia posições em quatro eixos</h1><p className="muted">Cada envio é independente. O histórico fica nesta sessão do navegador.</p></div>{!profile && <Link className="button secondary" to="/teste">Fazer meu teste</Link>}</header>
    <p className="aiDisclaimer">A análise é realizada por IA e pode cometer erros. Confira o texto original, a cobertura e as evidências antes de interpretar os resultados.</p>
    <div className="analysisGrid">
      <aside className="history" aria-label="Histórico desta sessão">{entries.length > 0 && <button className="newAnalysisButton" onClick={() => { setShowComposer(true); setMobileTab('analysis') }}>+ Nova análise</button>}<h2>Histórico</h2>{entries.length === 0 ? <p className="muted small">Nenhuma análise nesta sessão.</p> : <ul>{entries.map(entry => <li key={entry.id}><button aria-pressed={selectedId === entry.id && !showComposer} className={selectedId === entry.id && !showComposer ? 'historyButton active' : 'historyButton'} onClick={() => { setSelectedId(entry.id); setShowComposer(false); setMobileTab('analysis') }}>{entry.title}<span>{modeLabels[entry.mode]}</span></button></li>)}</ul>}</aside>
      <div className="conversation">
        <div className="mobileTabs" role="group" aria-label="Visualização"><button aria-pressed={mobileTab === 'analysis'} className={mobileTab === 'analysis' ? 'tab active' : 'tab'} onClick={() => setMobileTab('analysis')}>Análise</button><button aria-pressed={mobileTab === 'comparison'} className={mobileTab === 'comparison' ? 'tab active' : 'tab'} onClick={() => setMobileTab('comparison')}>Comparação</button></div>
        <div className={mobileTab === 'analysis' ? 'analysisContent' : 'analysisContent mobileHidden'}>
          {!showComposer && selected && <AnalysisResult entry={selected} reportClient={reportClient} reportOrigin="web">
            {isLabBuild && <ExperimentComparison key={selected.id} entry={selected} entries={entries} />}
            <div className="actions"><button className="secondary" onClick={() => { setText(selected.text); setTitle(selected.title); setShowComposer(true) }}>Usar este texto em nova análise</button><button className="secondary" onClick={() => setMobileTab('comparison')}>Comparar comigo</button></div>
          </AnalysisResult>}
          {showComposer && <AnalysisComposer text={text} title={title} mode={mode} caps={caps} busy={busy} seconds={seconds} error={error} capsError={capsError}
            recipient={experimentRecipients(mode, experiment.config, experiment.available)}
            configBlocked={experiment.blocked} experimentPanel={experiment.available ? <ExperimentPanel caps={experiment.available} config={experiment.config} onChange={experiment.setConfig} mode={mode} busy={busy} error={experiment.error} storageKey={experiment.storageKey} notice={experiment.notice} onNotice={experiment.setNotice} client={client} onKeysUpdated={async () => setCaps(await client.getCapabilities())} /> : isLabBuild ? <p className="notice small">Conecte a API Lab com a configuração experimental habilitada para editar parâmetros.</p> : undefined}
            onText={setText} onTitle={setTitle} onMode={setMode} onSend={() => void send()} onCancel={cancel}
            onRetry={() => { setCapsError(''); setCaps(null); void client.getCapabilities().then(setCaps).catch(() => setCapsError('API indisponível. Inicie o servidor para analisar textos.')) }}
            onClose={entries.length ? () => setShowComposer(false) : undefined} />}
        </div>
      </div>
      <div className={mobileTab === 'comparison' ? 'comparisonContent' : 'comparisonContent mobileHidden'}><ComparisonPanel profile={profile} analysis={selected?.analysis ?? null} /></div>
    </div>
  </main>
}
