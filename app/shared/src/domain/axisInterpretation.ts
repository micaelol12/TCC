import { AXES, type Axis } from './axes'

// Labels and score boundaries from rotulo_8values in Pipeline_JEV_2_Polos_LLM.ipynb.
const labels: Record<Axis, readonly string[]> = {
  economic: ['Comunista', 'Socialista', 'Social', 'Centrista', 'Mercado', 'Capitalista', 'Laissez-Faire'],
  diplomatic: ['Cosmopolita', 'Internacionalista', 'Pacífico', 'Equilibrado', 'Patriota', 'Nacionalista', 'Chauvinista'],
  state: ['Anarquista', 'Libertário', 'Liberal', 'Moderado', 'Estatal', 'Autoritário', 'Totalitário'],
  society: ['Revolucionário', 'Muito Progressista', 'Progressista', 'Neutro', 'Tradicional', 'Muito Tradicional', 'Reacionário'],
}

export function interpretAxisScore(axis: Axis, score: number | null): { label: string; description: string } | null {
  if (score === null || !Number.isFinite(score) || score < 0 || score > 100) return null
  const index = score > 90 ? 0 : score > 75 ? 1 : score > 60 ? 2 : score >= 40 ? 3 : score >= 25 ? 4 : score >= 10 ? 5 : 6
  const item = AXES[axis]
  return {
    label: labels[axis][index],
    description: index === 3
      ? `Resultado na faixa central entre ${item.a} e ${item.b}. ${item.explanation}`
      : index < 3 ? item.aDescription : item.bDescription,
  }
}
