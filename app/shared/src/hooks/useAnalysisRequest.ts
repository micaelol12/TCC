import { useCallback, useEffect, useRef, useState } from 'react'
import { createAnalysisClient, type Capabilities, type Mode } from '../api/analysisApi'
import type { ExperimentConfig } from '../domain/experimentConfig'

export function useAnalysisRequest(client: ReturnType<typeof createAnalysisClient>) {
  const [busy, setBusy] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [error, setError] = useState('')
  const active = useRef<AbortController | null>(null)
  const mounted = useRef(true)
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; active.current?.abort() } }, [])
  useEffect(() => { if (!busy) return; const timer = window.setInterval(() => setSeconds(s => s + 1), 1000); return () => clearInterval(timer) }, [busy])
  const run = useCallback(async (text: string, mode: Mode, caps: Capabilities, experimentConfig?: ExperimentConfig) => {
    if (active.current) throw new Error('Uma análise já está em andamento.')
    const controller = new AbortController()
    active.current = controller
    setBusy(true); setSeconds(0); setError('')
    try { return await client.analyze(text, mode, controller.signal, caps.timeout_seconds, experimentConfig) }
    catch (err) {
      const message = controller.signal.aborted ? 'Análise cancelada. O texto foi preservado.' : err instanceof Error ? err.message : 'Falha na análise. O texto foi preservado.'
      if (mounted.current) setError(message)
      throw new Error(message)
    } finally { if (mounted.current) setBusy(false); if (active.current === controller) active.current = null }
  }, [client])
  return { busy, seconds, error, run, cancel: () => active.current?.abort(), clearError: () => setError('') }
}
