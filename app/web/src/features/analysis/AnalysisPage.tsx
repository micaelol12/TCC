import { experimentRecipients } from '@8values/shared/domain/experimentConfig'
import { configuredRecipients } from '@8values/shared/api'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Profile } from '../../storage/localProfile'
import { createAnalysisClient } from '../../services/analysisApi'
import AnalysisResult from '@8values/shared/components/AnalysisResult'
import AnalysisComposer from '@8values/shared/components/AnalysisComposer'
import { useAnalysisRequest } from '@8values/shared/hooks/useAnalysisRequest'
import type { Capabilities } from '../../services/analysisApi'
import ComparisonPanel from '../comparison/ComparisonPanel'
import { createReportClient } from '@8values/shared/reports'
import ExperimentPanel from '@8values/shared/components/ExperimentPanel'
import ExperimentComparison from '@8values/shared/components/ExperimentComparison'
import { useExperimentConfig } from '@8values/shared/hooks/useExperimentConfig'
import { isLabBuild } from '@8values/shared/domain/experimentConfig'
import { CONNECTION_ERROR } from '@8values/shared/domain/analysisMessages'
import ConfirmAction from '@8values/shared/components/ConfirmAction'
import AnalysisHistoryPanel from './AnalysisHistoryPanel'
import { useAnalysisSession } from './useAnalysisSession'

const client = createAnalysisClient()
const reportClient = createReportClient()

export default function AnalysisPage({ profile }: { profile: Profile | null }) {
  const { draft, updateDraft, draftStored, entries, historyStored, appendAnalysis } = useAnalysisSession()
  const { title, text, mode } = draft
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null)
  const [capabilitiesError, setCapabilitiesError] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(() => entries.at(-1)?.id ?? null)
  const [showComposer, setShowComposer] = useState(() => !!(text || title) || entries.length === 0)
  const [view, setView] = useState<'analysis' | 'comparison' | 'experiments'>('analysis')
  const { busy, seconds, error, run, cancel, clearError } = useAnalysisRequest(client)
  const experiment = useExperimentConfig(capabilities, window.location.origin, mode)
  useEffect(() => { void refreshCapabilities() }, [])

  const selectedEntry = entries.find(entry => entry.id === selectedId) ?? null
  const replacesDraft = !!selectedEntry && !!(text || title) && (text !== selectedEntry.text || title !== selectedEntry.title)
  function reuseSelectedAnalysis() {
    if (!selectedEntry) return
    updateDraft({ text: selectedEntry.text, title: selectedEntry.title, mode: selectedEntry.mode })
    clearError()
    setShowComposer(true)
  }
  const characterLimit = capabilities?.max_chars ?? 60000
  const modeAvailable = capabilities?.modes[mode] ?? false

  async function refreshCapabilities() {
    setCapabilitiesError('')
    setCapabilities(null)
    try {
      setCapabilities(await client.getCapabilities())
    } catch {
      setCapabilitiesError(CONNECTION_ERROR)
    }
  }

  function startNewAnalysis() {
    clearError()
    setShowComposer(true)
    setView('analysis')
  }

  function selectHistoryEntry(entryId: number) {
    setSelectedId(entryId)
    setShowComposer(false)
  }

  function discardDraft() {
    updateDraft({ text: '', title: '' })
    clearError()
  }

  async function submitAnalysis(inputText = text, inputTitle = title) {
    if (!inputText.trim() || Array.from(inputText).length > characterLimit || busy || !modeAvailable || !capabilities || experiment.blocked) return
    try {
      const result = await run(inputText, mode, capabilities, experiment.requestConfig)
      const entry = appendAnalysis(inputText, inputTitle, mode, result)
      setSelectedId(entry.id)
      setView('analysis')
      setShowComposer(false)
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
      <AnalysisHistoryPanel entries={entries} selectedId={selectedId} showComposer={showComposer} busy={busy}
        onNewAnalysis={startNewAnalysis} onSelectEntry={selectHistoryEntry} />
      <div className="conversation">
        <div className="analysisViewTabs" role="group" aria-label="Visualização"><button aria-pressed={view === 'analysis'} className={view === 'analysis' ? '' : 'secondary'} onClick={() => setView('analysis')}>Análise</button><button aria-pressed={view !== 'analysis'} className={view !== 'analysis' ? '' : 'secondary'} onClick={() => setView('comparison')}>Comparação</button></div>
        {view === 'analysis' ? <div className="analysisContent">
          {!showComposer && selectedEntry && <AnalysisResult entry={selectedEntry} reportClient={reportClient} reportOrigin="web">
            <div className="actions">{replacesDraft ? <ConfirmAction label="Editar e reanalisar" className="secondary" title="Substituir o rascunho atual?" description="O rascunho ainda não enviado será substituído pelo texto desta análise. Cancele para manter seu rascunho." confirmLabel="Sim, substituir rascunho" onConfirm={reuseSelectedAnalysis} /> : <button className="secondary" onClick={reuseSelectedAnalysis}>Editar e reanalisar</button>}<button className="secondary" onClick={() => setView('comparison')}>Comparar comigo</button><button className="secondary" onClick={() => setView('experiments')}>Comparar análises</button></div>
          </AnalysisResult>}
          {showComposer && <AnalysisComposer text={text} title={title} mode={mode} caps={capabilities} busy={busy} seconds={seconds} error={error} capsError={capabilitiesError}
            recipient={experiment.available ? experimentRecipients(mode, experiment.config, experiment.available) : configuredRecipients(mode, capabilities)}
            configBlocked={experiment.blocked} experimentPanel={experiment.available ? <ExperimentPanel caps={experiment.available} config={experiment.config} onChange={experiment.setConfig} mode={mode} busy={busy} error={experiment.error} notice={experiment.notice} onNotice={experiment.setNotice} client={client} onKeysUpdated={async () => setCapabilities(await client.getCapabilities())} /> : isLabBuild ? <p className="notice small">Conecte a API Lab com a configuração experimental habilitada para editar parâmetros.</p> : undefined}
            onText={text => updateDraft({ text })} onTitle={title => updateDraft({ title })} onMode={mode => updateDraft({ mode })} onSend={() => void submitAnalysis()} onCancel={cancel}
            draftNotice={draftStored && (text || title) ? 'Rascunho guardado nesta aba. Você pode navegar e voltar ou recarregar a página. Fechar a aba encerra esta sessão.' : undefined}
            onDiscard={discardDraft}
            onRetry={() => void refreshCapabilities()}
            onClose={entries.length ? () => setShowComposer(false) : undefined} />}
        </div> : <div className="analysisContent">
          <nav className="comparisonModes" aria-label="Tipo de comparação"><button className={view === 'comparison' ? '' : 'secondary'} aria-pressed={view === 'comparison'} onClick={() => setView('comparison')}>Com meu perfil</button><button className={view === 'experiments' ? '' : 'secondary'} aria-pressed={view === 'experiments'} disabled={!selectedEntry} onClick={() => setView('experiments')}>Entre análises</button></nav>
          {view === 'experiments' && selectedEntry ? <ExperimentComparison key={selectedEntry.id} entry={selectedEntry} entries={entries} /> : <ComparisonPanel profile={profile} analysis={selectedEntry?.analysis ?? null} analysisTitle={selectedEntry?.title} />}
        </div>}
      </div>
    </div>
  </main>
}
