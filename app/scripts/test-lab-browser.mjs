import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { analysisFixture, capabilities, labCapabilities, experimentCapabilities } from '../shared/src/testing/fixtures.ts'
import { scaleFixtures } from '../shared/src/testing/scaleFixtures.ts'

const target = process.argv[2] ?? 'chrome'
const output = resolve('test-results')
mkdirSync(output, { recursive: true })
const executablePath = process.env.BROWSER_EXECUTABLE || (target === 'edge' ? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' : 'C:/Program Files/Google/Chrome/Application/chrome.exe')
assert(existsSync(executablePath), 'Defina BROWSER_EXECUTABLE com o caminho do navegador.')
const context = await chromium.launchPersistentContext(resolve(output, `lab-${target}-${Date.now()}`), {
  headless: true, executablePath, viewport: { width: 1100, height: 1000 },
  ignoreDefaultArgs: ['--disable-extensions'], args: ['--enable-unsafe-extension-debugging'],
})
const errors = [], requests = [], reports = []
const keySessions = new Map()
const hash = readFileSync(resolve('shared/src/domain/quizScoring.ts'), 'utf8').match(/QUESTION_HASH = '([^']+)'/)[1]
const profile = { schema_version: 1, question_hash: hash, completed_at: new Date().toISOString(), scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
const text = 'É preciso ampliar as liberdades civis e a cooperação entre países.'
const canonical = value => value && typeof value === 'object' && !Array.isArray(value) ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value
const waitValue = (page, selector, value) => page.waitForFunction(({ selector, value }) => document.querySelector(selector)?.value === value, { selector, value })
async function checkModelSelectionWithoutKeys(page) {
  const selector = page.locator('#lab-llm_model')
  for (const mode of ['low', 'medium', 'high']) {
    await page.locator(`input[name="mode"][value="${mode}"]`).check()
    const primitive = page.locator('#lab-primitiva_polaridade')
    assert.equal(await primitive.isDisabled(), mode === 'high')
    const decisionRule = page.locator('#lab-regra_decisao')
    assert.equal(await decisionRule.isDisabled(), mode === 'high')
    if (mode !== 'high') {
      await decisionRule.selectOption('polo_primeiro')
      assert.equal(await decisionRule.inputValue(), 'polo_primeiro')
      await decisionRule.selectOption('nivel')
      await primitive.selectOption('choice')
      assert.equal(await primitive.inputValue(), 'choice')
      await primitive.selectOption('score')
    }
    assert(await selector.isEnabled(), `Seletor LLM deve abrir no modo ${mode}.`)
    await selector.click()
    await selector.press('Escape')
    for (const model of ['sabia-4', 'sabiazinho-4', 'gemini-3.1-flash-lite', 'gemini-3.7-flash']) {
      await selector.selectOption(model)
      assert.equal(await selector.inputValue(), model)
      assert((await selector.locator('option:checked').innerText()).includes('chave ausente'))
      assert(await page.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled(), 'Selecionar modelo não deve liberar análise sem chaves.')
    }
    if (mode === 'low') assert((await page.locator('#help-llm_model').innerText()).includes('apenas JEV'))
  }
  await page.locator('input[name="mode"][value="medium"]').check()
}
let activeCaps = structuredClone(labCapabilities)
activeCaps.experimental.scales = structuredClone(scaleFixtures)
activeCaps.experimental.defaults.escala = structuredClone(scaleFixtures[1])
activeCaps.experimental.defaults.chunk_strategy = 'sentencas'
try {
  // Both editions use actual built files; providers and report persistence are simulated.
  await context.route(/http:\/\/127\.0\.0\.1:517[34]\//, async route => {
    const url = new URL(route.request().url())
    if (url.pathname.startsWith('/api/')) return route.fallback()
    const asset = url.pathname.startsWith('/assets/')
    const root = url.port === '5174' ? 'web/dist-lab' : 'web/dist'
    await route.fulfill({ path: resolve(root, asset ? url.pathname.slice(1) : 'index.html'), contentType: asset ? (url.pathname.endsWith('.css') ? 'text/css' : 'application/javascript') : 'text/html' })
  })
  await context.route(/http:\/\/127\.0\.0\.1:(800[01]|517[34])\/api\//, async route => {
    const url = new URL(route.request().url())
    const lab = ['8001', '5174'].includes(url.port)
    const sessionToken = route.request().headers()['x-lab-session']
    const session = keySessions.get(sessionToken)
    if (url.pathname.endsWith('/capabilities')) {
      const caps = structuredClone(lab ? activeCaps : capabilities)
      if (lab) {
        for (const provider of ['typesafe', 'maritaca', 'gemini']) caps.experimental.providers[provider] = !!session?.[provider]
        const providers = caps.experimental.providers
        caps.modes = { low: providers.typesafe, medium: providers.typesafe && (providers.maritaca || providers.gemini), high: providers.maritaca || providers.gemini }
        if (!providers[caps.experimental.model_providers[caps.experimental.defaults.llm_model]]) {
          caps.experimental.defaults.llm_model = Object.keys(caps.experimental.model_providers).find(model => providers[caps.experimental.model_providers[model]]) ?? caps.experimental.defaults.llm_model
        }
      }
      await route.fulfill({ json: caps }); return
    }
    if (url.pathname.includes('/lab/api-keys')) {
      assert(lab)
      const current = session ?? {}
      if (route.request().method() === 'POST') {
        const payload = route.request().postDataJSON()
        assert.deepEqual(Object.keys(payload).sort(), ['api_key', 'provider'])
        assert(payload.api_key.startsWith('private-key'))
        current[payload.provider] = true
      } else current[url.pathname.split('/').at(-1)] = false
      const token = sessionToken ?? crypto.randomUUID().replaceAll('-', '') + crypto.randomUUID().replaceAll('-', '')
      keySessions.set(token, current)
      await route.fulfill({ json: { session_token: token, expires_in_seconds: 28800 } }); return
    }
    if (url.pathname.endsWith('/lab/session')) { keySessions.delete(sessionToken); await route.fulfill({ json: { status: 'cleared' } }); return }
    const payload = route.request().postDataJSON()
    if (url.pathname.endsWith('/reports')) {
      assert.equal(payload.analysis.environment, 'lab')
      assert(payload.analysis.effective_config)
      assert(!JSON.stringify(payload).includes('private-key'))
      reports.push(payload)
      await route.fulfill({ status: 201, json: { report_id: crypto.randomUUID(), received_at: new Date().toISOString(), status: 'pending' } }); return
    }
    assert(url.pathname.endsWith('/analyze'))
    if (lab) {
      assert(payload.processing_level === 'high' || session?.typesafe, 'JEV exige a chave da sessão.')
      assert(payload.processing_level === 'low' || session?.[activeCaps.experimental.model_providers[payload.experiment_config.llm_model]], 'LLM exige a chave do provedor selecionado.')
    }
    assert.deepEqual(Object.keys(payload).sort(), lab ? ['experiment_config', 'processing_level', 'text'] : ['processing_level', 'text'])
    requests.push(payload)
    const result = analysisFixture(payload.processing_level, payload.text)
    if (lab) {
      result.schema_version = '3'
      result.escala = payload.experiment_config.escala
      result.escala_hash = createHash('sha256').update(JSON.stringify(canonical(result.escala))).digest('hex')
      for (const axis of result.axes) {
        axis.level_counts_by_key = Object.fromEntries(result.escala.niveis.map(n => [n.chave, n.codigo === 1 ? axis.valid_chunks : 0]))
        if (axis.valid_chunks) {
          axis.pole_a = 100 * result.escala.niveis.find(n => n.codigo === 1).valor
          axis.pole_b = 100 - axis.pole_a
        }
      }
      result.environment = 'lab'; result.config_version = '1'; result.effective_config = payload.experiment_config
      result.config_hash = createHash('sha256').update(JSON.stringify(canonical({ effective_config: result.effective_config, config_version: '1', pipeline_version: result.pipeline_version }))).digest('hex')
      result.lab_execution_id = crypto.randomUUID()
      if (payload.experiment_config.semantic_evidence_check) {
        assert(session?.typesafe, 'Checagem semântica exige TypeSafe inclusive no modo alto.')
        result.axes[0].evidence_audit = [{ chunk_index: 0, kind: 'semantic', status: 'contradiz', level: 1, quote: payload.text, confidence: 0.9, model: 'jev-simulado' }]
      }
      if (payload.experiment_config.jev_evidence_search && payload.processing_level !== 'high') {
        result.axes[0].evidence = [{ chunk_index: 0, quote: payload.text, verified: true }]
        result.axes[0].evidence_audit ??= []
        result.axes[0].evidence_audit.unshift({ chunk_index: 0, kind: 'search', status: 'found', level: 1, quote: payload.text,
          sentence_id: 'S000', start: 0, end: Array.from(payload.text).length, existence_probability: 0.95, confidence: 0.9, model: 'jev-simulado' })
      }
    }
    await route.fulfill({ json: result })
  })
  const cdp = await context.browser().newBrowserCDPSession()
  const standard = await cdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist') })
  const lab = await cdp.send('Extensions.loadUnpacked', { path: resolve('extension/dist-lab') })
  assert.notEqual(standard.id, lab.id)
  if (process.argv.includes('--persistence-only')) {
    const url = `chrome-extension://${lab.id}/sidepanel.html`
    const openPanel = async () => {
      const page = await context.newPage()
      page.on('pageerror', error => errors.push(error.message))
      await page.goto(url)
      await page.locator('#lab-chunk_tokens').waitFor()
      return page
    }
    let page = await openPanel()
    assert.equal(await page.getByRole('button', { name: 'Salvar configuração', exact: true }).count(), 0)
    // Preferences must persist even while provider keys are missing.
    await page.locator('#lab-chunk_tokens').fill('400')
    await page.locator('#lab-chunk_strategy').selectOption('tokens')
    await page.locator('#lab-regra_decisao').selectOption('polo_primeiro')
    await page.locator('#lab-llm_model').selectOption('sabiazinho-4')
    await page.close()
    page = await openPanel()
    await waitValue(page, '#lab-chunk_tokens', '400')
    assert.equal(await page.locator('#lab-chunk_strategy').inputValue(), 'tokens')
    assert.equal(await page.locator('#lab-regra_decisao').inputValue(), 'polo_primeiro')
    assert.equal(await page.locator('#lab-llm_model').inputValue(), 'sabiazinho-4')
    // Incomplete and invalid edits must preserve the latest valid configuration.
    for (const invalid of ['', '99']) {
      await page.locator('#lab-chunk_tokens').fill(invalid)
      await page.reload()
      await waitValue(page, '#lab-chunk_tokens', '400')
    }
    await page.getByRole('tab', { name: 'API keys', exact: true }).click()
    for (const [provider, label] of [['typesafe', 'TypeSafe'], ['maritaca', 'Maritaca']]) {
      await page.locator(`#lab-key-${provider}`).fill(`private-key-${provider}`)
      await page.getByRole('button', { name: `Salvar chave ${label}`, exact: true }).click()
      await page.getByRole('status').filter({ hasText: 'Chave configurada nesta sessão' }).waitFor()
    }
    const stored = await page.evaluate(() => chrome.storage.local.get(null))
    assert(Object.keys(stored).some(key => key.startsWith('8values-lab-key-session-v1:')))
    assert(!JSON.stringify(stored).includes('private-key'))
    await page.close()
    page = await openPanel()
    await page.locator('#text-input').fill(text)
    assert(await page.getByRole('button', { name: 'Analisar texto', exact: true }).isEnabled())
    assert.equal(await page.locator('#lab-llm_model').inputValue(), 'sabiazinho-4')
    await page.getByRole('button', { name: 'Restaurar padrões', exact: true }).click()
    await page.close()
    page = await openPanel()
    await waitValue(page, '#lab-chunk_tokens', '600')
    // Importing also replaces the persisted configuration immediately.
    const preset = { format: '8values-lab-preset', format_version: 2, environment: 'lab', config_version: '1', config: { ...activeCaps.experimental.defaults, chunk_tokens: 450 } }
    await page.locator('#lab-import').setInputFiles({ name: 'preset.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(preset)) })
    await waitValue(page, '#lab-chunk_tokens', '450')
    await page.close()
    page = await openPanel()
    await waitValue(page, '#lab-chunk_tokens', '450')
    await page.getByRole('tab', { name: 'API keys', exact: true }).click()
    await page.getByRole('button', { name: 'Limpar chaves da sessão', exact: true }).click()
    await page.getByRole('status').filter({ hasText: 'Sessão encerrada.' }).waitFor()
    assert(!Object.keys(await page.evaluate(() => chrome.storage.local.get(null))).some(key => key.startsWith('8values-lab-key-session-v1:')))
    await page.close()
    page = await openPanel()
    await page.locator('#text-input').fill(text)
    assert(await page.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled())
    assert.deepEqual(errors, [])
    console.log(JSON.stringify({ browser: target, checks: ['autosave-without-keys', 'invalid-edit-preserves-config', 'close-and-reopen-config-and-keys', 'no-raw-keys-in-storage', 'restore-defaults-persists', 'import-persists', 'clear-keys-persists'], pageErrors: errors }, null, 2))
  } else {
  const website = await context.newPage()
  website.on('pageerror', error => errors.push(error.message))
  await website.goto('http://127.0.0.1:5174/analise')
  await website.locator('#lab-chunk_tokens').waitFor()
  assert.equal(await website.locator('#lab-chunk_strategy').inputValue(), 'sentencas')
  await website.locator('#text-input').fill(text)
  assert(await website.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled(), 'Lab começa sem chaves.')
  await checkModelSelectionWithoutKeys(website)
  await website.getByRole('tab', { name: 'API keys', exact: true }).click()
  await website.locator('#lab-key-typesafe').fill('private-key-typesafe')
  await website.getByRole('button', { name: 'Salvar chave TypeSafe', exact: true }).click()
  await website.getByRole('status').filter({ hasText: 'Chave configurada nesta sessão' }).waitFor()
  await website.locator('#lab-key-gemini').fill('private-key-gemini')
  await website.getByRole('button', { name: 'Salvar chave Gemini', exact: true }).click()
  await website.getByRole('status').filter({ hasText: 'Chave configurada nesta sessão' }).waitFor()
  assert.equal(await website.locator('#lab-key-gemini').inputValue(), '')
  assert(!(await website.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).includes('private-key'))
  await website.getByRole('tab', { name: 'Parâmetros', exact: true }).click()
  assert(await website.locator('#lab-llm_model option[value="gemini-3.1-flash-lite"]').isEnabled())
  await website.locator('#lab-llm_model').selectOption('gemini-3.1-flash-lite')
  await website.locator('#lab-escala').selectOption('0')
  assert.equal(await website.locator('#lab-chunk_tokens').inputValue(), '600')
  await website.locator('#text-input').fill(text)
  await website.locator('#local-title').fill('Configuração A')
  await website.locator('#lab-chunk_tokens').fill('400')
  await website.locator('#lab-chunk_strategy').selectOption('tokens')
  await website.locator('#lab-level_confidence_min').fill('0.7')
  await website.locator('#lab-primitiva_polaridade').selectOption('choice')
  await website.locator('#lab-regra_decisao').selectOption('polo_primeiro')
  await website.locator('#lab-semantic_evidence_check').check()
  await website.locator('#lab-jev_evidence_search').check()
  await website.locator('#lab-evidence_existence_min').fill('0.8')
  assert.equal(await website.getByRole('button', { name: 'Salvar configuração', exact: true }).count(), 0)
  const downloaded = website.waitForEvent('download')
  await website.getByRole('button', { name: 'Exportar JSON', exact: true }).click()
  const download = await downloaded
  const presetPath = resolve(output, `${target}-lab-preset.json`)
  await download.saveAs(presetPath)
  const preset = JSON.parse(readFileSync(presetPath, 'utf8'))
  assert.equal(preset.config.chunk_tokens, 400)
  assert.equal(preset.config.chunk_strategy, 'tokens')
  assert.equal(preset.config.primitiva_polaridade, 'choice')
  assert.equal(preset.config.regra_decisao, 'polo_primeiro')
  assert.equal(preset.config.semantic_evidence_check, true)
  assert.equal(preset.config.jev_evidence_search, true)
  assert.equal(preset.config.evidence_existence_min, 0.8)
  assert.deepEqual(Object.keys(preset.config).sort(), Object.keys(activeCaps.experimental.defaults).sort())
  assert.equal(preset.format_version, 2)
  assert.equal(preset.config.escala.id, 'ordinal_5_v1')
  await website.reload()
  await website.locator('#lab-chunk_tokens').waitFor()
  await waitValue(website, '#lab-chunk_tokens', '400')
  assert.equal(await website.locator('#lab-primitiva_polaridade').inputValue(), 'choice')
  assert.equal(await website.locator('#lab-regra_decisao').inputValue(), 'polo_primeiro')
  assert.equal(await website.locator('#lab-chunk_tokens').inputValue(), '400')
  await website.locator('#lab-chunk_tokens').fill('99')
  await website.reload()
  await waitValue(website, '#lab-chunk_tokens', '400')
  await website.locator('#text-input').fill(text)
  await website.locator('#local-title').fill('Configuração A')
  await website.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await website.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  assert.equal(requests[0].experiment_config.chunk_tokens, 400)
  assert.equal(requests[0].experiment_config.chunk_strategy, 'tokens')
  assert.equal(requests[0].experiment_config.primitiva_polaridade, 'choice')
  assert.equal(requests[0].experiment_config.regra_decisao, 'polo_primeiro')
  assert.equal(requests[0].experiment_config.escala.id, 'ordinal_5_v1')
  await website.getByText('Escala: 5 níveis · ordinal_5_v1 · v1.', { exact: true }).waitFor()
  await website.getByText('Distribuição e evidências de Econômico', { exact: true }).click()
  await website.getByText('Contradiz a posição atribuída', { exact: true }).waitFor()
  await website.getByText('Passagem encontrada', { exact: true }).waitFor()
  await website.screenshot({ path: resolve(output, `${target}-lab-evidence-web.png`), fullPage: true })
  await website.getByRole('button', { name: 'Usar este texto em nova análise', exact: true }).click()
  await website.locator('#local-title').fill('Configuração B')
  await website.getByRole('button', { name: 'Restaurar padrões', exact: true }).click()
  assert.equal(await website.locator('#lab-chunk_strategy').inputValue(), 'sentencas')
  assert.equal(await website.locator('#lab-primitiva_polaridade').inputValue(), 'score')
  assert.equal(await website.locator('#lab-regra_decisao').inputValue(), 'nivel')
  await website.getByLabel('Alto', { exact: false }).check()
  assert(await website.locator('#lab-level_confidence_min').isDisabled())
  await website.locator('#lab-llm_model').selectOption('gemini-3.7-flash')
  await website.locator('#lab-semantic_evidence_check').check()
  assert(await website.locator('#lab-jev_evidence_search').isDisabled())
  assert(await website.locator('#lab-jev_model').isEnabled())
  assert((await website.locator('.privacyNote').innerText()).includes('TypeSafe'))
  assert((await website.locator('.privacyNote').innerText()).includes('Google Gemini'))
  await website.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await website.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await website.locator('#lab-compare').selectOption('1')
  await website.getByText('Escala: 9 níveis · ordinal_9_v1 · v1.', { exact: true }).waitFor()
  assert((await website.getByRole('region', { name: 'Comparar experimentos' }).innerText()).includes('400'))
  await website.getByText('Configuração utilizada · versão de teste', { exact: true }).click()
  await website.getByRole('button', { name: 'Reportar classificação', exact: true }).click()
  await website.getByLabel('Estou ciente e concordo com o envio e o armazenamento desses dados').check()
  await website.getByRole('button', { name: 'Enviar report', exact: true }).click()
  await website.getByRole('status').filter({ hasText: 'Report enviado. O trecho e a análise foram armazenados' }).waitFor()
  assert.equal(reports[0].analysis.effective_config.llm_model, 'gemini-3.7-flash')
  await website.getByRole('status').filter({ hasText: 'Execução gravada no banco' }).waitFor()
  await website.screenshot({ path: resolve(output, `${target}-lab-web-result.png`), fullPage: true })
  await website.setViewportSize({ width: 390, height: 844 })
  assert(await website.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Site deve caber em celular.')
  await website.reload()
  await website.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await website.getByRole('button', { name: 'Usar este texto em nova análise', exact: true }).click()
  await website.locator('#lab-import').setInputFiles(presetPath)
  await waitValue(website, '#lab-chunk_tokens', '400')
  assert.equal(await website.locator('#lab-chunk_tokens').inputValue(), '400')
  const before = requests.length
  await website.locator('#lab-import').setInputFiles({ name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ ...preset, private_key: 'private-key' })) })
  await website.getByRole('alert').filter({ hasText: 'inválido' }).waitFor()
  assert.equal(requests.length, before)
  await website.locator('#lab-chunk_tokens').fill('99')
  assert(await website.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled())
  await website.getByRole('button', { name: 'Restaurar padrões', exact: true }).click()
  await website.screenshot({ path: resolve(output, `${target}-lab-web-composer.png`), fullPage: true })

  let panel = await context.newPage()
  panel.on('pageerror', error => errors.push(error.message))
  await panel.setViewportSize({ width: 380, height: 900 })
  await panel.goto(`chrome-extension://${lab.id}/sidepanel.html`)
  const configSummary = panel.locator('.experimentDisclosure > summary')
  await configSummary.waitFor()
  assert.equal(await panel.locator('.experimentDisclosure').getAttribute('open'), null)
  assert.equal(await panel.locator('#lab-chunk_tokens').isVisible(), false)
  await panel.screenshot({ path: resolve(output, `${target}-lab-config-collapsed.png`), fullPage: true })
  await configSummary.focus()
  await configSummary.press('Enter')
  await panel.locator('#lab-chunk_tokens').waitFor()
  await panel.locator('#lab-chunk_tokens').fill('450')
  await configSummary.click()
  assert.equal(await panel.locator('#lab-chunk_tokens').isVisible(), false)
  await configSummary.focus()
  await configSummary.press('Space')
  assert.equal(await panel.locator('#lab-chunk_tokens').inputValue(), '450', 'Recolher preserva os parâmetros.')
  assert(await panel.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  await panel.screenshot({ path: resolve(output, `${target}-lab-config-expanded.png`), fullPage: true })
  assert.equal(await panel.locator('#lab-chunk_strategy').inputValue(), 'sentencas')
  await panel.locator('#text-input').fill(text)
  assert(await panel.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled(), 'Extensão exige suas próprias chaves.')
  await checkModelSelectionWithoutKeys(panel)
  await panel.getByRole('tab', { name: 'API keys', exact: true }).click()
  await panel.locator('#lab-key-typesafe').fill('private-key-extension-typesafe')
  await panel.getByRole('button', { name: 'Salvar chave TypeSafe', exact: true }).click()
  await panel.getByRole('status').filter({ hasText: 'Chave configurada nesta sessão' }).waitFor()
  await panel.locator('#lab-key-maritaca').fill('private-key-maritaca')
  await panel.getByRole('button', { name: 'Salvar chave Maritaca', exact: true }).click()
  await panel.getByRole('status').filter({ hasText: 'Chave configurada nesta sessão' }).waitFor()
  await panel.getByRole('tab', { name: 'Parâmetros', exact: true }).click()
  await panel.locator('#lab-llm_model').selectOption('sabiazinho-4')
  await panel.locator('#text-input').fill(text)
  await panel.locator('#lab-import').setInputFiles(presetPath)
  await waitValue(panel, '#lab-chunk_tokens', '400')
  assert.equal(await panel.locator('#lab-chunk_tokens').inputValue(), '400')
  assert.equal(await panel.locator('#lab-primitiva_polaridade').inputValue(), 'choice')
  assert.equal(await panel.locator('#lab-regra_decisao').inputValue(), 'polo_primeiro')
  await panel.locator('#lab-llm_model').selectOption('sabiazinho-4')
  assert.equal(await panel.getByRole('button', { name: 'Salvar configuração', exact: true }).count(), 0)
  const panelUrl = panel.url()
  const storedSession = await panel.evaluate(() => chrome.storage.local.get(null))
  assert(Object.keys(storedSession).some(key => key.startsWith('8values-lab-key-session-v1:')))
  assert(!JSON.stringify(storedSession).includes('private-key'))
  await panel.close()
  panel = await context.newPage()
  panel.on('pageerror', error => errors.push(error.message))
  await panel.setViewportSize({ width: 380, height: 900 })
  await panel.goto(panelUrl)
  await waitValue(panel, '#lab-chunk_tokens', '400')
  assert.equal(await panel.locator('#lab-llm_model').inputValue(), 'sabiazinho-4')
  assert.equal(await panel.locator('#lab-primitiva_polaridade').inputValue(), 'choice')
  assert.equal(await panel.locator('#lab-regra_decisao').inputValue(), 'polo_primeiro')
  await panel.locator('#text-input').fill(text)
  assert(await panel.getByRole('button', { name: 'Analisar texto', exact: true }).isEnabled(), 'Reabrir o painel preserva as chaves e a última configuração.')
  await panel.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await panel.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  assert.equal(requests.at(-1).experiment_config.llm_model, 'sabiazinho-4')
  assert.equal(requests.at(-1).experiment_config.chunk_strategy, 'tokens')
  assert.equal(requests.at(-1).experiment_config.primitiva_polaridade, 'choice')
  assert.equal(requests.at(-1).experiment_config.regra_decisao, 'polo_primeiro')
  assert.equal(requests.at(-1).experiment_config.escala.id, 'ordinal_5_v1')
  await panel.getByText('Escala: 5 níveis · ordinal_5_v1 · v1.', { exact: true }).waitFor()
  assert.equal(requests.at(-1).experiment_config.semantic_evidence_check, true)
  await panel.getByText('Distribuição e evidências de Econômico', { exact: true }).click()
  await panel.getByText('Contradiz a posição atribuída', { exact: true }).waitFor()
  await panel.getByText('Passagem encontrada', { exact: true }).waitFor()
  assert(await panel.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
  await panel.screenshot({ path: resolve(output, `${target}-lab-evidence-extension.png`), fullPage: true })
  await panel.reload()
  await panel.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await panel.getByRole('button', { name: 'Editar e reanalisar', exact: true }).click()
  await panel.locator('.experimentDisclosure > summary').click()
  await panel.getByRole('button', { name: 'Restaurar padrões', exact: true }).click()
  await panel.reload()
  await waitValue(panel, '#lab-min_valid_chunks', String(activeCaps.experimental.defaults.min_valid_chunks))
  await panel.locator('.experimentDisclosure > summary').click()
  assert.equal(await panel.locator('#lab-chunk_tokens').inputValue(), String(activeCaps.experimental.defaults.chunk_tokens))
  await panel.locator('#lab-min_valid_chunks').fill('1')
  await panel.getByRole('button', { name: 'Analisar texto', exact: true }).click()
  await panel.getByRole('heading', { name: 'Quatro eixos', exact: true }).waitFor()
  await panel.locator('.sessionHistory summary').click()
  await panel.locator('#lab-compare').selectOption({ index: 1 })
  assert((await panel.getByRole('region', { name: 'Comparar experimentos' }).innerText()).includes('400'))
  assert(await panel.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Painel deve caber na largura.')
  await panel.screenshot({ path: resolve(output, `${target}-lab-extension.png`), fullPage: true })
  await panel.getByRole('button', { name: 'Editar e reanalisar', exact: true }).click()
  await panel.locator('.experimentDisclosure > summary').click()
  await panel.locator('#lab-min_valid_chunks').fill('16')
  activeCaps.experimental.ranges.min_valid_chunks.max = 5
  activeCaps.experimental.defaults.min_valid_chunks = 5
  await panel.getByRole('button', { name: 'Verificar conexão e modos', exact: true }).click()
  await panel.getByRole('alert').filter({ hasText: 'entre 1 e 5' }).waitFor()
  assert(await panel.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled())
  await panel.getByRole('button', { name: 'Restaurar padrões', exact: true }).click()

  for (const page of [website, panel]) {
    await page.getByRole('tab', { name: 'API keys', exact: true }).click()
    await page.getByRole('button', { name: 'Limpar chaves da sessão', exact: true }).click()
    await page.getByRole('status').filter({ hasText: 'Sessão encerrada. Cadastre suas chaves' }).waitFor()
    assert(await page.getByRole('button', { name: 'Analisar texto', exact: true }).isDisabled())
    assert.equal(await page.getByRole('button', { name: 'Usar chaves do servidor', exact: true }).count(), 0)
    await page.getByRole('tab', { name: 'Parâmetros', exact: true }).click()
    await checkModelSelectionWithoutKeys(page)
  }

  if (process.argv.includes('--parameters-only')) {
    assert.deepEqual(errors, [])
    console.log(JSON.stringify({ browser: target, checks: ['sentence-default-web-and-extension', 'strategy-in-preset-and-request', 'strategy-autosave', 'strategy-restored-default', 'preset-import', 'effective-config', 'same-text-comparison', 'report-metadata', 'mobile-width'], analyses: requests.length, reports: reports.length, pageErrors: errors }, null, 2))
  } else {
  // Keep both extensions installed and verify transfer reaches only the matching edition.
  await website.evaluate(profile => localStorage.setItem('values-lab-profile-v1', JSON.stringify(profile)), profile)
  await website.goto('http://127.0.0.1:5174/resultado')
  await website.getByRole('button', { name: 'Usar resultado na extensão', exact: true }).click()
  await website.getByRole('status').filter({ hasText: 'Resultado enviado para esta sessão' }).waitFor()
  const savedLab = await panel.evaluate(() => chrome.storage.session.get('8values-lab-profile-session-v1'))
  assert.deepEqual(savedLab['8values-lab-profile-session-v1'], profile)
  const standardPanel = await context.newPage()
  await standardPanel.goto(`chrome-extension://${standard.id}/sidepanel.html`)
  await standardPanel.locator('#text-input').waitFor()
  assert.equal(await standardPanel.locator('#lab-chunk_tokens').count(), 0)
  assert.deepEqual(await standardPanel.evaluate(() => chrome.storage.session.get('8values-profile-session-v1')), {})
  await website.goto('http://127.0.0.1:5173/analise')
  await website.locator('#text-input').waitFor()
  assert.equal(await website.locator('#lab-chunk_tokens').count(), 0)
  assert.deepEqual(errors, [])
  const report = { browser: target, version: context.browser().version(), checks: ['evidence-controls-and-results', 'evidence-preset-transfer', 'high-semantic-recipient', 'lab-web', 'lab-extension', 'api-keys-tabs', 'models-gated-by-provider-key', 'no-keys-in-browser-storage', 'key-session-isolation', 'gemini-selection', 'sabiazinho-selection', 'execution-record-receipt', 'edit-config', 'saved-preset', 'preset-export-import', 'invalid-config', 'high-mode-controls', 'effective-config', 'same-text-comparison', 'history-reload', 'report-metadata', 'mobile-width', 'isolated-standard-build', 'profile-transfer-to-matching-edition'], analyses: requests.length, reports: reports.length, pageErrors: errors }
  writeFileSync(resolve(output, `${target}-lab-report.json`), JSON.stringify(report, null, 2))
  console.log(JSON.stringify(report, null, 2))
  }
  }
} finally { await context.close() }
