import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { extensionConfig } from './buildConfig'

export default defineConfig(({ mode }) => {
  const config = extensionConfig(mode, { ...loadEnv(mode, process.cwd(), 'VITE_'), ...process.env } as Record<string, string>)
  const manifest = JSON.parse(readFileSync(new URL('./manifest.json', import.meta.url), 'utf8'))
  return {
    plugins: [react(), { name: 'extension-manifest', generateBundle() {
      const notices = [
        readFileSync(new URL('../THIRD_PARTY_NOTICES.md', import.meta.url), 'utf8'),
        ...['react', 'react-dom', 'scheduler'].map(name => `\n## ${name}\n\n${readFileSync(new URL(`../node_modules/${name}/LICENSE`, import.meta.url), 'utf8')}`),
      ].join('\n')
      this.emitFile({ type: 'asset', fileName: 'THIRD_PARTY_NOTICES.md', source: notices })
      this.emitFile({ type: 'asset', fileName: 'profile-bridge.js', source: readFileSync(new URL('./src/platform/profileBridge.js', import.meta.url), 'utf8').replace('__WEB_ORIGIN__', JSON.stringify(config.webBase)) })
      this.emitFile({ type: 'asset', fileName: 'manifest.json', source: JSON.stringify({ ...manifest,
        host_permissions: [config.hostPermission],
        content_scripts: [{ matches: [config.webMatchPattern], js: ['profile-bridge.js'], run_at: 'document_start' }],
        content_security_policy: { extension_pages: `script-src 'self'; object-src 'self'; connect-src ${config.apiBase}; style-src 'self'; style-src-attr 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'` },
      }, null, 2) })
    } }],
    define: { __API_BASE_URL__: JSON.stringify(config.apiBase), __WEB_BASE_URL__: JSON.stringify(config.webBase) },
    resolve: { dedupe: ['react', 'react-dom'] },
    base: './',
    build: { rollupOptions: { input: { sidepanel: resolve('sidepanel.html'), background: resolve('src/background.ts') },
      output: { entryFileNames: chunk => chunk.name === 'background' ? 'background.js' : 'assets/[name]-[hash].js' } } },
  }
})
