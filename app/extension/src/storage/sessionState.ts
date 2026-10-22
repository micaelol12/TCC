import { isAnalysis, modes, type Analysis, type AnalysisEntry, type Mode } from '@8values/shared/api'
import { isCapture, type Capture } from '../platform/selection'

export type Entry = AnalysisEntry<string>
export type Draft = { text: string; title: string; source?: string }
export type Request = Draft & { id: string; owner: string; mode: Mode; startedAt: number }
export type Session = {
  version: 1; draft: Draft; mode: Mode; entries: Entry[]; selectedId: string | null;
  showComposer: boolean; pending: Capture | null; seenCapture: string | null; seenAt: number;
  request: Request | null; notice: string
}
export function emptySession(mode: Mode = 'medium'): Session {
  return { version: 1, draft: { text: '', title: '' }, mode, entries: [], selectedId: null, showComposer: true, pending: null, seenCapture: null, seenAt: 0, request: null, notice: '' }
}
function isDraft(value: unknown): value is Draft {
  if (!value || typeof value !== 'object') return false
  const draft = value as Draft
  return typeof draft.text === 'string' && typeof draft.title === 'string' && (draft.source === undefined || typeof draft.source === 'string')
}
export function hydrateSession(raw: unknown, mode: Mode = 'medium'): Session {
  const fresh = emptySession(mode)
  if (!raw || typeof raw !== 'object') return fresh
  const saved = raw as Partial<Session>
  if (saved.version !== 1) return fresh
  if (isDraft(saved.draft)) fresh.draft = saved.draft
  if (modes.includes(saved.mode as Mode)) fresh.mode = saved.mode!
  if (Array.isArray(saved.entries)) fresh.entries = saved.entries.filter(entry => entry && typeof entry === 'object' && typeof entry.id === 'string' && typeof entry.title === 'string' && typeof entry.text === 'string' &&
    (entry.source === undefined || typeof entry.source === 'string') && modes.includes(entry.mode) && isAnalysis(entry.analysis) && entry.mode === entry.analysis.processing_level).slice(-10)
  fresh.selectedId = fresh.entries.some(entry => entry.id === saved.selectedId) ? saved.selectedId! : fresh.entries.at(-1)?.id ?? null
  fresh.showComposer = typeof saved.showComposer === 'boolean' ? saved.showComposer || !fresh.selectedId : !fresh.selectedId
  fresh.pending = isCapture(saved.pending) ? saved.pending : null
  fresh.seenCapture = typeof saved.seenCapture === 'string' ? saved.seenCapture : null
  fresh.seenAt = typeof saved.seenAt === 'number' && Number.isFinite(saved.seenAt) ? saved.seenAt : 0
  if (isDraft(saved.request)) {
    // There is no HTTP task to resume in a newly loaded document.
    fresh.draft = { text: saved.request.text, title: saved.request.title, source: saved.request.source }
    fresh.showComposer = true
    fresh.notice = 'Análise interrompida ao fechar ou recarregar o painel. O texto foi preservado; envie novamente se desejar.'
  }
  return fresh
}
export type Action =
  | { type: 'capture'; capture: Capture }
  | { type: 'use-pending' } | { type: 'ignore-pending' }
  | { type: 'edit'; draft: Partial<Draft> } | { type: 'mode'; mode: Mode }
  | { type: 'begin'; request: Request }
  | { type: 'success'; id: string; analysis: Analysis }
  | { type: 'failure'; id: string; message: string }
  | { type: 'select'; id: string } | { type: 'compose' } | { type: 'close-composer' }
  | { type: 'reuse'; entry: Entry } | { type: 'clear' }
export function reduceSession(state: Session, action: Action): Session {
  switch (action.type) {
    case 'capture': {
      if (state.seenCapture === action.capture.id || action.capture.createdAt <= state.seenAt) return state
      const next = { ...state, seenCapture: action.capture.id, seenAt: action.capture.createdAt }
      if (state.request || state.draft.text.trim()) return { ...next, pending: action.capture }
      return { ...next, draft: { text: action.capture.text, title: '', source: action.capture.source }, pending: null, showComposer: true, notice: '' }
    }
    case 'use-pending': return state.request || !state.pending ? state : { ...state, draft: { text: state.pending.text, title: '', source: state.pending.source }, pending: null, showComposer: true, notice: '' }
    case 'ignore-pending': return { ...state, pending: null }
    case 'edit': return state.request ? state : { ...state, draft: { ...state.draft, ...action.draft }, notice: '' }
    case 'mode': return state.request ? state : { ...state, mode: action.mode }
    case 'begin': return state.request ? state : { ...state, request: action.request, notice: '' }
    case 'success': {
      if (state.request?.id !== action.id) return state
      const entry: Entry = { id: action.id, text: state.request.text, title: state.request.title.trim() || `Análise ${state.entries.length + 1}`, source: state.request.source, mode: state.request.mode, analysis: action.analysis }
      return { ...state, entries: [...state.entries, entry].slice(-10), selectedId: entry.id, draft: { text: '', title: '' }, request: null, showComposer: false, notice: '' }
    }
    case 'failure': return state.request?.id !== action.id ? state : { ...state, request: null, notice: action.message, showComposer: true }
    case 'select': return state.request || !state.entries.some(entry => entry.id === action.id) ? state : { ...state, selectedId: action.id, showComposer: false }
    case 'compose': return { ...state, showComposer: true }
    case 'close-composer': return state.request ? state : { ...state, showComposer: !state.selectedId }
    case 'reuse': return state.request ? state : { ...state, draft: { text: action.entry.text, title: action.entry.title, source: action.entry.source }, mode: action.entry.mode, showComposer: true, notice: '' }
    case 'clear': return state.request ? state : { ...emptySession(state.mode), seenCapture: state.seenCapture, seenAt: state.seenAt }
  }
}
export const MAX_SESSION_BYTES = 700_000
export function fitSession(state: Session): { state: Session; trimmed: boolean } {
  const size = (value: Session) => new TextEncoder().encode(JSON.stringify(value)).length
  const result = { ...state, entries: state.entries.slice(-10) }
  let trimmed = result.entries.length !== state.entries.length
  while (size(result) > MAX_SESSION_BYTES && result.entries.length) { result.entries = result.entries.slice(1); trimmed = true }
  if (size(result) > MAX_SESSION_BYTES) throw new Error('Rascunho acima do espaço temporário disponível. Reduza o texto para guardá-lo.')
  if (!result.entries.some(entry => entry.id === result.selectedId)) result.selectedId = result.entries.at(-1)?.id ?? null
  if (!result.selectedId) result.showComposer = true
  return { state: result, trimmed }
}
