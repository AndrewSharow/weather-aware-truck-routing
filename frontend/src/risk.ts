import type { RiskLevel } from './types'

export const RISK_LEVELS: RiskLevel[] = [
  'low',
  'moderate',
  'high',
  'severe',
  'no_travel',
  'unknown',
]

export const RISK_COLORS: Record<RiskLevel, string> = {
  low: '#22c55e',
  moderate: '#eab308',
  high: '#f97316',
  severe: '#ef4444',
  no_travel: '#6b21a8',
  unknown: '#9ca3af',
}

export const RISK_LABELS: Record<RiskLevel, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  severe: 'Severe',
  no_travel: 'No Travel',
  unknown: 'Unknown',
}

export function levelFromScore(score: number | null): RiskLevel {
  return score === null ? 'unknown' : RISK_LEVELS[score]
}

export interface RiskSegment {
  level: RiskLevel
  miles: number
  percent: number
}

export function riskSegments(milesByLevel: Record<RiskLevel, number>): RiskSegment[] {
  const total = RISK_LEVELS.reduce((sum, level) => sum + milesByLevel[level], 0)
  if (!total) return []
  return RISK_LEVELS.filter((level) => milesByLevel[level] > 0).map((level) => ({
    level,
    miles: milesByLevel[level],
    percent: (milesByLevel[level] / total) * 100,
  }))
}
