import ConfirmAction from './ConfirmAction'

type AnalysisResultActionsProps = {
  replacesDraft: boolean
  onReuseAnalysis: () => void
  onCompareProfile: () => void
  onCompareAnalyses: () => void
}

/** Reúne as ações de reutilizar e comparar um resultado, confirmando a substituição de rascunho. */
export default function AnalysisResultActions({ replacesDraft, onReuseAnalysis, onCompareProfile, onCompareAnalyses }: AnalysisResultActionsProps) {
  return <div className="actions">
    {replacesDraft ? <ConfirmAction label="Editar e reanalisar" className="secondary" title="Substituir o rascunho atual?"
      description="O rascunho ainda não enviado será substituído pelo texto desta análise. Cancele para manter seu rascunho."
      confirmLabel="Sim, substituir rascunho" onConfirm={onReuseAnalysis} />
      : <button className="secondary" onClick={onReuseAnalysis}>Editar e reanalisar</button>}
    <button className="secondary" onClick={onCompareProfile}>Comparar comigo</button>
    <button className="secondary" onClick={onCompareAnalyses}>Comparar análises</button>
  </div>
}
