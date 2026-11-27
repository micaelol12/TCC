import { useCallback, useEffect, useRef, useState } from 'react'
import type { Profile } from '@8values/shared/profile'
import { captureKey, sessionKey, isCapture, type Capture } from '../../platform/selection'
import { emptySession, hydrateSession, reduceSession, fitSession, type Action, type Session } from '../../storage/sessionState'
import { createSessionStore } from '../../storage/sessionStore'
import { readPreferences } from '../../storage/preferences'

type SessionCallbacks = { onCapture: () => void; onProfileLoaded: (profile: Profile | null) => void }

/** Coordena restauração, capturas e persistência da sessão da janela do navegador. */
export function useExtensionSession({ onCapture, onProfileLoaded }: SessionCallbacks) {
  const [sessionState, setSessionState] = useState<Session>(emptySession)
  const sessionRef = useRef(sessionState)
  const [ready, setReady] = useState(false)
  const isReadyRef = useRef(false)
  const [storageError, setStorageError] = useState('')
  const windowIdRef = useRef<number | null>(null)
  const sessionStore = useRef<ReturnType<typeof createSessionStore> | null>(null)
  const isMountedRef = useRef(true)

  /** Aplica a ação, ajusta o histórico ao espaço disponível e sincroniza estado e referência. */
  const updateSession = useCallback((action: Action) => {
    const reducedSession = reduceSession(sessionRef.current, action)
    let nextSession = reducedSession
    try {
      const fittedSession = fitSession(reducedSession)
      nextSession = fittedSession.state
      if (fittedSession.trimmed) setStorageError('Entradas antigas foram removidas para manter o espaço temporário disponível.')
    } catch (err) { setStorageError(err instanceof Error ? err.message : 'Não foi possível guardar estes dados.') }
    sessionRef.current = nextSession
    if (isMountedRef.current) setSessionState(nextSession)
    return nextSession
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    const pendingEvents: Capture[] = []
    /** Enfileira capturas durante a restauração e aplica apenas as destinadas à janela atual. */
    const receive = (capture: Capture) => {
      if (capture.windowId !== windowIdRef.current) return
      if (!isReadyRef.current) pendingEvents.push(capture)
      else { updateSession({ type: 'capture', capture }); onCapture() }
    }
    /** Recebe novas capturas persistidas na sessão desta janela. */
    const onStorage = (changes: Record<string, chrome.storage.StorageChange>, area: string) => {
      if (area !== 'session' || windowIdRef.current === null) return
      const capture = changes[captureKey(windowIdRef.current)]?.newValue
      if (isCapture(capture)) receive(capture)
    }
    /** Recupera uma seleção entregue por mensagem quando sua gravação temporária falhou. */
    const onMessage = (message: unknown) => {
      const data = message as { type?: string; capture?: Capture; windowId?: number }
      if (data?.type === 'capture-storage-failed' && data.windowId === windowIdRef.current && isCapture(data.capture)) {
        setStorageError('Não foi possível guardar a seleção. Ela ficará apenas neste painel.'); receive(data.capture)
      }
    }
    // Subscribe before reading to avoid losing a capture while hydrating.
    chrome.storage.onChanged.addListener(onStorage)
    chrome.runtime.onMessage.addListener(onMessage)
    /** Restaura preferências e histórico e reaplica capturas recebidas durante a inicialização. */
    async function restoreSavedSession() {
      try {
        const current = await chrome.windows.getCurrent()
        if (!isMountedRef.current || current.id === undefined) return
        windowIdRef.current = current.id
        sessionStore.current = createSessionStore(current.id)
        const preferences = await readPreferences().catch(() => ({ mode: 'medium' as const, profile: null }))
        const keys = [sessionKey(current.id), captureKey(current.id)]
        const saved = await chrome.storage.session.get(keys)
        if (!isMountedRef.current) return
        let nextSession = hydrateSession(saved[sessionKey(current.id)], preferences.mode)
        const initial = saved[captureKey(current.id)]
        const captures = [...pendingEvents, ...(isCapture(initial) ? [initial] : [])].sort((a, b) => a.createdAt - b.createdAt)
        for (const capture of captures) nextSession = reduceSession(nextSession, { type: 'capture', capture })
        sessionRef.current = nextSession; setSessionState(nextSession)
        onProfileLoaded(preferences.profile)
      } catch {
        setStorageError('Armazenamento indisponível. Os dados permanecerão apenas enquanto este painel estiver aberto.')
        let nextSession = sessionRef.current
        for (const capture of pendingEvents) nextSession = reduceSession(nextSession, { type: 'capture', capture })
        sessionRef.current = nextSession; setSessionState(nextSession)
      } finally { if (isMountedRef.current) { isReadyRef.current = true; setReady(true) } }
    }
    void restoreSavedSession()
    return () => { isMountedRef.current = false; isReadyRef.current = false; chrome.storage.onChanged.removeListener(onStorage); chrome.runtime.onMessage.removeListener(onMessage) }
  }, [onCapture, onProfileLoaded, updateSession])

  useEffect(() => {
    if (!ready || !sessionStore.current) return
    try { void sessionStore.current.save(sessionState).catch(() => { if (isMountedRef.current) setStorageError('Falha ao guardar os dados temporários. Mantenha o painel aberto para preservar o texto.') }) }
    catch (err) { setStorageError(err instanceof Error ? err.message : 'Falha no armazenamento.') }
  }, [ready, sessionState])

  /** Confirma a limpeza persistida antes de apagar o histórico exibido no painel. */
  async function clearSession() {
    if (!isReadyRef.current || sessionRef.current.request) throw new Error('Aguarde ou cancele a análise antes de limpar o histórico.')
    const nextSession = reduceSession(sessionRef.current, { type: 'clear' })
    // Wait for earlier saves and confirm the deletion before changing the screen.
    try {
      if (sessionStore.current) await sessionStore.current.save(nextSession)
      if (windowIdRef.current !== null) await chrome.storage.session.remove(captureKey(windowIdRef.current))
    } catch { throw new Error('Não foi possível limpar todos os dados desta janela. Verifique o armazenamento do navegador e tente novamente.') }
    updateSession({ type: 'clear' })
    setStorageError('')
  }

  /** Aguarda a gravação do estado que permite recuperar uma análise interrompida. */
  async function saveSnapshot(snapshot: Session) {
    if (sessionStore.current) await sessionStore.current.save(snapshot)
  }

  return {
    sessionState, ready, storageError, setStorageError, updateSession, clearSession, saveSnapshot,
    getCurrentSession: () => sessionRef.current,
    isReady: () => isReadyRef.current,
    isPanelOpen: () => isMountedRef.current,
  }
}
