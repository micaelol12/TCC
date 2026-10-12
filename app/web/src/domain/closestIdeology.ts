import ideologies from '../data/ideologies.json'
import { axisOrder } from './axes'
import type { Scores } from './quizScoring'

type Ideology = { name: string; stats: { econ: number; dipl: number; govt: number; scty: number } }
const profiles = ideologies as Ideology[]
const diplomaticAndSocialExponent = 1.73856063

/** Matches the distance calculation and first-tie behavior in TCC.ipynb. */
export function closestIdeology(scores: Scores): string | null {
  if (axisOrder.some(axis => !Number.isFinite(scores[axis]) || scores[axis] < 0 || scores[axis] > 100)) return null
  let best: Ideology | null = null
  let shortest = Infinity
  for (const candidate of profiles) {
    const distance = Math.abs(candidate.stats.econ - scores.economic) ** 2 +
      Math.abs(candidate.stats.govt - scores.state) ** 2 +
      Math.abs(candidate.stats.dipl - scores.diplomatic) ** diplomaticAndSocialExponent +
      Math.abs(candidate.stats.scty - scores.society) ** diplomaticAndSocialExponent
    if (distance < shortest) { shortest = distance; best = candidate }
  }
  return best?.name ?? null
}
