import type { ReactNode, Ref } from 'react'
import { QUESTIONS, type Answer } from '../../domain/quizScoring'
import styles from '@8values/shared/styles/Cards.module.css'
import { quizOptions } from './quizOptions'
import type { QuizState } from './quizSession'
import Actions from '@8values/shared/components/Actions'
import Button from '@8values/shared/components/Button'

type QuizQuestionCardProps = {
  state: QuizState
  answeredCount: number
  headingRef: Ref<HTMLHeadingElement>
  onAnswer: (id: number, answer: Answer) => void
  onNavigate: (index: number) => void
  onNextQuestion: () => void
  onReview: () => void
  discardButton: ReactNode
}

/** Exibe a pergunta atual, as alternativas e os controles de navegação do teste. */
export default function QuizQuestionCard({ state, answeredCount, headingRef, onAnswer, onNavigate, onNextQuestion, onReview, discardButton }: QuizQuestionCardProps) {
  const question = QUESTIONS[state.index]

  return <section className={styles.card}>
      <div className="progressText">Pergunta {state.index + 1} de {QUESTIONS.length} · {answeredCount} respondidas</div>
      <progress value={answeredCount} max={QUESTIONS.length} aria-label="Perguntas respondidas" />
      <h2 id="question-title" ref={headingRef} tabIndex={-1}>{question.question}</h2>
      <fieldset aria-labelledby="question-title"><legend className="srOnly">Selecione sua resposta</legend>
        {quizOptions.map(option => <label key={option.value} className={styles.option}><input type="radio" name={`question-${question.id}`} checked={state.answers[question.id] === option.value} onChange={() => onAnswer(question.id, option.value)} />{option.label}</label>)}
      </fieldset>
      <Actions><Button variant="secondary" disabled={state.index === 0} onClick={() => onNavigate(state.index - 1)}>Voltar</Button><Button disabled={!Object.hasOwn(state.answers, question.id)} onClick={onNextQuestion}>{state.index === QUESTIONS.length - 1 ? 'Revisar' : 'Próxima'}</Button>
        {answeredCount > 0 && <Button variant="secondary" onClick={onReview}>{state.reviewVisited ? 'Voltar à revisão' : 'Revisar respostas'}</Button>}{discardButton}</Actions>
    </section>
}
