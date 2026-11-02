import assert from 'node:assert/strict'
import { existsSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities } from '../shared/src/testing/fixtures.ts'

const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const executablePath = process.env.BROWSER_EXECUTABLE || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const context = await chromium.launchPersistentContext(resolve(output, `history-${Date.now()}`), {
  headless: true, executablePath, viewport: { width: 380, height: 900 },
  ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
})
const errors = []
let requests = 0
try {
  await context.route('http://127.0.0.1:5173/**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname.startsWith('/api/')) return route.fallback()
    const asset = url.pathname.startsWith('/assets/')
    await route.fulfill({ path: resolve('web/dist', asset ? url.pathname.slice(1) : 'index.html'),
      contentType: asset ? (url.pathname.endsWith('.css') ? 'text/css' : 'application/javascript') : 'text/html' })
  })
  await context.route('**/api/**', async route => {
    if (route.request().url().endsWith('/capabilities')) return route.fulfill({ json: capabilities })
    assert(route.request().url().endsWith('/analyze'), 'Selecionar histórico não deve enviar relatos ou outras requisições.')
    requests++
    const payload = route.request().postDataJSON()
    await route.fulfill({ json: analysisFixture(payload.processing_level, payload.text) })
  })
  const cdp = await context.browser().newBrowserCDPSession()
  const extension = await cdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist') })
  const entries = [
    { title: 'Primeiro resultado', text: 'A tributação progressiva deve financiar os serviços públicos.' },
    { title: 'Segundo resultado', text: 'As liberdades civis devem ser ampliadas e protegidas.' },
  ]
  for (const [name, url] of [['site', 'http://127.0.0.1:5173/analise'], ['extensão', `chrome-extension://${extension.id}/sidepanel.html`]]) {
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(`${name}: ${error.message}`))
    page.on('console', message => {
      if (message.type() === 'error' && /same key|unique.*key/i.test(message.text())) errors.push(`${name}: ${message.text()}`)
    })
    await page.goto(url)
    const result = page.getByRole('region', { name: 'Análise selecionada', exact: true })
    const explorer = page.getByRole('region', { name: 'Distribuição e evidências', exact: true })
    const history = page.locator(name === 'site' ? '.historyButton' : '.historyEntry')
    for (const [index, entry] of entries.entries()) {
      if (index) await page.getByRole('button', { name: name === 'site' ? '+ Nova análise' : '+ Nova', exact: true }).click()
      await page.locator('#local-title').fill(entry.title)
      await page.locator('#text-input').fill(entry.text)
      await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
      await result.getByRole('heading', { name: entry.title, exact: true }).waitFor()
    }
    const initialRequests = requests
    // Restore from session storage before switching between saved results.
    await page.reload()
    await result.waitFor()
    if (name === 'extensão') await page.locator('.sessionHistory > summary').click()
    for (const index of [0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1]) {
      await history.nth(index).click()
      await result.getByRole('heading', { name: entries[index].title, exact: true }).waitFor()
      assert.equal(await result.count(), 1, `${name}: deve existir um único resultado.`)
      assert.equal(await explorer.count(), 1, `${name}: a troca de histórico deve substituir as evidências anteriores.`)
      assert.equal(await page.locator('.reportAction').count(), 1, `${name}: deve existir uma única ação de relato.`)
      assert.equal(await history.count(), entries.length, `${name}: selecionar não deve adicionar entradas ao histórico.`)
      assert.equal(await history.nth(index).getAttribute('aria-pressed'), 'true')
      assert.equal(await page.locator('#text-input').count(), 0)
      await explorer.getByRole('tab', { name: 'Evidências', exact: true }).click()
      assert.equal(await explorer.locator('blockquote').innerText(), `“${entries[index].text}”`)
      assert(!(await result.innerText()).includes(entries[1 - index].text), `${name}: não deve restar texto de outra análise.`)
      await result.locator('.sourceDetails > summary').click()
      assert.equal(await result.locator('.sourceText').innerText(), entries[index].text)
      await result.locator('.sourceDetails > summary').click()
      await page.getByRole('button', { name: 'Relatar problema na classificação', exact: true }).click()
      const dialog = page.getByRole('dialog', { name: 'Relatar problema na classificação', exact: true })
      await dialog.getByText('Ver trecho que será armazenado', { exact: true }).click()
      assert.equal(await dialog.locator('.sourceText').innerText(), entries[index].text)
      assert.equal(await dialog.getByRole('checkbox').isChecked(), false)
      await dialog.getByRole('button', { name: 'Cancelar', exact: true }).click()
    }
    assert.equal(requests, initialRequests, `${name}: histórico não deve reenviar análises.`)
    await page.close()
    console.log(`OK: ${name}; 12 seleções de histórico, resultado e evidências únicos, texto e relato correspondentes, sem novos envios.`)
  }
  assert.deepEqual(errors, [])
} finally { await context.close() }
