import type { Mode } from '../../services/analysisApi'
import { storagePrefix } from '@8values/shared/domain/experimentConfig'

export type AnalysisDraft = { title: string; text: string; mode: Mode }
const DRAFT_KEY = `${storagePrefix}-analysis-draft-v1`
const emptyDraft = (): AnalysisDraft => ({ title: '', text: '', mode: 'medium' })
let memoryDraft = emptyDraft()
let memoryOnly = false

export function readAnalysisDraft(): AnalysisDraft {
  if (memoryOnly) return memoryDraft
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY)
    if (!raw) return memoryDraft
    const value: unknown = JSON.parse(raw)
    if (value && typeof value === 'object' && 'title' in value && typeof value.title === 'string' &&
      'text' in value && typeof value.text === 'string' && 'mode' in value && ['low', 'medium', 'high'].includes(value.mode as string)) {
      memoryDraft = { title: value.title, text: value.text, mode: value.mode as Mode }
    }
  } catch { /* Preserve the latest draft in memory when storage is unavailable. */ }
  return memoryDraft
}

export function saveAnalysisDraft(draft: AnalysisDraft): boolean {
  memoryDraft = draft
  try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft)); memoryOnly = false; return true }
  catch { memoryOnly = true; return false }
}

export function clearAnalysisDraft(): void {
  sessionStorage.removeItem(DRAFT_KEY)
  memoryDraft = emptyDraft(); memoryOnly = false
}
