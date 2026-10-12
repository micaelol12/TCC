import { describe, expect, it } from 'vitest'
import { closestIdeology } from './closestIdeology'

describe('closest ideology from the TCC reference profiles', () => {
  it('matches profiles with the notebook distance formula', () => {
    expect(closestIdeology({ economic: 50, diplomatic: 50, state: 50, society: 50 })).toBe('Centrista')
    expect(closestIdeology({ economic: 100, diplomatic: 50, state: 100, society: 90 })).toBe('Anarco-Comunismo')
  })

  it('does not classify incomplete or invalid scores', () => {
    expect(closestIdeology({ economic: 50, diplomatic: NaN, state: 50, society: 50 })).toBeNull()
  })
})
