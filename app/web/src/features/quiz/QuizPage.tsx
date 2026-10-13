import { useEffect, useReducer, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { QUESTIONS, scoreAnswers } from '../../domain/quizScoring'
import type { Answer, Answers } from '../../domain/quizScoring'
import type { Profile } from '../../storage/localProfile'
import { DRAFT_KEY, removeLocalData, saveProfile } from '../../storage/localProfile'
import { QUESTION_HASH } from '../../domain/quizScoring'
import styles from '@8values/shared/styles/Cards.module.css'
import AxisGuide from './AxisGuide'

type QuizState = { index: number; answers: Answers; review: boolean }
type Action = { type: 'answer'; id: number; value: Answer } | { type: 'index'; index: number } | { type: 'review' } | { type: 'reset' }
const initial: QuizState = { index: 0, answers: {}, review: false }
function reducer(state: QuizState, action: Action): QuizState {
  if (action.type === 'answer') return { ...state, answers: { ...state.answers, [action.id]: action.value } }
  if (action.type === 'index') return { ...state, index: action.index, review: false }
  if (action.type === 'review') return { ...state, review: true }
  return initial
}
function loadDraft(): QuizState {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY)
    if (!raw) return initial
    const value = JSON.parse(raw)
    if (value.question_hash !== QUESTION_HASH || !Number.isInteger(value.index) || value.index < 0 || value.index >= QUESTIONS.length || typeof value.answers !== 'object') return initial
    const answers: Answers = {}
    for (const q of QUESTIONS) if ([-1, -.5, 0, .5, 1].includes(value.answers[q.id])) answers[q.id] = value.answers[q.id]
    return { index: value.index, answers, review: false }
  } catch { return initial }
}
const options: { value: Answer; label: string }[] = [
  { value: 1, label: 'Concordo fortemente' }, { value: .5, label: 'Concordo' },
  { value: 0, label: 'Neutro ou incerto' }, { value: -.5, label: 'Discordo' },
  { value: -1, label: 'Discordo fortemente' },
]

export default function QuizPage({ onComplete }: { onComplete: (profile: Profile, stored: boolean) => void }) {
  const [state, dispatch] = useReducer(reducer, undefined, loadDraft)
  const [storageWarning, setStorageWarning] = useState(false)
  const [keep, setKeep] = useState(true)
  const navigate = useNavigate()
  const headingRef = useRef<HTMLHeadingElement>(null)
  const initialQuestion = useRef(true)
  const question = QUESTIONS[state.index]
  const answered = QUESTIONS.filter(q => Object.hasOwn(state.answers, q.id)).length
  useEffect(() => {
    try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ question_hash: QUESTION_HASH, index: state.index, answers: state.answers })) }
    catch { setStorageWarning(true) }
  }, [state.index, state.answers])
  useEffect(() => {
    if (initialQuestion.current) { initialQuestion.current = false; return }
    headingRef.current?.focus()
  }, [state.index, state.review])
  function finish() {
    if (answered !== QUESTIONS.length) { dispatch({ type: 'review' }); return }
    const profile: Profile = { schema_version: 1, question_hash: QUESTION_HASH, completed_at: new Date().toISOString(), scores: scoreAnswers(state.answers) }
    const stored = keep && saveProfile(profile)
    if (!stored) removeLocalData()
    try { sessionStorage.removeItem(DRAFT_KEY) } catch { /* unavailable */ }
    onComplete(profile, stored)
    navigate('/resultado')
  }
  function discard() {
    try { sessionStorage.removeItem(DRAFT_KEY) } catch { /* unavailable */ }
    dispatch({ type: 'reset' }); navigate('/')
  }
  return <main className="narrow flow quizPage">
    <div className="eyebrow">Questionário 8values</div>
    <h1>Conheça seus valores</h1>
    <div className="quizIntro"><p className="muted">Uma pergunta de cada vez. Você pode voltar e alterar respostas.</p><AxisGuide /></div>
    {storageWarning && <p className="notice" role="status">O navegador bloqueou o rascunho. Suas respostas continuam nesta página enquanto ela estiver aberta.</p>}
    {state.review ? <section className={styles.card}>
      <h2 ref={headingRef} tabIndex={-1}>Revisar respostas</h2><p>{answered} de {QUESTIONS.length} respondidas.</p>
      <div className="reviewGrid">{QUESTIONS.map((q, index) => <button key={q.id} className={Object.hasOwn(state.answers, q.id) ? 'subtle' : 'pending'} onClick={() => dispatch({ type: 'index', index })} aria-label={`Ir à pergunta ${q.id}${Object.hasOwn(state.answers, q.id) ? '' : ', pendente'}`}>{q.id}</button>)}</div>
      <label className="check"><input type="checkbox" checked={keep} onChange={e => setKeep(e.target.checked)} /> Guardar o resultado neste navegador após concluir</label>
      <div className="actions"><button onClick={finish} disabled={answered !== QUESTIONS.length}>Concluir teste</button><button className="secondary" onClick={discard}>Descartar teste</button></div>
    </section> : <section className={styles.card}>
      <div className="progressText">Pergunta {state.index + 1} de {QUESTIONS.length} · {answered} respondidas</div>
      <progress value={answered} max={QUESTIONS.length} aria-label="Perguntas respondidas" />
      <h2 id="question-title" ref={headingRef} tabIndex={-1}>{question.question}</h2>
      <fieldset aria-labelledby="question-title"><legend className="srOnly">Selecione sua resposta</legend>
        {options.map(option => <label key={option.value} className={styles.option}><input type="radio" name={`question-${question.id}`} checked={state.answers[question.id] === option.value} onChange={() => dispatch({ type: 'answer', id: question.id, value: option.value })} />{option.label}</label>)}
      </fieldset>
      <div className="actions"><button className="secondary" disabled={state.index === 0} onClick={() => dispatch({ type: 'index', index: state.index - 1 })}>Voltar</button><button disabled={!Object.hasOwn(state.answers, question.id)} onClick={() => state.index === QUESTIONS.length - 1 ? dispatch({ type: 'review' }) : dispatch({ type: 'index', index: state.index + 1 })}>{state.index === QUESTIONS.length - 1 ? 'Revisar' : 'Próxima'}</button><button className="textButton" onClick={discard}>Descartar teste</button></div>
    </section>}
  </main>
}
