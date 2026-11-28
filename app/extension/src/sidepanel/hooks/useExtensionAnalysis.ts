import { useRef } from 'react'
import type { Capabilities } from '@8values/shared/api'
import type { ExperimentConfig } from '@8values/shared/domain/experimentConfig'
import { useAnalysisRequest } from '@8values/shared/hooks/useAnalysisRequest'
import { client } from '../../config'
import type { useExtensionSession } from './useExtensionSession'

type RequestOptions = {
  session: ReturnType<typeof useExtensionSession>
  capabilities: Capabilities | null
  experimentConfig?: ExperimentConfig
  configBlocked: boolean
}

/** Conecta o envio e cancelamento de análises ao estado persistido do painel. */
export function useExtensionAnalysis({ session, capabilities, experimentConfig, configBlocked }: RequestOptions) {
  const owner = useRef(crypto.randomUUID())
  const cancelRequested = useRef(false)
  const request = useAnalysisRequest(client)

  /** Valida a sessão, salva o texto em processamento e associa o resultado à tentativa correta. */
  async function submitAnalysis() {
    const current = session.getCurrentSession()
    if (!session.isReady() || current.request || !capabilities || !capabilities.modes[current.mode] || !current.draft.text.trim() || Array.from(current.draft.text).length > capabilities.max_chars || configBlocked) return
    const analysisSnapshot = { ...current.draft, id: crypto.randomUUID(), owner: owner.current, mode: current.mode, startedAt: Date.now() }
    cancelRequested.current = false
    const started = session.updateSession({ type: 'begin', request: analysisSnapshot })
    // Persist the in-flight snapshot before starting HTTP, so a reload can recover it.
    try {
      await session.saveSnapshot(started)
    } catch {
      if (session.isPanelOpen()) session.setStorageError('A análise pode ser feita, mas o texto não foi guardado. Mantenha o painel aberto.')
    }
    if (!session.isPanelOpen()) return
    if (cancelRequested.current) {
      session.updateSession({ type: 'failure', id: analysisSnapshot.id, message: 'Análise cancelada. O texto foi preservado.' })
      return
    }
    try {
      const result = await request.run(analysisSnapshot.text, analysisSnapshot.mode, capabilities, experimentConfig)
      if (session.isPanelOpen()) session.updateSession({ type: 'success', id: analysisSnapshot.id, analysis: result })
    } catch (err) {
      if (session.isPanelOpen()) session.updateSession({ type: 'failure', id: analysisSnapshot.id, message: err instanceof Error ? err.message : 'Falha na análise.' })
    }
  }

  /** Sinaliza o cancelamento mesmo antes de a gravação inicial permitir o envio HTTP. */
  function cancelAnalysis() {
    cancelRequested.current = true
    request.cancel()
  }

  return {
    busy: request.busy,
    seconds: request.seconds,
    error: request.error,
    clearError: request.clearError,
    submitAnalysis,
    cancelAnalysis,
  }
}
