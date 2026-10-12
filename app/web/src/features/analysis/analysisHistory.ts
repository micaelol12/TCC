import type { Analysis, Mode } from '../../services/analysisApi'

export type Entry = { id: number; title: string; text: string; analysis: Analysis; mode: Mode }

const HISTORY_KEY = '8values-analysis-history-v1'
let memoryEntries: Entry[] = []

export function readAnalysisHistory(): Entry[] {
  try {
    const raw = sessionStorage.getItem(HISTORY_KEY)
    if (!raw) return memoryEntries
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return memoryEntries
    memoryEntries = parsed.filter((entry): entry is Entry => {
      if (!entry || typeof entry !== 'object') return false
      const item = entry as Partial<Entry>
      return Number.isSafeInteger(item.id) && typeof item.title === 'string' &&
        typeof item.text === 'string' && ['low', 'medium', 'high'].includes(item.mode ?? '') &&
        Array.isArray(item.analysis?.axes) && Array.isArray(item.analysis?.chunks) &&
        Array.isArray(item.analysis?.warnings) && Array.isArray(item.analysis?.models_used)
    })
    return memoryEntries
  } catch { return memoryEntries }
}

export function saveAnalysisHistory(entries: Entry[]): void {
  memoryEntries = entries
  try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(entries)) } catch { /* keep this page's memory copy */ }
}

export function clearAnalysisHistory(): void {
  memoryEntries = []
  try { sessionStorage.removeItem(HISTORY_KEY) } catch { /* storage unavailable */ }
}
