import assert from 'node:assert/strict'
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities } from '../shared/src/testing/fixtures.ts'

const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const target = process.argv[2] ?? 'chrome'
const executablePath = process.env.BROWSER_EXECUTABLE || (target === 'edge' ? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' : 'C:/Program Files/Google/Chrome/Application/chrome.exe')
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const context = await chromium.launchPersistentContext(resolve(output, `browser-${target}-${Date.now()}`), {
  headless: true, executablePath, viewport: { width: 380, height: 900 }, ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
})
const errors = [], requests = []
let behavior = 'success', delay = 0
try {
  await context.route('http://127.0.0.1:8000/api/**', async route => {
    const request = route.request()
    if (request.url().endsWith('/capabilities')) { await route.fulfill({ json: capabilities }); return }
    assert(request.url().endsWith('/analyze'), 'Endpoint inesperado')
    const payload = request.postDataJSON()
    assert.deepEqual(Object.keys(payload).sort(), ['processing_level', 'text'])
    requests.push(payload)
    const currentBehavior = behavior, currentDelay = delay
    if (currentDelay) await new Promise(resolveDelay => setTimeout(resolveDelay, currentDelay))
    try {
      if (currentBehavior === '429') await route.fulfill({ status: 429, json: { detail: 'limit' } })
      else await route.fulfill({ json: analysisFixture(payload.processing_level, payload.text) })
    } catch { /* the document may have aborted this request */ }
  })
  const browserCdp = await context.browser().newBrowserCDPSession()
  const { id } = await browserCdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist') })
  const page = await context.newPage()
  page.on('pageerror', error => errors.push(error.message))
  const url = `chrome-extension://${id}/sidepanel.html`
  await page.goto(url)
  const input = page.locator('#text-input')
  await input.waitFor()
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).waitFor()
  const capture = async (text, source = 'example.org') => page.evaluate(async ({ text, source }) => {
    const window = await chrome.windows.getCurrent()
    await chrome.storage.session.set({ [`8values-capture-v1:${window.id}`]: { id: crypto.randomUUID(), text, source, createdAt: Date.now(), windowId: window.id, tabId: 1 } })
  }, { text, source })
  const waitText = (text, locator = input) => locator.evaluate((element, expected) => {
    if (element.value === expected) return true
    return new Promise(resolveValue => { const timer = setInterval(() => { if (element.value === expected) { clearInterval(timer); resolveValue(true) } }, 30); setTimeout(() => { clearInterval(timer); resolveValue(false) }, 5000) })
  }, text).then(found => assert(found, `Texto esperado: ${text.slice(0, 50)}`))
  const selection = 'É preciso ampliar as liberdades civis.\nUma ação política em português.'
  await capture(selection)
  await waitText(selection)
  assert.equal(requests.length, 0)
  await page.screenshot({ path: resolve(output, `${target}-composer.png`), fullPage: true })
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  assert.deepEqual(requests[0], { text: selection, processing_level: 'medium' })
  await page.getByText('Distribuição e evidências de Econômico', { exact: true }).click()
  assert((await page.locator('body').innerText()).includes('Evidência limitada.'))
  assert((await page.locator('body').innerText()).includes('Sem estimativa'))
  await page.screenshot({ path: resolve(output, `${target}-result.png`), fullPage: true })
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
  await page.reload()
  await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Editar e reanalisar', exact: true }).click()
  await waitText(selection)
  behavior = '429'
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'Limite de uso atingido' }).waitFor()
  assert.equal(await input.inputValue(), selection)
  behavior = 'success'; delay = 35000
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('button', { name: 'Cancelar', exact: true }).waitFor()
  await capture('Próximo trecho, sem substituir a análise.')
  await page.getByRole('button', { name: 'Usar nova seleção', exact: true }).waitFor()
  assert.equal(await input.inputValue(), selection)
  await page.getByRole('button', { name: 'Cancelar', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'cancelada' }).waitFor()
  await page.getByRole('button', { name: 'Usar nova seleção', exact: true }).click()
  await waitText('Próximo trecho, sem substituir a análise.')
  delay = 0
  await page.reload()
  await waitText('Próximo trecho, sem substituir a análise.')
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Editar e reanalisar', exact: true }).click()
  delay = 35000
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('button', { name: 'Cancelar', exact: true }).waitFor()
  await page.reload()
  await page.getByRole('alert').filter({ hasText: 'interrompida' }).waitFor()
  assert.equal(await input.inputValue(), 'Próximo trecho, sem substituir a análise.')
  const before = requests.length
  await new Promise(resolveDelay => setTimeout(resolveDelay, 100))
  assert.equal(requests.length, before, 'Não deve haver reenvio automático')
  // Native browser storage, separate windows, same installed extension.
  const secondOpened = context.waitForEvent('page')
  await page.evaluate(url => chrome.windows.create({ url }), url)
  const second = await secondOpened
  await second.locator('#text-input').waitFor()
  const firstWindowId = await page.evaluate(async () => (await chrome.windows.getCurrent()).id)
  const secondWindowId = await second.evaluate(async () => (await chrome.windows.getCurrent()).id)
  assert.notEqual(firstWindowId, secondWindowId)
  await second.evaluate(async () => {
    const current = await chrome.windows.getCurrent()
    await chrome.storage.session.set({ [`8values-capture-v1:${current.id}`]: { id: crypto.randomUUID(), text: 'Texto na segunda janela', createdAt: Date.now(), windowId: current.id, tabId: 2 } })
  })
  await waitText('Texto na segunda janela', second.locator('#text-input'))
  assert.equal(await input.inputValue(), 'Próximo trecho, sem substituir a análise.')
  await second.close()
  await page.getByRole('button', { name: 'Comparação', exact: true }).click()
  const scoring = readFileSync(resolve('shared/src/domain/quizScoring.ts'), 'utf8')
  const hash = scoring.match(/QUESTION_HASH = '([^']+)'/)[1]
  const profile = { schema_version: 1, question_hash: hash, completed_at: new Date().toISOString(), scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
  await page.locator('#profile-file').setInputFiles({ name: 'perfil.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(profile)) })
  await page.getByText('Perfil salvo localmente nesta extensão.', { exact: true }).waitFor()
  assert.deepEqual(await page.evaluate(async () => (await chrome.storage.local.get('8values-profile-local-v1'))['8values-profile-local-v1']), profile)
  await page.getByText('Diferença de 50,0 pontos;', { exact: false }).waitFor()
  await page.getByRole('button', { name: 'Apagar perfil', exact: true }).click()
  await page.getByRole('link', { name: 'Fazer meu teste no site' }).waitFor()
  await page.getByRole('button', { name: 'Análise', exact: true }).click()
  await page.locator('.sessionHistory > summary').click()
  await page.getByRole('button', { name: 'Limpar histórico e rascunhos' }).click()
  assert.equal(await input.inputValue(), '')
  await page.reload(); await input.waitFor(); assert.equal(await input.inputValue(), '')
  await input.fill('x'.repeat(60001))
  assert(await page.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled())
  await input.fill('Texto <script>window.evil=true</script> mostrado como texto.')
  delay = target === 'chrome' ? 31000 : 0
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor({ timeout: 45000 })
  assert.equal(await page.evaluate(() => window.evil), undefined)
  assert.equal(errors.length, 0, errors.join('\n'))
  const report = { browser: target, browserVersion: context.browser().version(), extensionId: id, analyses: requests.length, checks: ['capture-and-review', 'payload-only-text-and-mode', 'partial-results', 'literal-evidence', 'draft-and-history-reload', 'http-429', 'cancel', 'pending-selection', 'interruption-without-retry', 'window-isolation', 'profile-import-delete', 'clear', 'character-limit', 'text-escaping', ...(delay ? ['analysis-over-30-seconds'] : [])], pageErrors: errors }
  writeFileSync(resolve(output, `${target}-report.json`), JSON.stringify(report, null, 2))
  console.log(JSON.stringify(report, null, 2))
} finally { await context.close() }
