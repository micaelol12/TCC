import { sessionKey } from '../platform/selection'
import { fitSession, type Session } from './sessionState'

/** Cria uma fila de persistência para a sessão da janela, preservando a ordem das gravações. */
export function createSessionStore(windowId: number) {
  let queue = Promise.resolve()
  return {
    /** Ajusta o tamanho da sessão e enfileira sua gravação mesmo após uma falha anterior. */
    save(state: Session): Promise<{ trimmed: boolean }> {
      const fitted = fitSession(state)
      const write = queue.catch(() => undefined).then(() => chrome.storage.session.set({ [sessionKey(windowId)]: fitted.state }))
      queue = write
      return write.then(() => ({ trimmed: fitted.trimmed }))
    },
  }
}
