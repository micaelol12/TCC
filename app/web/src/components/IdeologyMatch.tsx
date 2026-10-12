import { closestIdeology } from '../domain/closestIdeology'
import type { Scores } from '../domain/quizScoring'

export default function IdeologyMatch({ scores, source }: { scores: Scores; source: 'test' | 'analysis' }) {
  const match = closestIdeology(scores)
  if (!match) return null
  const Heading = source === 'analysis' ? 'h3' : 'h2'
  return <section className="ideologyMatch" aria-labelledby={`ideology-${source}`}>
    <div className="eyebrow">Correspondência exploratória</div>
    <Heading id={`ideology-${source}`}>Ideologia mais próxima</Heading>
    <p className="ideologyName">{match}</p>
    <p className="muted small">{source === 'analysis' ? 'Calculada a partir dos quatro eixos estimados pela IA. ' : ''}O próprio 8values informa que essa correspondência é menos precisa que os valores dos eixos. {source === 'analysis' ? 'Não define a posição política do texto ou de seu autor.' : 'Não define sua posição política.'}</p>
  </section>
}
