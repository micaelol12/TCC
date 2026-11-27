import { useEffect, useRef, useState } from 'react'
import type { Analysis, Mode } from '../../services/analysisApi'
import { readAnalysisDraft, saveAnalysisDraft, type AnalysisDraft } from './analysisDraft'
import { readAnalysisHistory, saveAnalysisHistory, type Entry } from './analysisHistory'

export function useAnalysisSession() {
  const [draft, setDraft] = useState(readAnalysisDraft)
  const [entries, setEntries] = useState(readAnalysisHistory)
  const [draftStored, setDraftStored] = useState(true)
  const [historyStored, setHistoryStored] = useState(true)
  const lastEntryId = useRef(Math.max(0, ...entries.map(entry => entry.id)))

  useEffect(() => { setDraftStored(saveAnalysisDraft(draft)) }, [draft])
  useEffect(() => { setHistoryStored(saveAnalysisHistory(entries)) }, [entries])
  useEffect(() => {
    if (draftStored || !(draft.text || draft.title)) return
    function warnAboutUnsavedDraft(event: BeforeUnloadEvent) {
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', warnAboutUnsavedDraft)
    return () => window.removeEventListener('beforeunload', warnAboutUnsavedDraft)
  }, [draftStored, draft.text, draft.title])

  function updateDraft(change: Partial<AnalysisDraft>) {
    setDraft(current => ({ ...current, ...change }))
  }

  function appendAnalysis(text: string, title: string, mode: Mode, analysis: Analysis): Entry {
    const id = ++lastEntryId.current
    const entry: Entry = { id, title: title.trim() || `Análise ${id}`, text, mode, analysis }
    setEntries(current => [...current, entry])
    return entry
  }

  return { draft, updateDraft, draftStored, entries, historyStored, appendAnalysis }
}
