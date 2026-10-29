import assert from 'node:assert/strict'
import { existsSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities, experimentCapabilities } from '../shared/src/testing/fixtures.ts'
import { scaleFixtures } from '../shared/src/testing/scaleFixtures.ts'

// Exercise the actual app and unpacked extension with test-only API responses.
const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const executablePath = process.env.BROWSER_EXECUTABLE || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const context = await chromium.launchPersistentContext(resolve(output, `evidence-${Date.now()}`), {
  headless: true, executablePath, viewport: { width: 380, height: 900 },
  ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
})
const errors = []
const text = 'A tributação progressiva deve financiar a ampliação dos serviços públicos.'
let historical = false
let minimum = 16
function fixture(mode) {
  const analysis = analysisFixture(mode, text)
  if (historical) return analysis
  const scale = structuredClone(scaleFixtures[1])
  Object.assign(analysis, { schema_version: '3', escala: scale, escala_hash: 'a'.repeat(64),
    effective_config: { ...experimentCapabilities.defaults, min_valid_chunks: minimum, escala: scale, regra_decisao: 'polo_primeiro' },
    config_version: '1', config_hash: 'b'.repeat(64), environment: 'development' })
  analysis.chunks.push({ index: 3, text: 'Outro trecho cuja intensidade não foi determinada.' })
  Object.assign(analysis.axes[2], { status: 'abstained', valid_chunks: 0, pole_a: null, pole_b: null, evidence: [], level_counts: { minus2: 0, minus1: 0, zero: 0, plus1: 0, plus2: 0 } })
  Object.assign(analysis.axes[3], { pole_a: 50, pole_b: 50, level_counts: { minus2: 0, minus1: 0, zero: 1, plus1: 0, plus2: 0 } })
  for (const axis of analysis.axes) {
    axis.total_chunks = 2; axis.coverage = axis.valid_chunks / 2
    axis.sufficient_evidence = axis.valid_chunks >= minimum
    axis.level_counts_by_key = Object.fromEntries(scale.niveis.map(n => [n.chave, n.codigo === (axis.axis === 'society' ? 0 : 1) ? axis.valid_chunks : 0]))
  }
  const axis = analysis.axes[0]
  axis.evidence_audit = [
    { chunk_index: 0, kind: 'search', status: 'found', level: 1, quote: text, sentence_id: 'S000', start: 0, end: Array.from(text).length, existence_probability: .95 },
    { chunk_index: 0, kind: 'semantic', status: 'contradiz', level: 1, quote: text, confidence: .9 },
  ]
  axis.jev_diagnostics = [
    { chunk_index: 0, regra_decisao: 'polo_primeiro', relevante: true, nivel_jev_bruto: 1, nivel: 1, grupo_mais_provavel: 'A',
      probabilities_abc: { A: .75, B: .15, C: .1 }, margem_grupo: .6, probabilidade_nivel_condicional: .4 / .75, confianca_nivel: .4,
      probabilities_nivel: Object.fromEntries(scale.niveis.map((n, i) => [n.chave, [.02, .03, .05, .05, .1, .4, .2, .1, .05][i]])) },
    { chunk_index: 3, regra_decisao: 'polo_primeiro', relevante: true, nivel_jev_bruto: null, nivel: null, grupo_mais_provavel: 'A',
      probabilities_abc: { A: .7, B: .2, C: .1 }, margem_grupo: .5, probabilidade_nivel_condicional: null, confianca_nivel: .35,
      probabilities_nivel: Object.fromEntries(scale.niveis.map((n, i) => [n.chave, [.05, .05, .05, .05, .1, .35, .35, 0, 0][i]])) },
  ]
  return analysis
}
try {
  await context.route('http://127.0.0.1:5173/**', async route => {
    const url = new URL(route.request().url())
    if (url.pathname.startsWith('/api/')) return route.fallback()
    const asset = url.pathname.startsWith('/assets/')
    await route.fulfill({ path: resolve('web/dist', asset ? url.pathname.slice(1) : 'index.html'), contentType: asset ? (url.pathname.endsWith('.css') ? 'text/css' : 'application/javascript') : 'text/html' })
  })
  await context.route(/http:\/\/127\.0\.0\.1:(8000|5173)\/api\//, async route => {
    if (route.request().url().endsWith('/capabilities')) return route.fulfill({ json: capabilities })
    assert(route.request().url().endsWith('/analyze'))
    await route.fulfill({ json: fixture(route.request().postDataJSON().processing_level) })
  })
  const cdp = await context.browser().newBrowserCDPSession()
  const extension = await cdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist') })
  for (const [name, url] of [['extension', `chrome-extension://${extension.id}/sidepanel.html`], ['app', 'http://127.0.0.1:5173/analise']]) {
    historical = false
    minimum = 16
    const page = await context.newPage()
    page.on('pageerror', error => errors.push(error.message))
    await page.goto(url)
    await page.locator('#text-input').fill(text)
    await page.locator('#local-title').fill('Caso 1')
    await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
    const explorer = page.getByRole('region', { name: 'Distribuição e evidências', exact: true })
    await explorer.waitFor()
    assert.equal(await explorer.getByRole('article').count(), 1, 'Busca e parecer do mesmo trecho devem ficar juntos.')
    assert(await explorer.getByText('Citação literal localizada', { exact: true }).isVisible())
    assert(await explorer.getByText('Contradiz a posição atribuída', { exact: true }).isVisible())
    assert.equal(await explorer.locator('blockquote').count(), 1, 'A mesma citação não deve se repetir em cada verificação.')
    assert(await explorer.getByText('Poucos trechos válidos', { exact: true }).isVisible())
    assert((await explorer.innerText()).includes('Há 1 trecho válido neste eixo. O mínimo configurado nesta análise é 16.'))
    await explorer.getByRole('tab', { name: 'Distribuição', exact: true }).click()
    assert.equal(await explorer.getByRole('list', { name: 'Distribuição final de Econômico' }).getByRole('listitem').count(), 9)
    const finalLevel = explorer.getByRole('listitem').filter({ hasText: '+1 · Igualdade leve' })
    assert((await finalLevel.innerText()).includes('100,0%'), 'A porcentagem deve considerar o único trecho válido, e não os dois trechos analisados.')
    assert((await finalLevel.innerText()).includes('1 trecho'), 'A contagem deve continuar visível junto à porcentagem.')
    await explorer.getByRole('tab', { name: 'Distribuição', exact: true }).press('ArrowRight')
    assert.equal(await explorer.getByRole('tab', { name: 'Modelo JEV', exact: true }).getAttribute('aria-selected'), 'true')
    assert((await explorer.innerText()).includes('53,3%'), 'Suporte dentro do polo deve permanecer diferente da confiança do nível.')
    assert((await explorer.innerText()).includes('40,0%'))
    await explorer.getByLabel('Examinar trecho', { exact: true }).selectOption('3')
    assert((await explorer.innerText()).includes('Intensidade incerta: houve empate'))
    await explorer.getByRole('button', { name: 'Diplomático', exact: true }).click()
    assert(await explorer.getByText('Sem relevância neste eixo', { exact: true }).isVisible())
    assert((await explorer.getByRole('button', { name: 'Diplomático', exact: true }).innerText()).includes('Sem relevância'))
    assert.equal(await explorer.getByText('Poucos trechos válidos', { exact: true }).count(), 0)
    assert.equal(await explorer.getByRole('tab', { name: 'Modelo JEV', exact: true }).count(), 0)
    await explorer.screenshot({ path: resolve(output, `evidence-${name}-no-relevance.png`) })
    await explorer.getByRole('tab', { name: 'Distribuição', exact: true }).click()
    assert(await explorer.getByText('Sem distribuição final', { exact: true }).isVisible())
    assert.equal(await explorer.getByRole('listitem').count(), 0, 'Eixo irrelevante não deve parecer uma distribuição neutra.')
    await explorer.getByRole('button', { name: 'Civil', exact: true }).click()
    assert(await explorer.getByText('Classificação indeterminada', { exact: true }).isVisible())
    assert.equal(await explorer.getByText('Sem relevância neste eixo', { exact: true }).count(), 0)
    assert.equal(await explorer.getByText('Poucos trechos válidos', { exact: true }).count(), 0)
    await explorer.getByRole('button', { name: 'Social', exact: true }).click()
    assert.equal(await explorer.getByText('Sem relevância neste eixo', { exact: true }).count(), 0)
    assert(await explorer.getByText('Poucos trechos válidos', { exact: true }).isVisible())
    await explorer.getByRole('tab', { name: 'Distribuição', exact: true }).click()
    assert((await explorer.getByRole('listitem').filter({ hasText: '0 · sem posicao' }).innerText()).includes('1 trecho'), 'O nível sem posição deve continuar sendo contado como válido.')
    await explorer.getByRole('button', { name: 'Econômico', exact: true }).click()
    for (const width of [320, 380, 1280]) {
      await page.setViewportSize({ width, height: 900 })
      for (const tab of ['Evidências', 'Distribuição', 'Modelo JEV']) {
        await explorer.getByRole('tab', { name: tab, exact: true }).click()
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}: sem overflow em ${width}px na aba ${tab}`)
      }
    }
    await page.setViewportSize({ width: name === 'extension' ? 380 : 1280, height: 1000 })
    await explorer.getByRole('tab', { name: 'Evidências', exact: true }).click()
    await explorer.screenshot({ path: resolve(output, `evidence-${name}.png`) })
    await explorer.getByRole('tab', { name: 'Distribuição', exact: true }).click()
    await explorer.screenshot({ path: resolve(output, `evidence-${name}-distribution.png`) })
    await explorer.getByRole('tab', { name: 'Modelo JEV', exact: true }).click()
    await explorer.getByLabel('Examinar trecho', { exact: true }).selectOption('0')
    await explorer.getByRole('list').last().screenshot({ path: resolve(output, `evidence-${name}-model-levels.png`) })
    minimum = 1
    const reuse = page.getByRole('button', { name: name === 'extension' ? 'Editar e reanalisar' : 'Usar este texto em nova análise', exact: true })
    await reuse.click()
    await page.locator('#local-title').fill('Caso 2')
    await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
    await explorer.waitFor()
    assert.equal(await explorer.getByText('Poucos trechos válidos', { exact: true }).count(), 0, 'Ao atingir o mínimo configurado, o aviso deve desaparecer.')
    historical = true
    await reuse.click()
    await page.locator('#local-title').fill('Caso 3')
    await page.getByRole('button', { name: 'Analisar texto', exact: true }).click()
    await explorer.waitFor()
    assert((await explorer.innerText()).includes('cujo valor não foi registrado nesta análise'), 'Análises antigas não devem assumir o mínimo atual.')
    await explorer.getByRole('tab', { name: 'Distribuição', exact: true }).click()
    assert.equal(await explorer.getByRole('listitem').count(), 5, 'Análises históricas devem preservar a escala de cinco níveis.')
    assert.equal(await explorer.getByRole('tab', { name: 'Modelo JEV', exact: true }).count(), 0)
    await page.getByRole('button', { name: 'Comparar comigo', exact: true }).click()
    const comparison = page.getByRole('complementary', { name: 'Comparação pessoal', exact: true })
    await comparison.waitFor()
    for (const index of [0, 2, 0, 2]) {
      if (name === 'extension') await page.getByLabel('Análise do histórico', { exact: true }).selectOption({ index })
      else await page.locator('.historyButton').nth(index).click()
      await comparison.getByText(`Análise selecionada: Caso ${index + 1}`, { exact: true }).waitFor()
      assert.equal(await comparison.count(), 1, 'A troca no histórico deve manter uma única comparação.')
      assert.equal(await page.getByRole('region', { name: 'Análise selecionada', exact: true }).count(), 0, 'O histórico não deve abrir a análise enquanto se está comparando.')
      assert.equal(await page.locator('#text-input').count(), 0)
    }
    for (const width of [320, 380, 1280]) {
      await page.setViewportSize({ width, height: 1000 })
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}: comparação deve caber em ${width}px`)
      assert.equal(await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).count(), 0)
    }
    await page.getByRole('button', { name: 'Análise', exact: true }).click()
    await page.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
    await page.close()
  }
  assert.deepEqual(errors, [])
  console.log('OK: app e extensão; evidências agrupadas, auditoria contraditória, escalas históricas e configuráveis, diagnóstico por trecho, navegação por teclado e larguras 320/380/1280px.')
} finally { await context.close() }
