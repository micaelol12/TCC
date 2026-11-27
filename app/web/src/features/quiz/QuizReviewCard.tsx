import type { ReactNode, Ref } from 'react'
import { QUESTIONS, type Answers } from '../../domain/quizScoring'
import styles from '@8values/shared/styles/Cards.module.css'
import { quizOptions } from './quizOptions'

type QuizReviewCardProps = {
  answers: Answers
  answeredCount: number
  headingRef: Ref<HTMLHeadingElement>
  keepResult: boolean
  onKeepResult: (keep: boolean) => void
  onFinish: () => void
  onEditQuestion: (index: number) => void
  discardButton: ReactNode
}

/** Reúne as respostas para revisão e permite editar perguntas antes de concluir o teste. */
export default function QuizReviewCard({ answers, answeredCount, headingRef, keepResult, onKeepResult, onFinish, onEditQuestion, discardButton }: QuizReviewCardProps) {
  return <section className={styles.card}>
      <h2 ref={headingRef} tabIndex={-1}>Revisar respostas</h2><p>{answeredCount} de {QUESTIONS.length} respondidas.</p>
      <ol className="reviewList">{QUESTIONS.map((question, index) => <li key={question.id}>
        <div><span className="muted small">Pergunta {index + 1}</span><p>{question.question}</p><strong className="small">Sua resposta: {quizOptions.find(option => option.value === answers[question.id])?.label ?? 'Ainda não respondida'}</strong></div>
        <button className="secondary" onClick={() => onEditQuestion(index)} aria-label={`Editar pergunta ${index + 1}`}>Editar</button>
      </li>)}</ol>
      <label className="check"><input type="checkbox" checked={keepResult} onChange={e => onKeepResult(e.target.checked)} /> Guardar o resultado neste navegador após concluir</label>
      <div className="actions"><button onClick={onFinish} disabled={answeredCount !== QUESTIONS.length}>Concluir teste</button>{discardButton}</div>
    </section>
}
