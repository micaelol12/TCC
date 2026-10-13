// Standalone content script: no imports, page data reads, or automatic transfer.
(() => {
  const origin = __WEB_ORIGIN__
  // Match patterns ignore ports; enforce the configured origin here as well.
  if (location.origin !== origin || window !== window.top) return
  window.addEventListener('message', async event => {
    const data = event.data
    if (event.source !== window || event.origin !== origin || data?.type !== '8values:save-profile' ||
      typeof data.requestId !== 'string' || data.requestId.length > 100) return
    let response
    try {
      response = await chrome.runtime.sendMessage({ type: data.type, profile: data.profile, permanent: data.permanent })
    } catch {
      response = { ok: false, error: 'A conexão com a extensão foi interrompida. Recarregue esta página e tente novamente.' }
    }
    window.postMessage({ type: '8values:save-profile-result', requestId: data.requestId,
      ok: response?.ok === true, error: response?.error }, origin)
  })
})()
