import { afterEach, expect, test, vi } from 'vitest'
import { analysisFixture } from '../testing/fixtures'
import { buildReport, createReportClient } from './reportApi'

const text = 'Trecho político com evidência.'
const payload = buildReport({ id: 1, title: 'Título privado', text, analysis: analysisFixture(), mode: 'medium', source: 'site-privado.example' }, 'extension', 'Discordo.', 'cd0ab8b1-0419-4d0d-8837-1f122be138d2')
const receipt = { report_id: 'ee7f21b4-65a0-4628-9a19-20cf22e953d9', received_at: '2026-10-13T12:00:00Z', status: 'pending' }
afterEach(() => vi.useRealTimers())

test('report envia apenas o snapshot escolhido e aceite para a API configurada', async () => {
  const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json(receipt, { status: 201 }))
  expect(await createReportClient('http://127.0.0.1:8000/', fetcher).report(payload)).toEqual(receipt)
  const [url, options] = fetcher.mock.calls[0]
  expect(url).toBe('http://127.0.0.1:8000/api/reports')
  expect(JSON.parse(options!.body as string)).toEqual({ submission_id: payload.submission_id, text, analysis: analysisFixture(), comment: 'Discordo.', client: 'extension', storage_consent: true, notice_version: '1' })
  expect(options!.credentials).toBe('omit')
  expect(options!.cache).toBe('no-store')
})

test('recusa envio sem confirmação antes de chamar a rede', async () => {
  const fetcher = vi.fn<typeof fetch>()
  await expect(createReportClient('', fetcher).report({ ...payload, storage_consent: false as never })).rejects.toThrow('Confirme')
  expect(fetcher).not.toHaveBeenCalled()
})

test('nova tentativa manual mantém o identificador e aceita recibo idempotente', async () => {
  const fetcher = vi.fn<typeof fetch>().mockRejectedValueOnce(new TypeError('network')).mockResolvedValueOnce(Response.json(receipt, { status: 200 }))
  const client = createReportClient('', fetcher)
  await expect(client.report(payload)).rejects.toThrow('conexão')
  expect(fetcher).toHaveBeenCalledTimes(1)
  expect(await client.report(payload)).toEqual(receipt)
  expect(fetcher.mock.calls[0][1]!.body).toBe(fetcher.mock.calls[1][1]!.body)
})

test.each([409, 413, 422, 429, 503])('erro HTTP %s não confirma nem repete o envio', async status => {
  const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response('{}', { status }))
  await expect(createReportClient('', fetcher).report(payload)).rejects.toThrow()
  expect(fetcher).toHaveBeenCalledTimes(1)
})

test.each([{}, { ...receipt, report_id: 'invalid' }, { ...receipt, received_at: 'invalid' }, { ...receipt, status: 'unknown' }])('resposta inválida não confirma armazenamento', async data => {
  const fetcher = vi.fn<typeof fetch>().mockResolvedValue(Response.json(data))
  await expect(createReportClient('', fetcher).report(payload)).rejects.toThrow('confirmar')
})

test('timeout aborta a espera e não dispara nova tentativa', async () => {
  vi.useFakeTimers()
  const fetcher = vi.fn<typeof fetch>().mockImplementation((_url, options) => new Promise((_resolve, reject) => {
    options!.signal!.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')), { once: true })
  }))
  const pending = createReportClient('', fetcher).report(payload)
  const failure = expect(pending).rejects.toThrow('sem confirmação')
  await vi.advanceTimersByTimeAsync(15000)
  await failure
  expect(fetcher).toHaveBeenCalledTimes(1)
})
