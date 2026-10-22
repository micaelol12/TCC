import { storagePrefix } from '@8values/shared/domain/experimentConfig'
export const MENU_ID = `${storagePrefix}-analyze-selection`
export type Capture = { id: string; text: string; createdAt: number; windowId: number; tabId: number; source?: string }
export const captureKey = (windowId: number) => `${storagePrefix}-capture-v1:${windowId}`
export const sessionKey = (windowId: number) => `${storagePrefix}-session-v1:${windowId}`
export function makeCapture(text: string, windowId: number, tabId: number, url?: string): Capture {
  let source: string | undefined
  try { const parsed = new URL(url ?? ''); if (['http:', 'https:'].includes(parsed.protocol)) source = parsed.hostname } catch { /* no origin available */ }
  return { id: crypto.randomUUID(), text, createdAt: Date.now(), windowId, tabId, source }
}
export function isCapture(value: unknown): value is Capture {
  if (!value || typeof value !== 'object') return false
  const item = value as Capture
  return typeof item.id === 'string' && typeof item.text === 'string' && Number.isFinite(item.createdAt) &&
    Number.isInteger(item.windowId) && Number.isInteger(item.tabId) && (item.source === undefined || typeof item.source === 'string')
}
