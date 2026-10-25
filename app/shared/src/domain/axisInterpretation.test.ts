import { describe, expect, it } from 'vitest'
import { AXES, axisOrder } from './axes'
import { interpretAxisScore } from './axisInterpretation'

describe('axis result interpretation', () => {
  it('maps 75% Nação to Patriota and reuses the existing description', () => {
    expect(interpretAxisScore('diplomatic', 25)).toEqual({
      label: 'Patriota', description: AXES.diplomatic.bDescription,
    })
  })

  it.each([
    [100, 'Cosmopolita'], [90.1, 'Cosmopolita'], [90, 'Internacionalista'],
    [75.1, 'Internacionalista'], [75, 'Pacífico'], [60.1, 'Pacífico'],
    [60, 'Equilibrado'], [50, 'Equilibrado'], [40, 'Equilibrado'],
    [39.9, 'Patriota'], [25, 'Patriota'], [24.9, 'Nacionalista'],
    [10, 'Nacionalista'], [9.9, 'Chauvinista'], [0, 'Chauvinista'],
  ])('keeps notebook boundaries for a Globo score of %s', (score, label) => {
    expect(interpretAxisScore('diplomatic', score)?.label).toBe(label)
  })

  it('uses the correct direction and central label for each axis', () => {
    const expected = {
      economic: ['Comunista', 'Centrista', 'Laissez-Faire'],
      diplomatic: ['Cosmopolita', 'Equilibrado', 'Chauvinista'],
      state: ['Anarquista', 'Moderado', 'Totalitário'],
      society: ['Revolucionário', 'Neutro', 'Reacionário'],
    }
    for (const axis of axisOrder) {
      expect(interpretAxisScore(axis, 100)).toEqual({ label: expected[axis][0], description: AXES[axis].aDescription })
      expect(interpretAxisScore(axis, 50)?.label).toBe(expected[axis][1])
      expect(interpretAxisScore(axis, 50)?.description).toContain(`entre ${AXES[axis].a} e ${AXES[axis].b}`)
      expect(interpretAxisScore(axis, 0)).toEqual({ label: expected[axis][2], description: AXES[axis].bDescription })
    }
  })

  it.each([null, NaN, Infinity, -1, 101])('does not label an absent or invalid score (%s)', score => {
    expect(interpretAxisScore('diplomatic', score)).toBeNull()
  })
})
