import { useEffect, useReducer, useState } from 'react'
import { QUESTIONS } from '../../domain/quizScoring'
import { readQuizDraft, reduceQuizSession, saveQuizDraft } from './quizSession'

export function useQuizSession() {
  const [state, dispatch] = useReducer(reduceQuizSession, undefined, readQuizDraft)
  const [storageWarning, setStorageWarning] = useState(false)
  const answeredCount = QUESTIONS.filter(question => Object.hasOwn(state.answers, question.id)).length

  useEffect(() => {
    setStorageWarning(!saveQuizDraft(state))
  }, [state])

  return { state, dispatch, answeredCount, storageWarning }
}
