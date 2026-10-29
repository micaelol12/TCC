import assert from 'node:assert/strict'
import { existsSync, mkdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities, labCapabilities, experimentCapabilities } from '../shared/src/testing/fixtures.ts'

const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const executablePath = process.env.BROWSER_EXECUTABLE || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
assert(existsSync(executablePath))
const context = await chromium.launchPersistentContext(resolve(output, `comparison-${Date.now()}`), {
  headless: true, executablePath, viewport: { width: 1280, height: 1000 },
  ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
})
const errors = []
const hash = readFileSync(resolve('shared/src/domain/quizScoring.ts'), 'utf8').match(/QUESTION_HASH = '([^']+)'/)[1]
const profile = { schema_version: 1, question_hash: hash, completed_at: new Date().toISOString(), scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
function entries(lab, extension) {
  return [1, 2, 3].map(id => {
    const analysis = analysisFixture('medium', id === 3 ? 'Outro texto, com posições diferentes.' : 'O mesmo texto, analisado duas vezes.')
    Object.assign(analysis, { environment: lab ? 'lab' : 'production', config_version: '1', config_hash: String(id).repeat(64), effective_config: { ...experimentCapabilities.defaults, chunk_tokens: id === 1 ? 400 : 600 } })
    analysis.axes[0].pole_a = id === 1 ? 75 : 25
    analysis.axes[0].pole_b = id === 1 ? 25 : 75
    if (id === 3) { analysis.axes[2].pole_a = 0; analysis.axes[2].pole_b = 100 }
    return { id: extension ? String(id) : id, title: `Resultado ${id}`, text: analysis.chunks[0].text, mode: 'medium', analysis }
  })
}
async function selectExtensionHistory(page, index) {
  const history = page.locator('.sessionHistory')
  if (!await history.evaluate(element => element.open)) await history.locator(':scope > summary').click()
  await history.locator('.historyEntry').nth(index).click()
  const result = page.getByRole('region', { name: 'Análise selecionada', exact: true })
  await result.getByRole('heading', { name: `Resultado ${index + 1}`, exact: true }).waitFor()
  assert.equal(await result.count(), 1)
  assert.equal(await page.getByRole('button', { name: 'Análise', exact: true }).getAttribute('aria-pressed'), 'true')
  assert.equal(await history.locator('.historyEntry[aria-pressed="true"]').count(), 1)
  assert.equal(await page.getByRole('complementary', { name: 'Comparação pessoal' }).count(), 0)
  assert.equal(await page.getByRole('region', { name: 'Comparar análises' }).count(), 0)
}
try {
  await context.route(/http:\/\/127\.0\.0\.1:517[34]\//, async route => {
    const url = new URL(route.request().url())
    if (url.pathname.startsWith('/api/')) return route.fallback()
    const asset = url.pathname.startsWith('/assets/')
    await route.fulfill({ path: resolve(url.port === '5174' ? 'web/dist-lab' : 'web/dist', asset ? url.pathname.slice(1) : 'index.html'), contentType: asset ? (url.pathname.endsWith('.css') ? 'text/css' : 'application/javascript') : 'text/html' })
  })
  await context.route(/http:\/\/127\.0\.0\.1:(800[01]|517[34])\/api\//, route => {
    const url = new URL(route.request().url())
    assert(url.pathname.endsWith('/capabilities'), 'Comparar o histórico não deve executar novas análises.')
    return route.fulfill({ json: ['8001', '5174'].includes(url.port) ? labCapabilities : capabilities })
  })
  const cdp = await context.browser().newBrowserCDPSession()
  for (const lab of [false, true]) {
    const edition = lab ? 'lab' : 'common', prefix = lab ? '8values-lab' : '8values'
    const extension = await cdp.send('Extensions.loadUnpacked', { path: resolve(lab ? 'extension/dist-lab' : 'extension/dist') })
    for (const isExtension of [false, true]) {
      const name = `${edition}-${isExtension ? 'extension' : 'app'}`, saved = entries(lab, isExtension)
      const page = await context.newPage()
      page.on('pageerror', error => errors.push(error.message))
      if (isExtension) {
        await page.goto(`chrome-extension://${extension.id}/sidepanel.html`)
        await page.locator('#text-input').waitFor()
        await page.evaluate(async ({ saved, prefix, profile }) => {
          const window = await chrome.windows.getCurrent()
          await chrome.storage.local.set({ [`${prefix}-profile-local-v1`]: profile })
          await chrome.storage.session.set({ [`${prefix}-session-v1:${window.id}`]: { version: 1, draft: { text: '', title: '' }, mode: 'medium', entries: saved, selectedId: '2', showComposer: false, pending: null, seenCapture: null, seenAt: 0, request: null, notice: '' } })
        }, { saved, prefix, profile })
        await page.reload()
      } else {
        await page.addInitScript(({ saved, prefix, profile, lab }) => {
          sessionStorage.setItem(`${prefix}-analysis-history-v1`, JSON.stringify(saved))
          localStorage.setItem(lab ? 'values-lab-profile-v1' : 'values-profile-v1', JSON.stringify(profile))
        }, { saved, prefix, profile, lab })
        await page.goto(`http://127.0.0.1:${lab ? 5174 : 5173}/analise`)
      }
      await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
      assert.equal(await page.locator('.experimentSnapshot').count(), lab ? 1 : 0)
      if (isExtension) {
        await selectExtensionHistory(page, 0)
      }
      await page.getByRole('button', { name: 'Comparar comigo', exact: true }).click()
      for (const kind of ['personal', 'experiments', 'personal']) {
        await page.getByRole('button', { name: kind === 'personal' ? 'Com meu perfil' : 'Entre análises', exact: true }).click()
        const comparison = kind === 'personal' ? page.getByRole('complementary', { name: 'Comparação pessoal' }) : page.getByRole('region', { name: 'Comparar análises' })
        for (const index of [0, 1, 0, 1]) {
          if (isExtension) {
            await page.getByRole('button', { name: 'Análise', exact: true }).click()
            await selectExtensionHistory(page, index)
            await page.getByRole('button', { name: kind === 'personal' ? 'Comparar comigo' : 'Comparar análises', exact: true }).click()
            assert.equal(await page.locator('#comparison-history, .comparisonHistory').count(), 0)
          }
          else await page.locator('.historyButton').nth(index).click()
          await comparison.getByText(`Análise selecionada: Resultado ${index + 1}`, { exact: true }).waitFor()
          if (kind === 'experiments') {
            const selector = comparison.getByLabel('Outra análise', { exact: true })
            assert.equal(await selector.locator(`option[value="${index + 1}"]`).count(), 0, 'A própria análise não pode ser selecionada.')
            assert.equal(await selector.locator('option').count(), 3, 'Todas as outras análises devem estar disponíveis.')
            for (const otherId of [index === 0 ? 2 : 1, 3]) {
              await selector.selectOption(String(otherId))
              const summary = comparison.getByRole('region', { name: 'Resumo comparativo dos resultados' })
              await summary.waitFor()
              assert.equal(await summary.getByRole('img').count(), 4)
              assert.equal(await comparison.getByRole('table', { name: 'Resumo comparativo dos resultados' }).count(), 0)
              assert(await summary.getByText('Sem base para comparar', { exact: true }).isVisible())
              assert(await summary.getByText(`Diferença de ${index === 0 || otherId === 1 ? '50,0' : '0,0'} pontos`, { exact: true }).first().isVisible())
              const missing = summary.getByRole('img', { name: /^Diplomático/ })
              assert.equal(await missing.locator('circle, rect').count(), 0, 'Sem estimativa não deve virar ponto zero.')
              const economic = summary.getByRole('img', { name: /^Econômico/ })
              assert.equal(Number(await economic.locator('circle').getAttribute('cx')), 14 + (index === 0 ? 75 : 25) * 3.12)
              if (otherId === 3) {
                const zero = summary.getByRole('img', { name: /^Civil/ })
                assert.equal(Number(await zero.locator('rect').getAttribute('x')), 9, 'Zero válido deve aparecer na extremidade do gráfico.')
              }
              assert.equal(await comparison.getByRole('table', { name: 'Configurações utilizadas' }).count(), lab ? 1 : 0)
              if (!lab) assert(!await comparison.innerText().then(text => /chunk_tokens|Tokens por trecho|configuração não registrada|Chamadas lógicas/.test(text)))
            }
          }
          else assert(await comparison.getByRole('heading', { name: 'Radar comparativo' }).isVisible())
          assert.equal(await comparison.count(), 1)
          assert.equal(await page.getByRole('region', { name: 'Análise selecionada', exact: true }).count(), 0)
          assert.equal(await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).count(), 0)
          assert.equal(await page.locator('#text-input').count(), 0)
          assert.equal(await page.getByRole('region', { name: 'Comparar análises' }).count(), kind === 'experiments' ? 1 : 0)
          assert.equal(await page.getByRole('complementary', { name: 'Comparação pessoal' }).count(), kind === 'personal' ? 1 : 0)
        }
        for (const width of [320, 380, 1280]) {
          await page.setViewportSize({ width, height: 1000 })
          assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}/${kind}: sem overflow em ${width}px`)
        }
        await page.setViewportSize({ width: isExtension ? 380 : 1280, height: 1000 })
        await page.screenshot({ path: resolve(output, `comparison-${name}-${kind}.png`), fullPage: true })
      }
      await page.getByRole('button', { name: 'Análise', exact: true }).click()
      await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
      assert.equal(await page.getByRole('complementary', { name: 'Comparação pessoal' }).count(), 0)
      assert.equal(await page.getByRole('region', { name: 'Comparar análises' }).count(), 0)
      if (isExtension) {
        for (let repeat = 0; repeat < 12; repeat++) {
          await selectExtensionHistory(page, repeat % 2)
        }
      }
      // With only one saved analysis, offer a new analysis instead of self-comparison.
      if (!isExtension) {
        const single = await context.newPage()
        single.on('pageerror', error => errors.push(error.message))
        await single.addInitScript(({ prefix, saved }) => sessionStorage.setItem(`${prefix}-analysis-history-v1`, JSON.stringify(saved.slice(0, 1))), { prefix, saved })
        await single.goto(`http://127.0.0.1:${lab ? 5174 : 5173}/analise`)
        await single.getByRole('button', { name: 'Comparar análises', exact: true }).click()
        await single.getByText('Faça outra análise para comparar os resultados do histórico.', { exact: true }).waitFor()
        assert.equal(await single.getByLabel('Outra análise', { exact: true }).count(), 0)
        await single.close()
      }
      await page.close()
    }
  }
  assert.deepEqual(errors, [])
  console.log('OK: oficial e Lab, app e extensão; comparação entre quaisquer análises diferentes, resumo por eixo e configuração apenas no Lab; sem novas chamadas de análise e sem overflow em 320/380/1280px.')
} finally { await context.close() }
