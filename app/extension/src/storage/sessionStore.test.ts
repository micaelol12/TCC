import { afterEach, expect, test, vi } from 'vitest'
import { createSessionStore } from './sessionStore'
import { emptySession } from './sessionState'
afterEach(() => vi.unstubAllGlobals())
test('escritas de uma janela preservam ordem e a fila se recupera após falha', async () => {
  let release: () => void
  const first = new Promise<void>(resolve => { release = resolve })
  const set = vi.fn().mockReturnValueOnce(first).mockRejectedValueOnce(new Error('quota')).mockResolvedValue(undefined)
  vi.stubGlobal('chrome', { storage: { session: { set } } })
  const store = createSessionStore(5)
  const a = store.save(emptySession()), b = store.save({ ...emptySession(), draft: { text: 'b', title: '' } })
  const failure = expect(b).rejects.toThrow('quota')
  await vi.waitFor(() => expect(set).toHaveBeenCalledTimes(1))
  release!(); await a; await failure
  await store.save({ ...emptySession(), draft: { text: 'c', title: '' } })
  expect(set).toHaveBeenCalledTimes(3)
  expect(set.mock.calls[2][0]['8values-session-v1:5'].draft.text).toBe('c')
})
