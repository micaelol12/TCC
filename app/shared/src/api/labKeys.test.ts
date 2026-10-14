import { afterEach, expect, test, vi } from 'vitest'
import { createAnalysisClient } from './analysisApi'
import { labCapabilities, experimentCapabilities } from '../testing/fixtures'
import { modelReady } from '../domain/experimentConfig'

afterEach(() => vi.unstubAllGlobals())
test.each(['typesafe', 'maritaca', 'gemini'] as const)('chave %s é enviada só ao cadastro e apenas o token vai ao armazenamento e às análises', async provider => {
  const storage = new Map<string, string>()
  vi.stubGlobal('sessionStorage', { getItem: (name: string) => storage.get(name) ?? null, setItem: (name: string, value: string) => storage.set(name, value), removeItem: (name: string) => storage.delete(name) })
  const fetcher = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(Response.json({ session_token: 'a'.repeat(43) }))
    .mockResolvedValueOnce(Response.json(labCapabilities))
    .mockResolvedValueOnce(Response.json({ session_token: 'a'.repeat(43) }))
    .mockResolvedValueOnce(Response.json({ status: 'cleared' }))
  const client = createAnalysisClient('http://127.0.0.1:8001', fetcher)
  await client.saveLabKey(provider, 'secret-provider-key')
  expect(JSON.parse(fetcher.mock.calls[0][1]!.body as string)).toEqual({ provider, api_key: 'secret-provider-key' })
  expect([...storage.values()]).toEqual(['a'.repeat(43)])
  await client.getCapabilities()
  expect(new Headers(fetcher.mock.calls[1][1]!.headers).get('X-Lab-Session')).toBe('a'.repeat(43))
  expect(fetcher.mock.calls[1][1]!.body).toBeUndefined()
  await client.removeLabKey(provider)
  expect(fetcher.mock.calls[2][1]!.method).toBe('DELETE')
  expect(fetcher.mock.calls[2][1]!.body).toBeUndefined()
  await client.clearLabSession()
  expect(storage.size).toBe(0)
})
test('modelos Gemini exigem a chave Gemini e não são liberados pela chave Maritaca', () => {
  expect(modelReady(experimentCapabilities, 'sabiazinho-4')).toBe(true)
  expect(modelReady(experimentCapabilities, 'gemini-3.1-flash-lite')).toBe(false)
  expect(modelReady({ ...experimentCapabilities, providers: { ...experimentCapabilities.providers, gemini: true } }, 'gemini-3.7-flash')).toBe(true)
})
