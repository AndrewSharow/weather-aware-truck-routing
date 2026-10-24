import { describe, expect, it } from 'vitest'
import {
  RISK_COLORS,
  RISK_LABELS,
  RISK_LEVELS,
  levelFromScore,
  riskSegments,
} from './risk'

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

describe('riskSegments', () => {
  it('keeps levels with miles, in order, with their share', () => {
    const segments = riskSegments({
      low: 75,
      moderate: 0,
      high: 0,
      severe: 20,
      no_travel: 0,
      unknown: 5,
    })
    expect(segments).toEqual([
      { level: 'low', miles: 75, percent: 75 },
      { level: 'severe', miles: 20, percent: 20 },
      { level: 'unknown', miles: 5, percent: 5 },
    ])
  })

  it('returns nothing for a route without miles', () => {
    const empty = { low: 0, moderate: 0, high: 0, severe: 0, no_travel: 0, unknown: 0 }
    expect(riskSegments(empty)).toEqual([])
  })
})
