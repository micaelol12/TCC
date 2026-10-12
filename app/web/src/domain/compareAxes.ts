import { AXES } from './axes'
import type { Axis } from './axes'
import type { Scores } from './quizScoring'
import type { AxisResult } from '../services/analysisApi'

export function compareAxis(user: Scores, text: AxisResult) {
  if (text.pole_a === null) return null
  const delta = text.pole_a - user[text.axis]
  return {
    delta, distance: Math.abs(delta),
    direction: Math.abs(delta) < 0.05 ? 'na mesma posição neste eixo' : `relativamente mais próximo de ${delta > 0 ? AXES[text.axis as Axis].a : AXES[text.axis as Axis].b}`,
  }
}
