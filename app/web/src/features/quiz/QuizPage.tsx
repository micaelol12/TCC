import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { QUESTIONS, QUESTION_HASH, scoreAnswers } from '../../domain/quizScoring'
import { removeLocalData, saveProfile, type Profile } from '../../storage/localProfile'
import AxisGuide from './AxisGuide'
import ConfirmAction from '@8values/shared/components/ConfirmAction'
import QuizQuestionCard from './QuizQuestionCard'
import QuizReviewCard from './QuizReviewCard'
import { removeQuizDraft } from './quizSession'
import { useQuizSession } from './useQuizSession'

export default function QuizPage({ onComplete }: { onComplete: (profile: Profile, stored: boolean) => void }) {
  const { state, dispatch, answeredCount, storageWarning } = useQuizSession()
  const [keepResult, setKeepResult] = useState(true)
  const navigate = useNavigate()
  const headingRef = useRef<HTMLHeadingElement>(null)
  const initialQuestion = useRef(true)
  useEffect(() => {
    if (initialQuestion.current) { initialQuestion.current = false; return }
    headingRef.current?.focus()
  }, [state.index, state.review])
  function finishQuiz() {
    if (answeredCount !== QUESTIONS.length) { dispatch({ type: 'review' }); return }
    const profile: Profile = { schema_version: 1, question_hash: QUESTION_HASH, completed_at: new Date().toISOString(), scores: scoreAnswers(state.answers) }
    const stored = keepResult && saveProfile(profile)
    if (!stored) removeLocalData()
    try { removeQuizDraft() } catch { /* unavailable */ }
    onComplete(profile, stored)
    navigate('/resultado')
  }
  function discardQuiz() {
    try { removeQuizDraft() }
    catch { throw new Error('Não foi possível apagar o rascunho salvo. Verifique as permissões de armazenamento do navegador e tente novamente.') }
    dispatch({ type: 'reset' }); navigate('/')
  }
  function nextQuestion() {
    if (state.index === QUESTIONS.length - 1) dispatch({ type: 'review' })
    else dispatch({ type: 'index', index: state.index + 1 })
  }
  const discardButton = <ConfirmAction label="Descartar teste" className="textButton" title="Descartar as respostas do teste?"
    description="As respostas preenchidas neste teste serão apagadas. Seu resultado anterior e as análises de textos serão mantidos. Esta ação não pode ser desfeita."
    confirmLabel="Sim, descartar respostas" onConfirm={discardQuiz} />
  return <main className="narrow flow quizPage">
    <div className="eyebrow">Questionário 8values</div>
    <h1>Conheça seus valores</h1>
    <div className="quizIntro"><p className="muted">Uma pergunta de cada vez. Você pode voltar e alterar respostas.</p><AxisGuide /></div>
    {storageWarning && <p className="notice" role="status">O navegador bloqueou o rascunho. Suas respostas continuam nesta página enquanto ela estiver aberta.</p>}
    {state.review ? <QuizReviewCard answers={state.answers} answeredCount={answeredCount} headingRef={headingRef}
      keepResult={keepResult} onKeepResult={setKeepResult} onFinish={finishQuiz}
      onEditQuestion={index => dispatch({ type: 'index', index })} discardButton={discardButton} />
      : <QuizQuestionCard state={state} answeredCount={answeredCount} headingRef={headingRef}
        onAnswer={(id, value) => dispatch({ type: 'answer', id, value })}
        onNavigate={index => dispatch({ type: 'index', index })}
        onReview={() => dispatch({ type: 'review' })} onNextQuestion={nextQuestion} discardButton={discardButton} />}

  </main>
}
