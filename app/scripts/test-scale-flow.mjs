import assert from 'node:assert/strict'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { chromium } from 'playwright'

const browser = await chromium.launch({ headless: true, executablePath: process.env.BROWSER_EXECUTABLE || 'C:/Program Files/Google/Chrome/Application/chrome.exe' })
try {
  const errors = []
  for (const [id, count] of [['ordinal_5_v1', 5], ['ordinal_9_v1', 9], ['ordinal_7_diagnostico', 7]]) {
    const page = await browser.newPage()
    page.on('pageerror', e => errors.push(e.message))
    await page.goto(pathToFileURL(resolve(`test-results/scales/${id}.html`)).href)
    await page.locator('#subtitle').filter({ hasText: id }).waitFor()
    assert.equal(await page.locator('.legend span').count(), count + 2)
    assert((await page.locator('body').innerText()).includes(`Escala: ${id}`))
    await page.screenshot({ path: resolve(`test-results/scales/${id}.png`), fullPage: true })
    await page.close()
  }
  assert.deepEqual(errors, [])
  console.log('Fluxogramas: 5/9/7 níveis, snapshots e legendas corretos; zero erros JavaScript.')
} finally { await browser.close() }
