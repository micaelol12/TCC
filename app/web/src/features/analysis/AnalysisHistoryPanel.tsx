import { modeLabels } from '../../services/analysisApi'
import type { Entry } from './analysisHistory'

type AnalysisHistoryPanelProps = {
  entries: Entry[]
  selectedId: number | null
  showComposer: boolean
  busy: boolean
  onNewAnalysis: () => void
  onSelectEntry: (id: number) => void
}

export default function AnalysisHistoryPanel({ entries, selectedId, showComposer, busy, onNewAnalysis, onSelectEntry }: AnalysisHistoryPanelProps) {
  return <aside className="history" aria-label="Histórico desta sessão">
    {entries.length > 0 && <button className="newAnalysisButton" disabled={busy} onClick={onNewAnalysis}>+ Nova análise</button>}
    <h2>Histórico</h2>
    {entries.length === 0 ? <p className="muted small">Nenhuma análise nesta sessão.</p> : <ul>
      {entries.map(entry => {
        const isSelected = selectedId === entry.id && !showComposer
        return <li key={entry.id}>
          <button disabled={busy} aria-pressed={isSelected} className={isSelected ? 'historyButton active' : 'historyButton'} onClick={() => onSelectEntry(entry.id)}>
            {entry.title}<span>{modeLabels[entry.mode]}</span>
          </button>
        </li>
      })}
    </ul>}
  </aside>
}
