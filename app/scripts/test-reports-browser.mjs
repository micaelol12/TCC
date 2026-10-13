import assert from 'node:assert/strict'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { createServer } from 'node:http'
import { extname, resolve, sep } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities } from '../shared/src/testing/fixtures.ts'

const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const target = process.argv[2] ?? 'chrome'
const executablePath = process.env.BROWSER_EXECUTABLE || (target === 'edge' ? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' : 'C:/Program Files/Google/Chrome/Application/chrome.exe')
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const dist = resolve('web/dist')
const server = createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname)
  const file = pathname.startsWith('/assets/') ? resolve(dist, `.${pathname}`) : resolve(dist, 'index.html')
  if (!file.startsWith(dist + sep)) { response.writeHead(404); response.end(); return }
  try {
    const types = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' }
    response.setHeader('Content-Type', types[extname(file)] ?? 'application/octet-stream')
    response.end(readFileSync(file))
  } catch { response.writeHead(404); response.end() }
})
await new Promise(done => server.listen(0, '127.0.0.1', done))
const webUrl = `http://127.0.0.1:${server.address().port}`
let context
const errors = [], reports = [], analyses = []
let reportBehavior = 'success'
const receipt = { report_id: 'ee7f21b4-65a0-4628-9a19-20cf22e953d9', received_at: '2026-10-13T12:00:00Z', status: 'pending' }

async function exerciseReport(page, text, origin) {
  const reportButton = page.getByRole('button', { name: 'Reportar classificação', exact: true })
  const initialReports = reports.length
  await reportButton.click()
  let dialog = page.getByRole('dialog', { name: 'Reportar classificação' })
  await dialog.waitFor()
  assert((await dialog.innerText()).includes('armazenados em nosso banco de dados'))
  assert.equal(await dialog.getByRole('checkbox').isChecked(), false)
  assert(await dialog.getByRole('button', { name: 'Enviar report', exact: true }).isDisabled())
  assert.equal(reports.length, initialReports)
  await dialog.getByText('Ver trecho que será armazenado', { exact: true }).click()
  assert.equal(await dialog.locator('.sourceText').innerText(), text)
  await dialog.getByText('Ver análise que será armazenada', { exact: true }).click()
  assert.deepEqual(JSON.parse(await dialog.locator('pre').innerText()), analysisFixture('medium', text))
  await dialog.getByRole('button', { name: 'Cancelar', exact: true }).click()
  assert.equal(reports.length, initialReports)
  // Escape dismisses before sending, with native focus restoration.
  await reportButton.click()
  await page.keyboard.press('Escape')
  assert.equal(await page.getByRole('dialog').count(), 0)
  assert(await reportButton.evaluate(button => document.activeElement === button))
  assert.equal(reports.length, initialReports)
  await reportButton.click()
  dialog = page.getByRole('dialog', { name: 'Reportar classificação' })
  // Keyboard focus stays inside the native modal.
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab')
    assert(await dialog.evaluate(element => element.contains(document.activeElement)))
  }
  await dialog.getByRole('textbox').fill('x'.repeat(2001))
  await dialog.getByRole('checkbox').check()
  assert(await dialog.getByRole('button', { name: 'Enviar report', exact: true }).isDisabled())
  const comment = 'Discordo da classificação do eixo econômico. <script>window.reportEvil=true</script>'
  await dialog.getByRole('textbox').fill(comment)
  await page.screenshot({ path: resolve(output, `${target}-${origin}-report-dialog.png`), fullPage: true })
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
  // Simulate a lost response after acceptance; the retry must be identical.
  reportBehavior = 'uncertain'
  await dialog.getByRole('button', { name: 'Enviar report', exact: true }).click()
  await dialog.getByRole('alert').waitFor()
  assert.equal(await dialog.getByRole('textbox').inputValue(), comment)
  assert.equal(await page.getByRole('button', { name: 'Report enviado', exact: true }).count(), 0)
  assert.equal(reports.length, initialReports + 1)
  await dialog.getByRole('button', { name: 'Cancelar', exact: true }).click()
  await reportButton.click()
  dialog = page.getByRole('dialog', { name: 'Reportar classificação' })
  assert.equal(await dialog.getByRole('checkbox').isChecked(), false)
  assert.equal(await dialog.getByRole('textbox').inputValue(), comment)
  await dialog.getByRole('checkbox').check()
  reportBehavior = 'success'
  await dialog.getByRole('button', { name: 'Enviar report', exact: true }).click()
  await page.getByRole('button', { name: 'Enviando…', exact: true }).waitFor()
  assert(await dialog.getByRole('button', { name: 'Cancelar', exact: true }).isDisabled())
  assert(await dialog.getByRole('textbox').isDisabled())
  await page.keyboard.press('Escape')
  assert(await dialog.isVisible(), 'Escape não deve ocultar um envio em andamento')
  await page.getByRole('button', { name: 'Report enviado', exact: true }).waitFor()
  assert.equal(reports.length, initialReports + 2)
  assert.deepEqual(reports[initialReports], reports[initialReports + 1])
  const payload = reports[initialReports]
  assert.deepEqual(Object.keys(payload).sort(), ['analysis', 'client', 'comment', 'notice_version', 'storage_consent', 'submission_id', 'text'])
  assert.equal(payload.text, text)
  assert.equal(payload.comment, comment)
  assert.equal(payload.client, origin)
  assert.equal(payload.storage_consent, true)
  assert.equal(payload.notice_version, '1')
  assert.match(payload.submission_id, /^[0-9a-f-]{36}$/i)
  assert.deepEqual(payload.analysis, analysisFixture('medium', text))
  assert(await page.getByRole('button', { name: 'Report enviado', exact: true }).isDisabled())
  assert.equal(await page.evaluate(() => window.reportEvil), undefined)
  assert.equal(await page.getByRole('dialog').count(), 0)
}

try {
  context = await chromium.launchPersistentContext(resolve(output, `reports-${target}-${Date.now()}`), {
    headless: true, executablePath, viewport: { width: 380, height: 900 }, ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
  })
  await context.route('**/api/**', async route => {
    const request = route.request()
    if (request.url().endsWith('/capabilities')) { await route.fulfill({ json: capabilities }); return }
    const payload = request.postDataJSON()
    if (request.url().endsWith('/analyze')) {
      analyses.push(payload)
      await route.fulfill({ json: analysisFixture(payload.processing_level, payload.text) }); return
    }
    assert(request.url().endsWith('/reports'))
    reports.push(payload)
    if (reportBehavior === 'uncertain') { await route.abort('failed'); return }
    await new Promise(done => setTimeout(done, 500))
    await route.fulfill({ status: 200, json: receipt })
  })
  const browserCdp = await context.browser().newBrowserCDPSession()
  const { id } = await browserCdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist') })
  const panel = await context.newPage()
  panel.on('pageerror', error => errors.push(error.message))
  await panel.goto(`chrome-extension://${id}/sidepanel.html`)
  const extensionText = 'É preciso ampliar as liberdades civis.\nUma ação política em português.'
  await panel.locator('#text-input').fill(extensionText)
  await panel.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await panel.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  // Validate reports from restored history, rather than only from fresh results.
  await panel.reload()
  await panel.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await exerciseReport(panel, extensionText, 'extension')
  assert.equal(analyses.length, 1, 'Report não deve classificar novamente')

  const web = await context.newPage()
  web.on('pageerror', error => errors.push(error.message))
  await web.goto(`${webUrl}/analise`)
  const originalText = 'A cooperação internacional e a liberdade civil devem ser ampliadas.'
  await web.locator('#text-input').fill(originalText)
  await web.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await web.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await web.getByRole('button', { name: 'Usar este texto em nova análise', exact: true }).click()
  await web.locator('#text-input').fill('Novo rascunho que não deve ser reportado.')
  await web.getByRole('button', { name: 'Fechar', exact: true }).click()
  await exerciseReport(web, originalText, 'web')
  assert.equal(analyses.length, 2, 'Report do site não deve classificar novamente')
  // A desktop layout uses the same flow and restores history too.
  await web.setViewportSize({ width: 1440, height: 1000 })
  await web.reload()
  await web.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await web.getByRole('button', { name: 'Reportar classificação', exact: true }).click()
  await web.getByRole('dialog').waitFor()
  await web.screenshot({ path: resolve(output, `${target}-web-report-desktop.png`), fullPage: true })
  await web.keyboard.press('Escape')
  assert.equal(reports.length, 4)
  assert.equal(errors.length, 0, errors.join('\n'))
  const result = { browser: target, browserVersion: context.browser().version(), checks: ['web-and-extension', 'stored-history', 'original-snapshot-after-edit', 'notice-and-unchecked-consent', 'cancel-without-send', 'keyboard-modal-and-escape', 'comment-limit', 'uncertain-response-manual-idempotent-retry', 'busy-prevents-dismiss-and-duplicate', 'success-after-receipt', 'no-new-classification', 'no-profile-title-or-source', 'mobile-and-desktop-layout', 'text-escaping'], reports: reports.length, analyses: analyses.length, pageErrors: errors }
  writeFileSync(resolve(output, `${target}-reports-feature.json`), JSON.stringify(result, null, 2))
  console.log(JSON.stringify(result, null, 2))
} finally {
  if (context) await context.close()
  await new Promise(done => server.close(done))
}
