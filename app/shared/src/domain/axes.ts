export const AXES = {
  economic: { title: 'Econômico', a: 'Igualdade', b: 'Mercado', explanation: 'Distribuição de recursos e papel do mercado.', aDescription: 'Prioriza uma distribuição mais igualitária dos recursos, programas sociais e tributação progressiva.', bDescription: 'Prioriza o crescimento econômico, com menor intervenção estatal, impostos mais baixos e privatizações.' },
  diplomatic: { title: 'Diplomático', a: 'Globo', b: 'Nação', explanation: 'Cooperação internacional e interesses nacionais.', aDescription: 'Valoriza diplomacia, cooperação e integração entre países.', bDescription: 'Valoriza soberania nacional, força militar e uma política externa mais assertiva.' },
  state: { title: 'Civil', a: 'Liberdade', b: 'Autoridade', explanation: 'Liberdades individuais e poder do Estado.', aDescription: 'Defende liberdades civis e menor intervenção do Estado na vida pessoal; não se refere à liberdade econômica.', bDescription: 'Defende maior poder do Estado e mais intervenção na vida pessoal, podendo incluir vigilância.' },
  society: { title: 'Social', a: 'Progresso', b: 'Tradição', explanation: 'Mudança social e preservação de costumes.', aDescription: 'Valoriza mudança social, razão, ciência e pesquisa tecnológica.', bDescription: 'Valoriza costumes tradicionais, códigos morais e a preservação de práticas estabelecidas.' },
} as const

export type Axis = keyof typeof AXES
export const axisOrder = Object.keys(AXES) as Axis[]
export const formatScore = (value: number) => value.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
