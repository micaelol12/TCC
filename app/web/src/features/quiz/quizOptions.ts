import type { Answer } from '../../domain/quizScoring'

export const quizOptions: { value: Answer; label: string }[] = [
  { value: 1, label: 'Concordo fortemente' }, { value: .5, label: 'Concordo' },
  { value: 0, label: 'Neutro ou incerto' }, { value: -.5, label: 'Discordo' },
  { value: -1, label: 'Discordo fortemente' },
]
