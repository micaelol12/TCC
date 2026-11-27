import { useCallback, useState } from 'react'
import { experimentRecipients, isLabBuild } from '@8values/shared/domain/experimentConfig'
import { configuredRecipients } from '@8values/shared/api'
import AnalysisComposer from '@8values/shared/components/AnalysisComposer'
import AnalysisResult from '@8values/shared/components/AnalysisResult'
import ComparisonPanel from '@8values/shared/components/ComparisonPanel'
import ExperimentPanel from '@8values/shared/components/ExperimentPanel'
import ExperimentComparison from '@8values/shared/components/ExperimentComparison'
import AnalysisResultActions from '@8values/shared/components/AnalysisResultActions'
import { useAnalysisCapabilities } from '@8values/shared/hooks/useAnalysisCapabilities'
import { useExperimentConfig } from '@8values/shared/hooks/useExperimentConfig'
import { API_BASE_URL, WEB_BASE_URL, client, reportClient } from '../config'
import { saveMode } from '../storage/preferences'
import { useExtensionSession } from './hooks/useExtensionSession'
import { useExtensionProfile } from './hooks/useExtensionProfile'
import { useExtensionAnalysis } from './hooks/useExtensionAnalysis'
import ExtensionHistory from './components/ExtensionHistory'
import ExtensionProfileSettings from './components/ExtensionProfileSettings'
import ExtensionFooter from './components/ExtensionFooter'
import PendingCaptureNotice from './components/PendingCaptureNotice'

/** Integra análise, capturas pendentes, perfil e comparações no painel lateral. */
export default function ExtensionApp() {
  const [activeView, setActiveView] = useState<'analysis' | 'comparison' | 'experiments'>('analysis')
  const showAnalysis = useCallback(() => setActiveView('analysis'), [])
  const { profile, setProfile, profileError, profileBusy, importProfile, deleteProfile } = useExtensionProfile()
  const session = useExtensionSession({ onCapture: showAnalysis, onProfileLoaded: setProfile })
  const { sessionState, ready, storageError, setStorageError, updateSession } = session
  const { capabilities, capabilitiesError, refreshCapabilities, setCapabilities } = useAnalysisCapabilities(client)
  const experiment = useExperimentConfig(capabilities, API_BASE_URL, sessionState.mode)
  const { busy, seconds, error, submitAnalysis, cancelAnalysis, clearError } = useExtensionAnalysis({
    session, capabilities, experimentConfig: experiment.requestConfig, configBlocked: experiment.blocked,
  })

  /** Limpa a sessão persistida e depois remove a mensagem de erro da análise. */
  async function clearSession() {
    await session.clearSession()
    clearError()
  }
  /** Abre uma análise do histórico e limpa o erro anterior. */
  function selectHistoryEntry(entryId: string) {
    updateSession({ type: 'select', id: entryId })
    clearError()
  }

  /** Usa a seleção pendente no rascunho e retorna à visualização de análise. */
  function applyPendingCapture() {
    updateSession({ type: 'use-pending' })
    clearError()
    setActiveView('analysis')
  }

  /** Abre a composição e retorna à aba de análise. */
  function startNewAnalysis() {
    updateSession({ type: 'compose' })
    clearError()
    setActiveView('analysis')
  }

  /** Esvazia texto, título e origem do rascunho sem remover o histórico. */
  function discardDraft() {
    updateSession({ type: 'edit', draft: { text: '', title: '', source: undefined } })
    clearError()
  }

  const selectedEntry = sessionState.entries.find(entry => entry.id === sessionState.selectedId) ?? null
  const isBusy = busy || !!sessionState.request
  const replacesDraft = !!selectedEntry && !!(sessionState.draft.text || sessionState.draft.title) && (sessionState.draft.text !== selectedEntry.text || sessionState.draft.title !== selectedEntry.title)
  /** Reabre a análise selecionada como rascunho para um novo envio. */
  function reuseSelectedAnalysis() {
    if (!selectedEntry) return
    updateSession({ type: 'reuse', entry: selectedEntry })
    clearError()
  }
  return <>
    <a className="skipLink" href="#panel-content">Pular para o conteúdo</a>
    <header className="panelHeader"><div className="brand"><span className="brandMark">8</span><span>valores <span className="brandPlus">+ textos</span></span></div><button className="secondary" disabled={!ready || isBusy} onClick={startNewAnalysis}>+ Nova</button></header>
    <main id="panel-content" className="panelMain analysisContent">
      {isLabBuild && <p className="labBadge">8values Lab · Versão de teste</p>}
      <div className="eyebrow">Leitura crítica · quatro eixos</div><h1>Analise um trecho</h1>
      <p className="muted small">Selecione um texto na página e use “Analisar com 8values” no botão direito.</p>
      <p className="aiDisclaimer small">A IA pode cometer erros. Confira o texto, a cobertura e as evidências.</p>
      {!ready && <p role="status">Carregando os dados desta sessão…</p>}
      {storageError && <p className="notice small" role="status">{storageError}</p>}
      {sessionState.pending && <PendingCaptureNotice capture={sessionState.pending} busy={isBusy} onUseCapture={applyPendingCapture} onKeepDraft={() => updateSession({ type: 'ignore-pending' })} />}
      <nav className="panelTabs" aria-label="Visualização"><button className={activeView === 'analysis' ? '' : 'secondary'} aria-pressed={activeView === 'analysis'} onClick={() => setActiveView('analysis')}>Análise</button><button className={activeView !== 'analysis' ? '' : 'secondary'} aria-pressed={activeView !== 'analysis'} onClick={() => setActiveView('comparison')}>Comparação</button></nav>
      {activeView === 'analysis' ? <>
        {ready && sessionState.showComposer && <AnalysisComposer text={sessionState.draft.text} title={sessionState.draft.title} source={sessionState.draft.source} mode={sessionState.mode} caps={capabilities} busy={isBusy} seconds={seconds} error={sessionState.notice || error} capsError={capabilitiesError}
          recipient={experiment.available ? experimentRecipients(sessionState.mode, experiment.config, experiment.available) : configuredRecipients(sessionState.mode, capabilities)}
          configBlocked={experiment.blocked} experimentPanel={experiment.available ? <ExperimentPanel collapsible capabilities={experiment.available} config={experiment.config} onChange={experiment.setConfig} mode={sessionState.mode} busy={isBusy} error={experiment.error} notice={experiment.notice} onNotice={experiment.setNotice} client={client} onKeysUpdated={async () => setCapabilities(await client.getCapabilities())} /> : isLabBuild ? <p className="notice small">Conecte a API Lab com a configuração experimental habilitada para editar parâmetros.</p> : undefined}
          onText={text => updateSession({ type: 'edit', draft: { text } })} onTitle={title => updateSession({ type: 'edit', draft: { title } })}
          onDiscard={discardDraft}
          onMode={mode => { updateSession({ type: 'mode', mode }); void saveMode(mode).catch(() => setStorageError('Não foi possível guardar o modo preferido.')) }}
          onSend={() => void submitAnalysis()} onCancel={cancelAnalysis} onRetry={() => void refreshCapabilities()} onClose={selectedEntry ? () => updateSession({ type: 'close-composer' }) : undefined} />}
        {!sessionState.showComposer && selectedEntry && <AnalysisResult entry={selectedEntry} reportClient={reportClient} reportOrigin="extension" compact><AnalysisResultActions replacesDraft={replacesDraft} onReuseAnalysis={reuseSelectedAnalysis} onCompareProfile={() => setActiveView('comparison')} onCompareAnalyses={() => setActiveView('experiments')} /></AnalysisResult>}
        <ExtensionHistory session={sessionState} ready={ready} busy={isBusy} onSelect={selectHistoryEntry} onClear={clearSession} />
      </> : <>
        <nav className="comparisonModes" aria-label="Tipo de comparação"><button className={activeView === 'comparison' ? '' : 'secondary'} aria-pressed={activeView === 'comparison'} onClick={() => setActiveView('comparison')}>Com meu perfil</button><button className={activeView === 'experiments' ? '' : 'secondary'} aria-pressed={activeView === 'experiments'} disabled={!selectedEntry} onClick={() => setActiveView('experiments')}>Entre análises</button></nav>
        {activeView === 'experiments' && selectedEntry ? <ExperimentComparison key={selectedEntry.id} entry={selectedEntry} entries={sessionState.entries} /> : <>
        <ComparisonPanel profile={profile} analysis={selectedEntry?.analysis ?? null} analysisTitle={selectedEntry?.title} profileAction={<a className="button secondary" href={`${WEB_BASE_URL}/teste`} target="_blank" rel="noreferrer">Fazer meu teste no site</a>} />
        <ExtensionProfileSettings profile={profile} ready={ready} busy={profileBusy} error={profileError} onImport={importProfile} onDelete={deleteProfile} />
        </>}
      </>}
    </main><ExtensionFooter />
  </>
}
