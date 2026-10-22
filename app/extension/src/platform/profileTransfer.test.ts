import { afterEach, expect, test, vi } from 'vitest'
import { QUESTION_HASH } from '@8values/shared/domain/quizScoring'
import { registerProfileTransfer } from './profileTransfer'
import { LOCAL_PROFILE_KEY, TEMP_PROFILE_KEY } from '../storage/preferences'

afterEach(() => vi.unstubAllGlobals())
const origin = 'http://127.0.0.1:5173'
const profile = { schema_version: 1, question_hash: QUESTION_HASH, completed_at: '2026-10-13T12:00:00Z', scores: { economic: 25, diplomatic: 50, state: 75, society: 100 } }
const sender = { id: 'extension-id', frameId: 0, tab: { id: 1 }, url: `${origin}/resultado`, origin }
function setup() {
  let listener: (...args: any[]) => unknown
  const local: Record<string, unknown> = {}, session: Record<string, unknown> = {}
  const area = (data: Record<string, unknown>) => ({ set: vi.fn(async (values: Record<string, unknown>) => { Object.assign(data, values) }), remove: vi.fn(async (key: string) => { delete data[key] }) })
  const storage = { local: area(local), session: area(session) }
  vi.stubGlobal('chrome', { runtime: { id: sender.id, onMessage: { addListener: (fn: typeof listener) => { listener = fn } } }, storage })
  registerProfileTransfer(origin)
  return { local, session, storage, send: (data: unknown, from = sender) => {
    const respond = vi.fn()
    const pending = listener(data, from, respond)
    return { respond, pending }
  } }
}
test('grava só o perfil validado, confirma após salvar e troca entre temporário e permanente', async () => {
  const { send, local, session } = setup()
  const first = send({ type: '8values:save-profile', profile: { ...profile, answers: ['private'] }, permanent: false })
  expect(first.pending).toBe(true)
  expect(first.respond).not.toHaveBeenCalled()
  await vi.waitFor(() => expect(first.respond).toHaveBeenCalledWith({ ok: true }))
  expect(session[TEMP_PROFILE_KEY]).toEqual(profile)
  expect(local[LOCAL_PROFILE_KEY]).toBeNull()
  const second = send({ type: '8values:save-profile', profile, permanent: true })
  await vi.waitFor(() => expect(second.respond).toHaveBeenCalledWith({ ok: true }))
  expect(local[LOCAL_PROFILE_KEY]).toEqual(profile)
  expect(session[TEMP_PROFILE_KEY]).toBeUndefined()
})
test.each([
  { ...sender, url: 'https://evil.example/resultado', origin: 'https://evil.example' },
  { ...sender, url: 'http://127.0.0.1:5174/resultado', origin: 'http://127.0.0.1:5174' },
  { ...sender, origin: 'null' }, { ...sender, frameId: 1 }, { ...sender, id: 'other-extension' },
])('recusa remetente não autorizado %j', from => {
  const { send, storage } = setup()
  const { respond } = send({ type: '8values:save-profile', profile, permanent: true }, from)
  expect(respond).toHaveBeenCalledWith(expect.objectContaining({ ok: false }))
  expect(storage.local.set).not.toHaveBeenCalled()
})
test('recusa perfil inválido e escolha de persistência ausente', () => {
  const { send, storage } = setup()
  for (const data of [{ profile: { ...profile, question_hash: 'old' }, permanent: true }, { profile }]) {
    expect(send({ type: '8values:save-profile', ...data }).respond).toHaveBeenCalledWith(expect.objectContaining({ ok: false }))
  }
  expect(storage.local.set).not.toHaveBeenCalled()
})
test('não confirma sucesso quando o armazenamento falha', async () => {
  const { send, storage } = setup()
  storage.local.set.mockRejectedValueOnce(new Error('quota'))
  const { respond } = send({ type: '8values:save-profile', profile, permanent: true })
  await vi.waitFor(() => expect(respond).toHaveBeenCalledWith(expect.objectContaining({ ok: false })))
})
