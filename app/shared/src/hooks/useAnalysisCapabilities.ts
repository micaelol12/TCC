import { useCallback, useEffect, useRef, useState } from 'react'
import type { Capabilities, createAnalysisClient } from '../api/analysisApi'
import { CONNECTION_ERROR } from '../domain/analysisMessages'

/** Mantém os modos disponíveis e o estado de conexão, cancelando consultas substituídas. */
export function useAnalysisCapabilities(client: ReturnType<typeof createAnalysisClient>) {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null)
  const [capabilitiesError, setCapabilitiesError] = useState('')
  const activeRequest = useRef<AbortController | null>(null)

  /** Substitui a consulta anterior e atualiza capacidades ou erro enquanto a chamada estiver ativa. */
  const refreshCapabilities = useCallback(async () => {
    activeRequest.current?.abort()
    const controller = new AbortController()
    activeRequest.current = controller
    setCapabilities(null)
    setCapabilitiesError('')
    try {
      const available = await client.getCapabilities(controller.signal)
      if (!controller.signal.aborted) setCapabilities(available)
    } catch {
      if (!controller.signal.aborted) setCapabilitiesError(CONNECTION_ERROR)
    }
  }, [client])

  useEffect(() => {
    void refreshCapabilities()

    return () => activeRequest.current?.abort()
  }, [refreshCapabilities])

  return { capabilities, capabilitiesError, refreshCapabilities, setCapabilities }
}
