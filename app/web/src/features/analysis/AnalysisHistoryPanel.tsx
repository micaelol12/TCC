import { modeLabels } from '../../services/analysisApi'
import type { Entry } from './analysisHistory'
import HelperText from '@8values/shared/components/HelperText'
import Button from '@8values/shared/components/Button'

type AnalysisHistoryPanelProps = {
  entries: Entry[]
  selectedId: number | null
  showComposer: boolean
  busy: boolean
  onNewAnalysis: () => void
  onSelectEntry: (id: number) => void
}

/** Lista análises da sessão e permite abrir um resultado ou iniciar uma nova composição. */
export default function AnalysisHistoryPanel({ entries, selectedId, showComposer, busy, onNewAnalysis, onSelectEntry }: AnalysisHistoryPanelProps) {
  return <aside className="history" aria-label="Histórico desta sessão">
    {entries.length > 0 && <Button className="newAnalysisButton" disabled={busy} onClick={onNewAnalysis}>+ Nova análise</Button>}
    <h2>Histórico</h2>
    {entries.length === 0 ? <HelperText>Nenhuma análise nesta sessão.</HelperText> : <ul>
      {entries.map(entry => {
        const isSelected = selectedId === entry.id && !showComposer

        return <li key={entry.id}>
          <Button disabled={busy} aria-pressed={isSelected} className={isSelected ? 'historyButton active' : 'historyButton'} onClick={() => onSelectEntry(entry.id)}>
            {entry.title}<span>{modeLabels[entry.mode]}</span>
          </Button>
        </li>
      })}
    </ul>}
  </aside>
}
