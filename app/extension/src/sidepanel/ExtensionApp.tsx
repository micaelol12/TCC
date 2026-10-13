import { useEffect, useRef, useState } from 'react'
import AnalysisComposer from '@8values/shared/components/AnalysisComposer'
import AnalysisResult from '@8values/shared/components/AnalysisResult'
import ComparisonPanel from '@8values/shared/components/ComparisonPanel'
import { modeLabels, type Capabilities } from '@8values/shared/api'
import { useAnalysisRequest } from '@8values/shared/hooks/useAnalysisRequest'
import { validateProfile, type Profile } from '@8values/shared/profile'
import { API_BASE_URL, WEB_BASE_URL, client } from '../config'
import { captureKey, sessionKey, isCapture, type Capture } from '../platform/selection'
import { emptySession, hydrateSession, reduceSession, fitSession, type Action, type Session } from '../storage/sessionState'
import { createSessionStore } from '../storage/sessionStore'
import { readPreferences, saveMode, saveProfile, TEMP_PROFILE_KEY, LOCAL_PROFILE_KEY } from '../storage/preferences'

export default function ExtensionApp() {
  const [state, setState] = useState<Session>(emptySession)
  const stateRef = useRef(state)
  const [ready, setReady] = useState(false)
  const readyRef = useRef(false)
  const [storageError, setStorageError] = useState('')
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [capsError, setCapsError] = useState('')
  const [profile, setProfile] = useState<Profile | null>(null)
  const [profileStored, setProfileStored] = useState(false)
  const [permanent, setPermanent] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [profileBusy, setProfileBusy] = useState(false)
  const [tab, setTab] = useState<'analysis' | 'comparison'>('analysis')
  const windowId = useRef<number | null>(null)
  const store = useRef<ReturnType<typeof createSessionStore> | null>(null)
  const mounted = useRef(true)
  const owner = useRef(crypto.randomUUID())
  const cancelRequested = useRef(false)
  const { busy, seconds, error, run, cancel, clearError } = useAnalysisRequest(client)

  function update(action: Action) {
    const reduced = reduceSession(stateRef.current, action)
    let next = reduced
    try {
      const fitted = fitSession(reduced)
      next = fitted.state
      if (fitted.trimmed) setStorageError('Entradas antigas foram removidas para manter o espaço temporário disponível.')
    } catch (err) { setStorageError(err instanceof Error ? err.message : 'Não foi possível guardar estes dados.') }
    stateRef.current = next
    if (mounted.current) setState(next)
    return next
  }

  useEffect(() => {
    mounted.current = true
    const pendingEvents: Capture[] = []
    const receive = (capture: Capture) => {
      if (capture.windowId !== windowId.current) return
      if (!readyRef.current) pendingEvents.push(capture)
      else { update({ type: 'capture', capture }); setTab('analysis') }
    }
    const onStorage = (changes: Record<string, chrome.storage.StorageChange>, area: string) => {
      if (area !== 'session' || windowId.current === null) return
      const capture = changes[captureKey(windowId.current)]?.newValue
      if (isCapture(capture)) receive(capture)
    }
    const onMessage = (message: unknown) => {
      const data = message as { type?: string; capture?: Capture; windowId?: number }
      if (data?.type === 'capture-storage-failed' && data.windowId === windowId.current && isCapture(data.capture)) {
        setStorageError('Não foi possível guardar a seleção. Ela ficará apenas neste painel.'); receive(data.capture)
      }
    }
    // Subscribe before reading to avoid losing a capture while hydrating.
    chrome.storage.onChanged.addListener(onStorage)
    chrome.runtime.onMessage.addListener(onMessage)
    void (async () => {
      try {
        const current = await chrome.windows.getCurrent()
        if (!mounted.current || current.id === undefined) return
        windowId.current = current.id
        store.current = createSessionStore(current.id)
        const preferences = await readPreferences().catch(() => ({ mode: 'medium' as const, profile: null }))
        const keys = [sessionKey(current.id), captureKey(current.id), TEMP_PROFILE_KEY]
        const saved = await chrome.storage.session.get(keys)
        if (!mounted.current) return
        let next = hydrateSession(saved[sessionKey(current.id)], preferences.mode)
        const initial = saved[captureKey(current.id)]
        const captures = [...pendingEvents, ...(isCapture(initial) ? [initial] : [])].sort((a, b) => a.createdAt - b.createdAt)
        for (const capture of captures) next = reduceSession(next, { type: 'capture', capture })
        stateRef.current = next; setState(next)
        const temporaryProfile = validateProfile(saved[TEMP_PROFILE_KEY])
        setProfile(temporaryProfile ?? preferences.profile)
        setProfileStored(!temporaryProfile && !!preferences.profile)
      } catch {
        setStorageError('Armazenamento indisponível. Os dados permanecerão apenas enquanto este painel estiver aberto.')
        let next = stateRef.current
        for (const capture of pendingEvents) next = reduceSession(next, { type: 'capture', capture })
        stateRef.current = next; setState(next)
      } finally { if (mounted.current) { readyRef.current = true; setReady(true) } }
    })()
    return () => { mounted.current = false; readyRef.current = false; chrome.storage.onChanged.removeListener(onStorage); chrome.runtime.onMessage.removeListener(onMessage) }
  }, [])

  useEffect(() => {
    if (!ready || !store.current) return
    try { void store.current.save(state).catch(() => { if (mounted.current) setStorageError('Falha ao guardar os dados temporários. Mantenha o painel aberto para preservar o texto.') }) }
    catch (err) { setStorageError(err instanceof Error ? err.message : 'Falha no armazenamento.') }
  }, [ready, state])

  useEffect(() => {
    let generation = 0
    const syncProfile = async (changes: Record<string, chrome.storage.StorageChange>, area: string) => {
      if (!(area === 'local' && changes[LOCAL_PROFILE_KEY]) && !(area === 'session' && changes[TEMP_PROFILE_KEY])) return
      const revision = ++generation
      try {
        const [preferences, temporary] = await Promise.all([readPreferences(), chrome.storage.session.get(TEMP_PROFILE_KEY)])
        if (!mounted.current || revision !== generation) return
        const current = validateProfile(temporary[TEMP_PROFILE_KEY])
        setProfile(current ?? preferences.profile); setProfileStored(!current && !!preferences.profile)
      } catch { /* keep the last usable profile until storage recovers */ }
    }
    chrome.storage.onChanged.addListener(syncProfile)
    return () => { generation++; chrome.storage.onChanged.removeListener(syncProfile) }
  }, [])

  const capsController = useRef<AbortController | null>(null)
  async function refreshCapabilities() {
    capsController.current?.abort()
    const controller = new AbortController(); capsController.current = controller
    setCaps(null); setCapsError('')
    try { const available = await client.getCapabilities(controller.signal); if (mounted.current && !controller.signal.aborted) setCaps(available) }
    catch { if (mounted.current && !controller.signal.aborted) setCapsError('API indisponível. Inicie o servidor e verifique a conexão.') }
  }
  useEffect(() => { void refreshCapabilities(); return () => capsController.current?.abort() }, [])

  async function send() {
    const current = stateRef.current
    if (!readyRef.current || current.request || !caps || !caps.modes[current.mode] || !current.draft.text.trim() || Array.from(current.draft.text).length > caps.max_chars) return
    const request = { ...current.draft, id: crypto.randomUUID(), owner: owner.current, mode: current.mode, startedAt: Date.now() }
    cancelRequested.current = false
    const started = update({ type: 'begin', request })
    // Persist the in-flight snapshot before starting HTTP, so a reload can recover it.
    if (store.current) {
      try { await store.current.save(started) }
      catch { if (mounted.current) setStorageError('A análise pode ser feita, mas o texto não foi guardado. Mantenha o painel aberto.') }
    }
    if (!mounted.current) return
    if (cancelRequested.current) { update({ type: 'failure', id: request.id, message: 'Análise cancelada. O texto foi preservado.' }); return }
    try {
      const result = await run(request.text, request.mode, caps)
      if (mounted.current) update({ type: 'success', id: request.id, analysis: result })
    } catch (err) {
      if (mounted.current) update({ type: 'failure', id: request.id, message: err instanceof Error ? err.message : 'Falha na análise.' })
    }
  }

  async function importProfile(file?: File) {
    if (!file) return
    setProfileError(''); setProfileBusy(true)
    try {
      if (file.size > 10000) throw new Error('Arquivo de perfil acima do limite de 10 KB.')
      const parsed = validateProfile(JSON.parse(await file.text()))
      if (!parsed) throw new Error('Perfil inválido ou de outra versão do questionário. Exporte novamente pelo site.')
      await saveProfile(parsed, permanent)
      setProfile(parsed); setProfileStored(permanent)
    } catch (err) { setProfileError(err instanceof Error ? err.message : 'Não foi possível importar o perfil.') }
    finally { setProfileBusy(false) }
  }
  async function deleteProfile() {
    setProfileBusy(true); setProfileError('')
    try { await saveProfile(null, false); setProfile(null); setProfileStored(false) }
    catch { setProfileError('Não foi possível apagar o perfil guardado. Tente novamente.') }
    finally { setProfileBusy(false) }
  }
  const selected = state.entries.find(entry => entry.id === state.selectedId) ?? null
  const isBusy = busy || !!state.request
  return <>
    <a className="skipLink" href="#panel-content">Pular para o conteúdo</a>
    <header className="panelHeader"><div className="brand"><span className="brandMark">8</span><span>valores <span className="brandPlus">+ textos</span></span></div><button className="secondary" disabled={!ready || isBusy} onClick={() => { update({ type: 'compose' }); clearError(); setTab('analysis') }}>+ Nova</button></header>
    <main id="panel-content" className="panelMain analysisContent">
      <div className="eyebrow">Leitura crítica · quatro eixos</div><h1>Analise um trecho</h1>
      <p className="muted small">Selecione um texto na página e use “Analisar com 8values” no botão direito.</p>
      <p className="aiDisclaimer small">A IA pode cometer erros. Confira o texto, a cobertura e as evidências.</p>
      {!ready && <p role="status">Carregando os dados desta sessão…</p>}
      {storageError && <p className="notice small" role="status">{storageError}</p>}
      {state.pending && <section className="notice" aria-label="Nova seleção"><strong>Você selecionou outro trecho.</strong><p className="pendingPreview">{state.pending.text.slice(0, 180)}{state.pending.text.length > 180 ? '…' : ''}</p><div className="actions"><button disabled={isBusy} onClick={() => { update({ type: 'use-pending' }); clearError(); setTab('analysis') }}>Usar nova seleção</button><button className="secondary" onClick={() => update({ type: 'ignore-pending' })}>Manter rascunho</button></div>{isBusy && <p className="small">A análise em andamento mantém o trecho anterior.</p>}</section>}
      <nav className="panelTabs" aria-label="Visualização"><button className={tab === 'analysis' ? '' : 'secondary'} aria-pressed={tab === 'analysis'} onClick={() => setTab('analysis')}>Análise</button><button className={tab === 'comparison' ? '' : 'secondary'} aria-pressed={tab === 'comparison'} onClick={() => setTab('comparison')}>Comparação</button></nav>
      {tab === 'analysis' ? <>
        {ready && state.showComposer && <AnalysisComposer text={state.draft.text} title={state.draft.title} source={state.draft.source} mode={state.mode} caps={caps} busy={isBusy} seconds={seconds} error={state.notice || error} capsError={capsError}
          onText={text => update({ type: 'edit', draft: { text } })} onTitle={title => update({ type: 'edit', draft: { title } })}
          onMode={mode => { update({ type: 'mode', mode }); void saveMode(mode).catch(() => setStorageError('Não foi possível guardar o modo preferido.')) }}
          onSend={() => void send()} onCancel={() => { cancelRequested.current = true; cancel() }} onRetry={() => void refreshCapabilities()} onClose={selected ? () => update({ type: 'close-composer' }) : undefined} />}
        {!state.showComposer && selected && <AnalysisResult entry={selected} compact><div className="actions"><button className="secondary" onClick={() => { update({ type: 'reuse', entry: selected }); clearError() }}>Editar e reanalisar</button><button className="secondary" onClick={() => setTab('comparison')}>Comparar comigo</button></div></AnalysisResult>}
        <details className="sessionHistory"><summary>Histórico desta sessão ({state.entries.length})</summary>{state.entries.length ? <ul>{state.entries.map(entry => <li key={entry.id}><button className="secondary historyEntry" aria-pressed={entry.id === state.selectedId && !state.showComposer} disabled={isBusy} onClick={() => { update({ type: 'select', id: entry.id }); clearError() }}>{entry.title}<span>{modeLabels[entry.mode]}</span></button></li>)}</ul> : <p className="muted small">Nenhuma análise nesta sessão.</p>}
          <p className="muted small">Até 10 análises, com limite de espaço. Os dados temporários são removidos ao reiniciar o navegador ou recarregar a extensão.</p>
          <button className="danger" disabled={!ready || isBusy} onClick={() => { update({ type: 'clear' }); clearError(); setStorageError(''); if (windowId.current !== null) void chrome.storage.session.remove(captureKey(windowId.current)).catch(() => setStorageError('Não foi possível apagar a seleção temporária.')) }}>Limpar histórico e rascunhos</button>
        </details>
      </> : <>
        <ComparisonPanel profile={profile} analysis={selected?.analysis ?? null} profileAction={<a className="button secondary" href={`${WEB_BASE_URL}/teste`} target="_blank" rel="noreferrer">Fazer meu teste no site</a>} />
        <section className="profileSettings" aria-label="Perfil pessoal"><h2>Meu perfil local</h2><p className="muted small">No site, abra “Meu resultado” e exporte o perfil. Importe o JSON aqui para comparar; ele fica neste navegador.</p>
          {profile && <><p role="status" className="small">{profileStored ? 'Perfil salvo localmente nesta extensão.' : 'Perfil temporário nesta sessão.'}</p><button className="danger" disabled={profileBusy} onClick={() => void deleteProfile()}>Apagar perfil</button></>}
          <label className="check"><input type="checkbox" checked={permanent} onChange={e => setPermanent(e.target.checked)} disabled={profileBusy} />Salvar o próximo perfil neste navegador</label>
          <label htmlFor="profile-file">Importar perfil JSON</label><input id="profile-file" type="file" accept="application/json,.json" disabled={profileBusy || !ready} onChange={e => { void importProfile(e.target.files?.[0]); e.target.value = '' }} />
          {profileError && <p className="error" role="alert">{profileError}</p>}
        </section>
      </>}
    </main><footer className="panelFooter"><span>Projeto acadêmico · baseado no <a href="https://8values.github.io/" target="_blank" rel="noreferrer">8values</a></span><details><summary>Conexão e dados</summary><p>API: {API_BASE_URL}</p><p>Selecionar texto não o envia. A análise envia o trecho revisado aos serviços indicados no modo escolhido. Perfil, domínio de origem e histórico não fazem parte do envio. A retenção dos serviços externos depende de suas políticas.</p></details></footer>
  </>
}
