import { sessionKey } from '../platform/selection'
import { fitSession, type Session } from './sessionState'

export function createSessionStore(windowId: number) {
  let queue = Promise.resolve()
  return {
    save(state: Session): Promise<{ trimmed: boolean }> {
      const fitted = fitSession(state)
      const write = queue.catch(() => undefined).then(() => chrome.storage.session.set({ [sessionKey(windowId)]: fitted.state }))
      queue = write
      return write.then(() => ({ trimmed: fitted.trimmed }))
    },
  }
}
