export function extensionConfig(mode: string, env: Record<string, string>) {
  if (!['development', 'production', 'lab'].includes(mode)) throw new Error('Modo de build desconhecido.')
  if (mode === 'production' && env.VITE_APP_VARIANT === 'lab') throw new Error('Produção não permite a variante Lab.')
  const production = mode === 'production'
  const input = env.VITE_API_BASE_URL || (production ? '' : mode === 'lab' ? 'http://127.0.0.1:8001' : 'http://127.0.0.1:8000')
  if (!input) throw new Error('Defina VITE_API_BASE_URL com o host HTTPS da API antes do build de produção.')
  const api = new URL(input)
  const local = ['127.0.0.1', 'localhost'].includes(api.hostname)
  if (api.username || api.password || api.search || api.hash || api.pathname !== '/' ||
    (production ? api.protocol !== 'https:' || local : !local || !['http:', 'https:'].includes(api.protocol))) {
    throw new Error('Use somente a origem da API: localhost/127.0.0.1 no desenvolvimento e HTTPS remoto na produção.')
  }
  const web = new URL(env.VITE_WEB_BASE_URL || (production ? api.origin : mode === 'lab' ? 'http://127.0.0.1:5174' : 'http://127.0.0.1:5173'))
  if (web.username || web.password || web.search || web.hash || web.pathname !== '/' || (production && web.protocol !== 'https:') || !['http:', 'https:'].includes(web.protocol)) throw new Error('VITE_WEB_BASE_URL deve ser uma origem HTTP(S), com HTTPS na produção.')
  if (mode === 'lab' && !['127.0.0.1', 'localhost'].includes(web.hostname)) throw new Error('O site Lab deve ser local.')
  return { apiBase: api.origin, webBase: web.origin, hostPermission: `${api.protocol}//${api.hostname}/*`, webMatchPattern: `${web.protocol}//${web.hostname}/*` }
}
