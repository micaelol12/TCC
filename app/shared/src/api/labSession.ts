import { isLabBuild } from '../domain/experimentConfig'

export type LabSessionStorage = {
  getItem: (key: string) => string | null | Promise<string | null>
  setItem: (key: string, value: string) => void | Promise<void>
  removeItem: (key: string) => void | Promise<void>
}

export function createLabSession(apiBaseUrl: string, labClient: 'web' | 'extension', sessionStore?: LabSessionStorage) {
  const sessionKey = `8values-lab-key-session-v1:${apiBaseUrl || 'same-origin'}`
  let memoryToken = ''

  async function readToken(): Promise<string> {
    try {
      return await (sessionStore ?? sessionStorage).getItem(sessionKey) ?? ''
    } catch {
      return memoryToken
    }
  }

  async function saveToken(token: string): Promise<void> {
    memoryToken = token
    try {
      const storage = sessionStore ?? sessionStorage
      if (token) await storage.setItem(sessionKey, token)
      else await storage.removeItem(sessionKey)
    } catch {
      if (sessionStore) throw new Error('Não foi possível guardar a sessão de chaves na extensão. Tente novamente antes de fechar o painel.')
    }
  }

  async function buildHeaders() {
    const token = await readToken()
    return {
      ...(token ? { 'X-Lab-Session': token } : {}),
      ...(isLabBuild ? { 'X-Lab-Client': labClient } : {}),
    }
  }

  return { readToken, saveToken, buildHeaders }
}
