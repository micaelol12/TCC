import { afterEach, expect, test, vi } from 'vitest'
import { createAnalysisClient } from '@8values/shared/api'
import { labCapabilities } from '../../../shared/src/testing/fixtures'
import { labSessionStorage } from './labSession'

afterEach(() => vi.unstubAllGlobals())

function storage() {
  const saved: Record<string, string> = {}
  const temporary = new Map<string, string>()
  const local = {
    get: vi.fn(async (key: string) => ({ [key]: saved[key] })),
    set: vi.fn(async (items: Record<string, string>) => { Object.assign(saved, items) }),
    remove: vi.fn(async (key: string) => { delete saved[key] }),
  }
  vi.stubGlobal('chrome', { storage: { local } })
  vi.stubGlobal('sessionStorage', {
    getItem: (key: string) => temporary.get(key) ?? null,
    removeItem: (key: string) => temporary.delete(key),
  })
  return { saved, temporary, local }
}

const base = 'http://127.0.0.1:8001'
const key = `8values-lab-key-session-v1:${base}`
const token = 'a'.repeat(43)

test('reabrir o painel recupera só o token persistente, sem guardar a chave', async () => {
  const { saved, temporary } = storage()
  const fetcher = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(Response.json({ session_token: token }))
    .mockResolvedValueOnce(Response.json(labCapabilities))
  await createAnalysisClient(base, fetcher, 'extension', labSessionStorage).saveLabKey('gemini', 'secret-provider-key')
  expect(saved).toEqual({ [key]: token })
  expect(temporary.size).toBe(0)
  const reopened = createAnalysisClient(base, fetcher, 'extension', labSessionStorage)
  await reopened.getCapabilities()
  expect(new Headers(fetcher.mock.calls[1][1]!.headers).get('X-Lab-Session')).toBe(token)
})

test('limpar a sessão em outro painel remove o token de painéis já abertos', async () => {
  const { saved } = storage()
  const fetcher = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(Response.json({ session_token: token }))
    .mockResolvedValueOnce(Response.json({ status: 'cleared' }))
    .mockResolvedValueOnce(Response.json(labCapabilities))
  const first = createAnalysisClient(base, fetcher, 'extension', labSessionStorage)
  await first.saveLabKey('typesafe', 'secret-provider-key')
  await createAnalysisClient(base, fetcher, 'extension', labSessionStorage).clearLabSession()
  await first.getCapabilities()
  expect(saved).toEqual({})
  expect(new Headers(fetcher.mock.calls[2][1]!.headers).has('X-Lab-Session')).toBe(false)
})

test('sessão expirada é removida e as capacidades são consultadas sem token', async () => {
  const { saved } = storage()
  saved[key] = token
  const fetcher = vi.fn<typeof fetch>()
    .mockResolvedValueOnce(new Response(null, { status: 401 }))
    .mockResolvedValueOnce(Response.json(labCapabilities))
  await createAnalysisClient(base, fetcher, 'extension', labSessionStorage).getCapabilities()
  expect(saved).toEqual({})
  expect(new Headers(fetcher.mock.calls[0][1]!.headers).get('X-Lab-Session')).toBe(token)
  expect(new Headers(fetcher.mock.calls[1][1]!.headers).has('X-Lab-Session')).toBe(false)
})

test('migra o identificador de um painel que ainda usa sessionStorage', async () => {
  const { saved, temporary } = storage()
  temporary.set(key, token)
  expect(await labSessionStorage.getItem(key)).toBe(token)
  expect(saved).toEqual({ [key]: token })
  expect(temporary.size).toBe(0)
})

test('falha ao persistir a sessão informa que fechar o painel perderia o acesso', async () => {
  const { local } = storage()
  local.set.mockRejectedValueOnce(new Error('quota'))
  const fetcher = vi.fn<typeof fetch>().mockResolvedValueOnce(Response.json({ session_token: token }))
  await expect(createAnalysisClient(base, fetcher, 'extension', labSessionStorage).saveLabKey('typesafe', 'secret-provider-key'))
    .rejects.toThrow('Não foi possível guardar a sessão de chaves na extensão')
})
