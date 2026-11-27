import type { Capabilities, Mode } from './analysisContracts'

export const modes: Mode[] = ['low', 'medium', 'high']
export const modeLabels: Record<Mode, string> = { low: 'Classificação direta', medium: 'Classificação com revisão', high: 'Modelo de linguagem' }
export const modeDescriptions: Record<Mode, string> = {
  low: 'Um classificador identifica as posições políticas de cada trecho.',
  medium: 'O classificador faz a primeira avaliação; um modelo de linguagem revisa os trechos quando necessário.',
  high: 'Um modelo de linguagem avalia diretamente as posições políticas de cada trecho.',
}
export const recipients: Record<Mode, string> = { low: 'TypeSafe (JEV)', medium: 'TypeSafe (JEV) e, quando necessário, Maritaca (Sabiá)', high: 'Maritaca (Sabiá)' }
/** Descreve os provedores que podem receber o texto conforme o modo e os padrões da API. */
export function configuredRecipients(mode: Mode, capabilities: Capabilities | null): string {
  const config = capabilities?.analysis_defaults
  if (!config) return recipients[mode]
  const llmRecipient = capabilities?.model_providers?.[config.llm_model] === 'gemini' ? 'Google Gemini' : 'Maritaca (Sabiá)'
  if (mode === 'low') return recipients.low
  if (mode === 'medium') return `TypeSafe (JEV) e, quando necessário, ${llmRecipient}`
  return config.semantic_evidence_check ? `${llmRecipient} e TypeSafe (checagem de evidências)` : llmRecipient
}
