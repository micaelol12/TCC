import type { LabSessionStorage } from '@8values/shared/api'

// Keep only the opaque API session identifier, shared by all extension panels.
export const labSessionStorage: LabSessionStorage = {
  /** Lê o token compartilhado e migra o identificador de um painel de versão anterior. */
  async getItem(key) {
    const saved = (await chrome.storage.local.get(key))[key]
    if (typeof saved === 'string') return saved
    // Preserve a session from a panel that was already open before this update.
    const previous = sessionStorage.getItem(key)
    if (previous) {
      await chrome.storage.local.set({ [key]: previous })
      sessionStorage.removeItem(key)
    }
    return previous
  },
  /** Persiste o token entre painéis e remove a cópia antiga da aba. */
  async setItem(key, value) {
    await chrome.storage.local.set({ [key]: value })
    sessionStorage.removeItem(key)
  },
  /** Apaga o identificador de sessão tanto do armazenamento compartilhado quanto do painel. */
  async removeItem(key) {
    await chrome.storage.local.remove(key)
    sessionStorage.removeItem(key)
  },
}
