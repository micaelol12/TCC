import { afterEach, expect, test, vi } from 'vitest'
import { AnalysisTimeoutError, createAnalysisClient, isAnalysis, isCapabilities } from './analysisApi'
import { analysisFixture, capabilities } from '../testing/fixtures'
afterEach(() => vi.useRealTimers())

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
