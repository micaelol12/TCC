import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const lab = mode === 'lab'
  if (mode === 'production' && env.VITE_APP_VARIANT === 'lab') throw new Error('Produção não permite a variante Lab.')
  const api = new URL(env.VITE_API_BASE_URL || (lab ? 'http://127.0.0.1:8001' : 'http://127.0.0.1:8000'))
  if (lab && (!['localhost', '127.0.0.1'].includes(api.hostname) || !['http:', 'https:'].includes(api.protocol) || api.pathname !== '/' || api.username || api.password || api.search || api.hash)) throw new Error('A API Lab deve usar uma origem local sem caminho ou credenciais.')
  return {
    plugins: [react()],
    define: { __APP_VARIANT__: JSON.stringify(lab ? 'lab' : 'standard') },
    server: { host: '127.0.0.1', port: lab ? 5174 : 5173, strictPort: true, proxy: { '/api': api.origin } },
    preview: { host: '127.0.0.1', port: lab ? 5174 : 4173, strictPort: true, proxy: { '/api': api.origin } },
    build: { outDir: lab ? 'dist-lab' : 'dist' },
  }
})
