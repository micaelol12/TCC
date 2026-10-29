import assert from 'node:assert/strict'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { extname, resolve, sep } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities } from '../shared/src/testing/fixtures.ts'
import { writeUsabilityReport } from './usability-report.mjs'

// Isolated browser profile, built UI and mocked API: no user data or provider calls.
const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const headed = process.argv.includes('--headed')
const executedAt = new Date().toISOString()
const executablePath = process.env.BROWSER_EXECUTABLE || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const context = await chromium.launchPersistentContext(resolve(output, `usability-${Date.now()}`), {
  headless: !headed, slowMo: headed ? 140 : 0, executablePath, viewport: { width: 1280, height: 1000 },
})
const origin = 'http://127.0.0.1:5187'
const dist = resolve('web/dist')
const errors = []
let failure = 0
let sent = 0
try {
  await context.route(`${origin}/**`, async route => {
    const pathname = new URL(route.request().url()).pathname
    const file = pathname.startsWith('/assets/') ? resolve(dist, `.${pathname}`) : resolve(dist, 'index.html')
    assert(file.startsWith(dist + sep))
    await route.fulfill({ body: readFileSync(file), contentType: { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' }[extname(file)] })
  })
  await context.route('**/api/**', async route => {
    if (route.request().url().endsWith('/capabilities')) { await route.fulfill({ json: capabilities }); return }
    assert(route.request().url().endsWith('/analyze'))
    sent++
    if (failure) { await route.fulfill({ status: failure, json: {} }); return }
    const payload = route.request().postDataJSON()
    assert.deepEqual(Object.keys(payload).sort(), ['processing_level', 'text'])
    const analysis = analysisFixture(payload.processing_level, payload.text)
    analysis.axes[0].reason_codes = ['evidencia_limitada', 'codigo_futuro']
    analysis.warnings = ['falha_jev', 'codigo_futuro']
    await route.fulfill({ json: analysis })
  })
  const page = await context.newPage()
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(`${origin}/analise`)
  const text = page.getByLabel('Texto em português', { exact: true })
  const title = page.getByLabel('Título local (opcional)', { exact: true })
  await text.fill('Rascunho fictício preservado durante a navegação. 📝')
  await title.fill('Título do rascunho')
  await page.getByRole('radio', { name: /^Classificação direta/ }).check()
  await page.getByRole('link', { name: 'Meu resultado', exact: true }).click()
  await page.getByRole('link', { name: 'Analisar texto', exact: true }).click()
  assert.equal(await text.inputValue(), 'Rascunho fictício preservado durante a navegação. 📝')
  assert.equal(await title.inputValue(), 'Título do rascunho')
  assert(await page.getByRole('radio', { name: /^Classificação direta/ }).isChecked())
  await page.reload()
  assert.equal(await text.inputValue(), 'Rascunho fictício preservado durante a navegação. 📝')
  await page.screenshot({ path: resolve(output, 'usability-draft-restored.png'), fullPage: true })
  await page.getByText('Como escolher o processamento?', { exact: true }).click()
  assert((await page.locator('body').innerText()).includes('nenhum modo garante uma classificação correta'))
  await page.screenshot({ path: resolve(output, 'usability-processing-help.png'), fullPage: true })
  failure = 413
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'Reduza o texto' }).waitFor()
  assert(!(await page.getByRole('alert').innerText()).includes('Lab'))
  await page.screenshot({ path: resolve(output, 'usability-size-error.png'), fullPage: true })
  failure = 0
  await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  assert((await page.locator('body').innerText()).includes('O serviço de classificação não respondeu'))
  assert(!(await page.locator('body').innerText()).includes('codigo_futuro'))
  await page.getByText('Motivos registrados na análise', { exact: true }).click()
  assert((await page.locator('body').innerText()).includes('limitação adicional'))
  await page.screenshot({ path: resolve(output, 'usability-translated-diagnostics.png'), fullPage: true })
  await page.getByRole('button', { name: 'Editar e reanalisar', exact: true }).click()
  await text.fill('Rascunho diferente da análise do histórico.')
  await page.getByRole('button', { name: 'Fechar', exact: true }).click()
  await page.getByRole('button', { name: 'Editar e reanalisar', exact: true }).click()
  await page.getByRole('dialog', { name: 'Substituir o rascunho atual?' }).waitFor()
  await page.screenshot({ path: resolve(output, 'usability-overwrite-confirmation.png'), fullPage: true })
  await page.getByRole('dialog').getByRole('button', { name: 'Cancelar', exact: true }).click()
  await page.getByRole('button', { name: '+ Nova análise', exact: true }).click()
  assert.equal(await text.inputValue(), 'Rascunho diferente da análise do histórico.')
  await page.reload()
  assert.equal(await text.inputValue(), 'Rascunho diferente da análise do histórico.')
  await page.screenshot({ path: resolve(output, 'usability-draft-with-history.png'), fullPage: true })
  await page.getByRole('button', { name: 'Descartar rascunho', exact: true }).click()
  await page.screenshot({ path: resolve(output, 'usability-draft-discard-confirmation.png'), fullPage: true })
  await page.getByRole('dialog').getByRole('button', { name: 'Cancelar', exact: true }).click()
  assert.equal(await text.inputValue(), 'Rascunho diferente da análise do histórico.')

  await page.getByRole('link', { name: 'Teste', exact: true }).click()
  await page.getByRole('radio', { name: 'Neutro ou incerto', exact: true }).check()
  await page.getByRole('button', { name: 'Revisar respostas', exact: true }).click()
  const review = page.locator('.reviewList')
  assert((await review.innerText()).includes('Sua resposta: Neutro ou incerto'))
  assert((await review.innerText()).includes('Ainda não respondida'))
  await page.screenshot({ path: resolve(output, 'usability-review-before-edit.png'), fullPage: true })
  await page.getByRole('button', { name: 'Editar pergunta 1', exact: true }).click()
  await page.getByRole('radio', { name: 'Concordo', exact: true }).check()
  await page.getByRole('button', { name: 'Voltar à revisão', exact: true }).click()
  assert((await review.locator('li').first().innerText()).includes('Sua resposta: Concordo'))
  await page.reload()
  await page.getByRole('heading', { name: 'Revisar respostas', exact: true }).waitFor()
  await page.screenshot({ path: resolve(output, 'usability-review-desktop.png'), fullPage: true })
  await page.setViewportSize({ width: 380, height: 900 })
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
  await page.screenshot({ path: resolve(output, 'usability-review-mobile.png'), fullPage: true })
  await page.getByRole('button', { name: 'Descartar teste', exact: true }).click()
  let dialog = page.getByRole('dialog')
  assert(await dialog.getByRole('button', { name: 'Cancelar', exact: true }).evaluate(element => element === document.activeElement))
  await page.screenshot({ path: resolve(output, 'usability-confirmation-mobile.png'), fullPage: true })
  await page.keyboard.press('Escape')
  assert.equal(await page.getByRole('dialog').count(), 0)
  assert((await review.locator('li').first().innerText()).includes('Sua resposta: Concordo'))
  await page.getByRole('button', { name: 'Editar pergunta 2', exact: true }).click()
  for (let index = 1; index < 70; index++) {
    await page.getByRole('radio', { name: 'Neutro ou incerto', exact: true }).check()
    await page.getByRole('button', { name: index === 69 ? 'Revisar' : 'Próxima', exact: true }).click()
  }
  await page.getByRole('button', { name: 'Concluir teste', exact: true }).click()
  await page.getByRole('heading', { name: 'Seus quatro eixos', exact: true }).waitFor()
  await page.screenshot({ path: resolve(output, 'usability-completed-result.png'), fullPage: true })
  await page.getByRole('button', { name: 'Apagar meus dados locais', exact: true }).click()
  await page.screenshot({ path: resolve(output, 'usability-delete-site-confirmation.png'), fullPage: true })
  await page.getByRole('dialog').getByRole('button', { name: 'Cancelar', exact: true }).click()
  await page.getByRole('link', { name: 'Analisar texto', exact: true }).click()
  assert.equal(await text.inputValue(), 'Rascunho diferente da análise do histórico.')
  await page.getByRole('button', { name: 'Descartar rascunho', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Sim, descartar rascunho', exact: true }).click()
  assert.equal(await text.inputValue(), '')
  assert((await page.locator('.history').innerText()).includes('Título do rascunho'))
  await page.getByRole('link', { name: 'Meu resultado', exact: true }).click()
  await page.getByRole('button', { name: 'Apagar meus dados locais', exact: true }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Sim, apagar dados do site', exact: true }).click()
  await page.getByRole('link', { name: 'Analisar texto', exact: true }).click()
  assert.equal(await text.inputValue(), '')
  assert((await page.locator('.history').innerText()).includes('Nenhuma análise'))
  await page.reload()
  assert.equal(await text.inputValue(), '')
  await page.screenshot({ path: resolve(output, 'usability-cleared-session.png'), fullPage: true })
  await page.getByRole('link', { name: 'Meu resultado', exact: true }).click()
  assert((await page.locator('main').innerText()).includes('ainda não concluiu'))

  // Storage unavailable: warn, preserve in-memory navigation, and avoid reviving stale data.
  const blocked = await context.newPage()
  blocked.on('pageerror', error => errors.push(error.message))
  await blocked.addInitScript(() => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = function(key, value) {
      if (key.startsWith('8values-analysis-')) throw new DOMException('Quota exceeded', 'QuotaExceededError')
      return original.call(this, key, value)
    }
  })
  await blocked.goto(`${origin}/analise`)
  await blocked.getByRole('status').filter({ hasText: 'Não foi possível guardar o histórico' }).waitFor()
  await blocked.getByLabel('Texto em português', { exact: true }).fill('Rascunho com armazenamento bloqueado.')
  await blocked.getByRole('status').filter({ hasText: 'Não foi possível guardar o rascunho' }).waitFor()
  await blocked.getByRole('link', { name: 'Meu resultado', exact: true }).click()
  await blocked.getByRole('link', { name: 'Analisar texto', exact: true }).click()
  assert.equal(await blocked.getByLabel('Texto em português', { exact: true }).inputValue(), 'Rascunho com armazenamento bloqueado.')
  await blocked.setViewportSize({ width: 380, height: 900 })
  assert(await blocked.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
  await blocked.screenshot({ path: resolve(output, 'usability-storage-warning-mobile.png'), fullPage: true })
  assert.equal(sent, 2, 'Restaurar rascunhos e navegar não deve enviar análises automaticamente.')
  assert.equal(errors.length, 0, errors.join('\n'))
  const result = { executedAt, browser: 'Chrome', browserVersion: context.browser().version(), checks: ['draft-navigation-and-reload', 'draft-with-existing-history', 'mode-help', 'size-error-without-lab', 'translated-diagnostics', 'overwrite-cancel', 'draft-discard-cancel-and-confirm', 'review-with-answers', 'edit-and-return-to-review', 'review-reload', 'destructive-dialog-focus-and-escape', 'complete-70-questions', 'delete-cancel-and-confirm', 'clear-all-session-data', 'storage-failure-warning-and-memory-fallback', 'desktop-and-mobile-layout'], requests: sent, pageErrors: errors }
  const report = writeUsabilityReport(result, output)
  assert.equal(report.passed, report.total, 'Todos os casos documentados devem estar cobertos pela execução.')
  for (const item of report.cases) assert(existsSync(resolve(output, item.evidence)), `Captura ausente: ${item.id}`)
  result.cases = report.cases
  writeFileSync(resolve(output, 'usability-report.json'), JSON.stringify(result, null, 2))
  console.log(JSON.stringify({ executedAt, checks: result.checks, passed: report.passed, total: report.total, requests: sent, pageErrors: errors, gallery: report.gallery, testCases: resolve('CASOS_TESTE_USABILIDADE.md') }, null, 2))
} finally { await context.close() }
