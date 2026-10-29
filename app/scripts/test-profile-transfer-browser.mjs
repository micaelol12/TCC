import assert from 'node:assert/strict'
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { capabilities } from '../shared/src/testing/fixtures.ts'

const target = process.argv[2] ?? 'chrome'
const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const executablePath = process.env.BROWSER_EXECUTABLE || (target === 'edge' ? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' : 'C:/Program Files/Google/Chrome/Application/chrome.exe')
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const context = await chromium.launchPersistentContext(resolve(output, `profile-${target}-${Date.now()}`), {
  headless: true, executablePath, viewport: { width: 1000, height: 1000 },
  ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
})
const errors = []
const hash = readFileSync(resolve('shared/src/domain/quizScoring.ts'), 'utf8').match(/QUESTION_HASH = '([^']+)'/)[1]
const profile = { schema_version: 1, question_hash: hash, completed_at: new Date().toISOString(), scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
try {
  // Serve the built website at its configured origin, without depending on a dev server.
  await context.route(/http:\/\/127\.0\.0\.1:517[34]\//, async route => {
    const pathname = new URL(route.request().url()).pathname
    const asset = pathname.startsWith('/assets/')
    await route.fulfill({ path: resolve('web/dist', asset ? pathname.slice(1) : 'index.html'), contentType: asset ? (pathname.endsWith('.css') ? 'text/css' : 'application/javascript') : 'text/html' })
  })
  await context.route('http://127.0.0.1:8000/api/**', route => {
    assert(route.request().url().endsWith('/capabilities'), 'O envio do perfil não deve acessar a API.')
    return route.fulfill({ json: capabilities })
  })
  const cdp = await context.browser().newBrowserCDPSession()
  const { id } = await cdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist') })
  const panel = await context.newPage()
  panel.on('pageerror', error => errors.push(error.message))
  await panel.goto(`chrome-extension://${id}/sidepanel.html`)
  await panel.locator('#text-input').waitFor()
  await panel.getByRole('button', { name: 'Comparação', exact: true }).click()
  const website = await context.newPage()
  website.on('pageerror', error => errors.push(error.message))
  await website.addInitScript(profile => {
    if (!localStorage.getItem('values-profile-v1')) localStorage.setItem('values-profile-v1', JSON.stringify(profile))
  }, profile)
  await website.goto('http://127.0.0.1:5173/resultado')
  const read = () => panel.evaluate(async () => ({ local: await chrome.storage.local.get('8values-profile-local-v1'), session: await chrome.storage.session.get('8values-profile-session-v1') }))
  // Opening the result never transfers it automatically.
  assert.deepEqual(await read(), { local: {}, session: {} })
  await website.getByRole('button', { name: 'Usar resultado na extensão', exact: true }).click()
  await website.getByRole('status').filter({ hasText: 'Resultado salvo na extensão!' }).waitFor()
  await panel.getByText('Perfil salvo localmente nesta extensão.', { exact: true }).waitFor()
  assert.deepEqual(await read(), { local: { '8values-profile-local-v1': profile }, session: {} })
  await panel.reload()
  await panel.locator('#text-input').waitFor()
  await panel.getByRole('button', { name: 'Comparação', exact: true }).click()
  await panel.getByText('Perfil salvo localmente nesta extensão.', { exact: true }).waitFor()
  await website.screenshot({ path: resolve(output, `${target}-profile-transfer.png`), fullPage: true })
  await website.setViewportSize({ width: 390, height: 844 })
  assert(await website.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Layout deve caber em celular.')
  // Replacing the profile also persists without an extra checkbox.
  const replacement = { ...profile, scores: { ...profile.scores, economic: 80 } }
  await website.evaluate(profile => localStorage.setItem('values-profile-v1', JSON.stringify(profile)), replacement)
  await website.reload()
  await website.getByRole('button', { name: 'Usar resultado na extensão', exact: true }).click()
  await website.getByRole('status').filter({ hasText: 'Resultado salvo na extensão!' }).waitFor()
  assert.deepEqual(await read(), { local: { '8values-profile-local-v1': replacement }, session: {} })
  // Same host, wrong port: no bridge, useful failure message, no writes.
  await website.goto('http://127.0.0.1:5174/resultado')
  await website.getByRole('button', { name: 'Usar resultado na extensão', exact: true }).click()
  await website.getByRole('alert').filter({ hasText: 'A extensão não respondeu' }).waitFor()
  assert.deepEqual(await read(), { local: { '8values-profile-local-v1': replacement }, session: {} })
  assert(await website.getByRole('button', { name: 'Usar resultado na extensão', exact: true }).isEnabled())
  await panel.getByRole('button', { name: 'Apagar perfil', exact: true }).click()
  await panel.getByRole('dialog').getByRole('button', { name: 'Sim, apagar perfil', exact: true }).click()
  await panel.getByRole('link', { name: 'Fazer meu teste no site' }).waitFor()
  assert.deepEqual(await read(), { local: { '8values-profile-local-v1': null }, session: {} })
  assert.deepEqual(errors, [])
  const report = { browser: target, version: context.browser().version(), checks: ['no-automatic-transfer', 'one-click-transfer', 'live-panel-update', 'persistent-profile', 'reload', 'replace-profile', 'wrong-port-timeout', 'delete-profile', 'mobile-width', 'no-profile-api-request'], pageErrors: errors }
  writeFileSync(resolve(output, `${target}-profile-transfer-report.json`), JSON.stringify(report, null, 2))
  console.log(JSON.stringify(report, null, 2))
} finally { await context.close() }
