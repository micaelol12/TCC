export const CONNECTION_ERROR = 'Não foi possível conectar ao serviço de análise. Confira sua conexão e use “Verificar conexão e modos” para tentar novamente. O questionário continua disponível.'

const reasonMessages: Record<string, string> = {
  falha_jev: 'O serviço de classificação não respondeu. Tente analisar novamente mais tarde.',
  falha_llm: 'O serviço de análise de linguagem não respondeu. Tente novamente mais tarde.',
  falha_autenticacao_jev: 'O serviço de classificação está com um problema de acesso. Tente outro modo disponível ou avise a equipe responsável.',
  falha_autenticacao_llm: 'O serviço de análise de linguagem está com um problema de acesso. Tente outro modo disponível ou avise a equipe responsável.',
  resposta_jev_invalida: 'O classificador retornou dados que não puderam ser interpretados. Confira os eixos disponíveis ou tente novamente.',
  evidencia_nao_verificada: 'Uma citação não pôde ser confirmada no texto. A estimativa correspondente foi descartada.',
  evidencia_limitada: 'Poucos trechos válidos foram usados neste eixo. Interprete a estimativa com cautela.',
  relevancia_ambigua: 'Há incerteza sobre a relevância de um ou mais trechos para este eixo.',
  empate_nivel: 'Dois ou mais níveis de classificação receberam o mesmo suporte.',
  baixa_confianca_nivel: 'O suporte ao nível selecionado ficou abaixo do mínimo configurado.',
  direcao_ambigua: 'Há incerteza sobre qual polo é predominante em um ou mais trechos.',
  intensidade_ambigua: 'Há incerteza sobre a intensidade da posição em um ou mais trechos.',
}

export function describeAnalysisReason(reason: string): string {
  return Object.hasOwn(reasonMessages, reason) ? reasonMessages[reason] : 'O serviço registrou uma limitação adicional. Confira as evidências e interprete o resultado com cautela.'
}
