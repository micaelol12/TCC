import { useCallback, useEffect, useRef, useState } from 'react'
import { createAnalysisClient, type Capabilities, type Mode } from '../api/analysisApi'
import type { ExperimentConfig } from '../domain/experimentConfig'

export function useAnalysisRequest(client: ReturnType<typeof createAnalysisClient>) {
  const [busy, setBusy] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [error, setError] = useState('')
  const activeRequest = useRef<AbortController | null>(null)
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
      activeRequest.current?.abort()
    }
  }, [])

  useEffect(() => {
    if (!busy) return
    const elapsedTimeTimer = window.setInterval(() => setSeconds(seconds => seconds + 1), 1000)
    return () => clearInterval(elapsedTimeTimer)
  }, [busy])

  const run = useCallback(async (text: string, mode: Mode, capabilities: Capabilities, experimentConfig?: ExperimentConfig) => {
    if (activeRequest.current) throw new Error('Uma análise já está em andamento.')
    const controller = new AbortController()
    activeRequest.current = controller
    setBusy(true)
    setSeconds(0)
    setError('')
    try {
      return await client.analyze(text, mode, controller.signal, capabilities.timeout_seconds, experimentConfig)
    } catch (error) {
      const message = controller.signal.aborted
        ? 'Análise cancelada. O texto foi preservado.'
        : error instanceof Error ? error.message : 'Falha na análise. O texto foi preservado.'
      if (isMounted.current) setError(message)
      throw new Error(message)
    } finally {
      if (isMounted.current) setBusy(false)
      if (activeRequest.current === controller) activeRequest.current = null
    }
  }, [client])

  return { busy, seconds, error, run, cancel: () => activeRequest.current?.abort(), clearError: () => setError('') }
}
