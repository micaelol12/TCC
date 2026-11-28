import ConfirmAction from './ConfirmAction'
import Actions from './Actions'
import Button from './Button'

type AnalysisResultActionsProps = {
  replacesDraft: boolean
  onReuseAnalysis: () => void
  onCompareProfile: () => void
  onCompareAnalyses: () => void
}

/** Reúne as ações de reutilizar e comparar um resultado, confirmando a substituição de rascunho. */
export default function AnalysisResultActions({ replacesDraft, onReuseAnalysis, onCompareProfile, onCompareAnalyses }: AnalysisResultActionsProps) {
  return <Actions>
    {replacesDraft ? <ConfirmAction label="Editar e reanalisar" className="secondary" title="Substituir o rascunho atual?"
      description="O rascunho ainda não enviado será substituído pelo texto desta análise. Cancele para manter seu rascunho."
      confirmLabel="Sim, substituir rascunho" onConfirm={onReuseAnalysis} />
      : <Button variant="secondary" onClick={onReuseAnalysis}>Editar e reanalisar</Button>}
    <Button variant="secondary" onClick={onCompareProfile}>Comparar comigo</Button>
    <Button variant="secondary" onClick={onCompareAnalyses}>Comparar análises</Button>
  </Actions>
}
