import { afterEach, expect, test, vi } from 'vitest'
import { AnalysisTimeoutError, configuredRecipients, createAnalysisClient, isAnalysis, isCapabilities } from './analysisApi'
import { analysisFixture, capabilities, experimentCapabilities } from '../testing/fixtures'
afterEach(() => vi.useRealTimers())

test('configuração oficial informa Gemini e checagem TypeSafe, validando os parâmetros recebidos', () => {
  const caps = { ...capabilities, analysis_defaults: { ...experimentCapabilities.defaults, llm_model: 'gemini-test', semantic_evidence_check: true }, model_providers: { 'gemini-test': 'gemini' as const } }
  expect(isCapabilities(caps)).toBe(true)
  expect(configuredRecipients('high', caps)).toBe('Google Gemini e TypeSafe (checagem de evidências)')
  expect(configuredRecipients('medium', caps)).toContain('Google Gemini')
  expect(configuredRecipients('low', caps)).toBe('TypeSafe (JEV)')
  expect(configuredRecipients('high', null)).toBe('Maritaca (Sabiá)')
  expect(isCapabilities({ ...caps, analysis_defaults: { ...caps.analysis_defaults, chunk_tokens: false } })).toBe(false)
  expect(isCapabilities({ ...caps, model_providers: { 'gemini-test': 'unknown' } })).toBe(false)
})

test('aceita a escala de nove níveis e preserva contratos antigos de cinco níveis', () => {
  const legacy = analysisFixture()
  expect(isAnalysis(legacy)).toBe(true)
  const current = analysisFixture()
  current.schema_version = '2'
  for (const axis of current.axes) {
    axis.level_counts = { ...axis.level_counts, minus4: 0, minus3: 0, plus3: 0, plus4: 0 }
  }
  current.axes[0].evidence_audit = [{ chunk_index: 0, kind: 'semantic', status: 'sustenta', level: 4 }]
  expect(isAnalysis(current)).toBe(true)
  current.schema_version = '1'
  expect(isAnalysis(current)).toBe(false)
  current.schema_version = '2'
  current.axes[0].evidence_audit[0].level = 5
  expect(isAnalysis(current)).toBe(false)
  current.axes[0].evidence_audit[0].level = -4
  delete current.axes[0].level_counts.minus4
  expect(isAnalysis(current)).toBe(false)
})

test('envia apenas texto e modo para a URL configurada, sem credenciais de cookies', async () => {
  const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json(analysisFixture('high')))
  await createAnalysisClient('http://127.0.0.1:8000/', fetcher).analyze('Trecho político com evidência.', 'high', new AbortController().signal)
  const [url, options] = fetcher.mock.calls[0]
  expect(url).toBe('http://127.0.0.1:8000/api/analyze')
  expect(JSON.parse(options!.body as string)).toEqual({ text: 'Trecho político com evidência.', processing_level: 'high' })
  expect(options!.credentials).toBe('omit')
})
test('preserva estimativas ausentes e rejeita contratos incompletos e evidências não verificadas', () => {
  expect(isAnalysis(analysisFixture())).toBe(true)
  expect(isAnalysis({ ...analysisFixture(), axes: [] })).toBe(false)
  const bad = analysisFixture(); bad.axes[0].evidence[0].verified = false as never
  expect(isAnalysis(bad)).toBe(false)
  const guessed = analysisFixture(); guessed.axes[1].pole_a = 50
  expect(isAnalysis(guessed)).toBe(false)
  expect(isCapabilities(capabilities)).toBe(true)
  expect(isCapabilities({ ...capabilities, timeout_seconds: NaN })).toBe(false)
})
test.each([413, 422, 429, 503, 504])('não repete POST com erro HTTP %s', async status => {
  const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response('{}', { status }))
  await expect(createAnalysisClient('', fetcher).analyze('texto', 'low', new AbortController().signal)).rejects.toThrow()
  expect(fetcher).toHaveBeenCalledTimes(1)
})
test('rejeita resposta de outro modo', async () => {
  await expect(createAnalysisClient('', vi.fn().mockResolvedValue(Response.json(analysisFixture('high')))).analyze('texto', 'low', new AbortController().signal)).rejects.toThrow('inválida')
})
test('análise pode aguardar mais de 30 segundos no documento do painel', async () => {
  vi.useFakeTimers()
  const fetcher = vi.fn<typeof fetch>().mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(Response.json(analysisFixture())), 35000)))
  const result = createAnalysisClient('', fetcher).analyze('texto', 'medium', new AbortController().signal)
  await vi.advanceTimersByTimeAsync(35000)
  expect(await result).toEqual(analysisFixture())
})
test('prazo e cancelamento abortam o HTTP sem reenvio', async () => {
  vi.useFakeTimers()
  const fetcher = vi.fn<typeof fetch>().mockImplementation((_url, options) => new Promise((_resolve, reject) => {
    if (options!.signal!.aborted) { reject(new DOMException('aborted', 'AbortError')); return }
    options!.signal!.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')), { once: true })
  }))
  const first = createAnalysisClient('', fetcher).analyze('texto', 'low', new AbortController().signal, 1)
  const failure = expect(first).rejects.toBeInstanceOf(AnalysisTimeoutError)
  await vi.advanceTimersByTimeAsync(16000); await failure
  const controller = new AbortController()
  const second = createAnalysisClient('', fetcher).analyze('texto', 'low', controller.signal)
  const cancelled = expect(second).rejects.toThrow('aborted'); controller.abort(); await cancelled
  expect(fetcher).toHaveBeenCalledTimes(2)
})
