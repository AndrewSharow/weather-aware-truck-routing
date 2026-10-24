import { describe, expect, it } from 'vitest'
import {
  defaultDepartureInput,
  formatDuration,
  formatMiles,
  formatTime,
  formatValue,
  hourLabel,
  localInputToUtcIso,
} from './format'

describe('formatMiles', () => {
  it('rounds and adds thousands separator', () => {
    expect(formatMiles(1004.7)).toBe('1,005 mi')
    expect(formatMiles(24.96)).toBe('25 mi')
    expect(formatMiles(0)).toBe('0 mi')
  })
})

describe('formatDuration', () => {
  it('shows hours and minutes', () => {
    expect(formatDuration(55_200)).toBe('15 h 20 min')
    expect(formatDuration(3_600)).toBe('1 h 0 min')
    expect(formatDuration(1_500)).toBe('25 min')
  })
})

describe('formatTime', () => {
  it('shows weekday, time and zone in the given time zone', () => {
    const text = formatTime('2026-10-24T13:30:00+00:00', 'America/Chicago')
    expect(text).toBe('Sat 8:30 AM CDT')
  })
})

describe('hourLabel', () => {
  it('adds hours to the start time', () => {
    const text = hourLabel('2026-10-24T13:00:00+00:00', 5, 'America/Chicago')
    expect(text).toBe('Sat 1:00 PM CDT')
  })
})

describe('local departure input', () => {
  it('converts local input to UTC ISO', () => {
    expect(localInputToUtcIso('2026-10-24T08:00')).toBe('2026-10-24T08:00:00.000Z')
  })

  it('defaults to the next full hour', () => {
    const now = new Date('2026-10-24T08:20:00Z')
    expect(defaultDepartureInput(now)).toBe('2026-10-24T09:00')
  })

  it('rolls over midnight', () => {
    const now = new Date('2026-10-24T23:40:00Z')
    expect(defaultDepartureInput(now)).toBe('2026-10-25T00:00')
  })
})

describe('formatValue', () => {
  it('rounds with unit and shows missing data', () => {
    expect(formatValue(12.345, 'mph', 0)).toBe('12 mph')
    expect(formatValue(0.1234, 'in/hr', 2)).toBe('0.12 in/hr')
    expect(formatValue(null, 'mph', 0)).toBe('no data')
  })
})
