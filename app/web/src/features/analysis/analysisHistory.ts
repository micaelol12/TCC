import type { AnalysisEntry } from '../../services/analysisApi'
import { storagePrefix } from '@8values/shared/domain/experimentConfig'
import { isAnalysis } from '../../services/analysisApi'

export type Entry = AnalysisEntry

const HISTORY_KEY = `${storagePrefix}-analysis-history-v1`
let memoryEntries: Entry[] = []
let memoryOnly = false

export function readAnalysisHistory(): Entry[] {
  if (memoryOnly) return memoryEntries
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
        isAnalysis(item.analysis) && item.mode === item.analysis.processing_level
    })
    return memoryEntries
  } catch { return memoryEntries }
}

export function saveAnalysisHistory(entries: Entry[]): boolean {
  memoryEntries = entries
  try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(entries)); memoryOnly = false; return true }
  catch { memoryOnly = true; return false }
}

export function clearAnalysisHistory(): void {
  sessionStorage.removeItem(HISTORY_KEY)
  memoryEntries = []
  memoryOnly = false
}
