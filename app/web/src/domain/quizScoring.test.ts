import { describe, expect, it } from 'vitest'
import { maximums, QUESTIONS, scoreAnswers } from './quizScoring'
import type { Answers } from './quizScoring'

describe('quiz scoring', () => {
  it('uses all 70 questions and verified maximums', () => {
    expect(QUESTIONS).toHaveLength(70)
    expect(maximums).toEqual({ economic: 195, diplomatic: 225, state: 320, society: 292 })
  })
  it('scores neutral at 50 and complementary poles at 100', () => {
    const answers = Object.fromEntries(QUESTIONS.map(q => [q.id, 0])) as Answers
    const scores = scoreAnswers(answers)
    for (const value of Object.values(scores)) expect(value).toBe(50)
    answers[1] = 1
    expect(scoreAnswers(answers).economic).toBeGreaterThan(50)
    answers[1] = -1
    expect(scoreAnswers(answers).economic).toBeLessThan(50)
  })
  it('does not treat missing answers as neutral', () => {
    expect(() => scoreAnswers({})).toThrow()
  })
})
