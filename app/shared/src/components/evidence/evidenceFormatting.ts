import { AXES, type Axis } from '../../domain/axes'
import type { ScaleLevel } from '../../domain/ordinalScale'

/** Converte a probabilidade em percentual com uma casa decimal no formato brasileiro. */
export const formatProbability = (value: number) => `${(value * 100).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`
/** Exibe o sinal positivo explicitamente para distinguir os códigos dos níveis. */
export const formatLevelCode = (value: number) => `${value > 0 ? '+' : ''}${value}`

/** Combina o rótulo do nível com o nome do polo correspondente ao eixo. */
export function formatLevelName(level: ScaleLevel, axis: Axis) {
  const pole = level.polo === 'A' ? AXES[axis].a : level.polo === 'B' ? AXES[axis].b : 'Sem posição'
  const label = level.rotulo === String(level.codigo) ? pole : level.rotulo.replace(/polo A/gi, AXES[axis].a).replace(/polo B/gi, AXES[axis].b)
  return `${formatLevelCode(level.codigo)} · ${label}`
}
