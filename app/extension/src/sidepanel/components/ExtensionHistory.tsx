import { modeLabels } from '@8values/shared/api'
import ConfirmAction from '@8values/shared/components/ConfirmAction'
import type { Session } from '../../storage/sessionState'
import HelperText from '@8values/shared/components/HelperText'
import Button from '@8values/shared/components/Button'

type ExtensionHistoryProps = {
  session: Pick<Session, 'entries' | 'selectedId' | 'showComposer'>
  ready: boolean
  busy: boolean
  onSelect: (id: string) => void
  onClear: () => Promise<void>
}

/** Lista resultados da janela e oferece a limpeza confirmada da sessão. */
export default function ExtensionHistory({ session, ready, busy, onSelect, onClear }: ExtensionHistoryProps) {
  return <details className="sessionHistory"><summary>Histórico desta sessão ({session.entries.length})</summary>{session.entries.length ? <ul>{session.entries.map(entry => <li key={entry.id}><Button variant="secondary" className="historyEntry" aria-pressed={entry.id === session.selectedId && !session.showComposer} disabled={busy} onClick={() => onSelect(entry.id)}>{entry.title}<span>{modeLabels[entry.mode]}</span></Button></li>)}</ul> : <HelperText>Nenhuma análise nesta sessão.</HelperText>}
          <HelperText>Até 10 análises, com limite de espaço. Os dados temporários são removidos ao reiniciar o navegador ou recarregar a extensão.</HelperText>
          <HelperText>Limpar este histórico não apaga relatos já enviados e armazenados no servidor.</HelperText>
          <ConfirmAction label="Limpar histórico e rascunhos" title="Apagar o histórico desta janela?" description="Todas as análises, o rascunho e as seleções pendentes desta janela serão apagados. Seu perfil e os relatos já enviados serão mantidos. Esta ação não pode ser desfeita."
            confirmLabel="Sim, limpar histórico e rascunhos" disabled={!ready || busy} onConfirm={onClear} />
        </details>
}
