import { describe, expect, it } from 'vitest'
import { RISK_COLORS, RISK_LABELS, RISK_LEVELS, levelFromScore } from './risk'

describe('risk levels', () => {
  it('lists levels from safest to worst, then unknown', () => {
    expect(RISK_LEVELS).toEqual([
      'low',
      'moderate',
      'high',
      'severe',
      'no_travel',
      'unknown',
    ])
  })

  it('has a color and a label for every level', () => {
    for (const level of RISK_LEVELS) {
      expect(RISK_COLORS[level]).toMatch(/^#[0-9a-f]{6}$/)
      expect(RISK_LABELS[level]).toBeTruthy()
    }
    expect(RISK_LABELS.no_travel).toBe('No Travel')
  })

  it('maps heatmap scores to levels', () => {
    expect(levelFromScore(0)).toBe('low')
    expect(levelFromScore(2)).toBe('high')
    expect(levelFromScore(4)).toBe('no_travel')
    expect(levelFromScore(null)).toBe('unknown')
  })
})
