import { describe, expect, it } from 'vitest'
import type { PlanFormValues } from './plan-request'
import { departureInputLimits, validatePlanForm } from './validate'

const NOW = new Date('2026-10-24T08:20:00Z')

const VALID: PlanFormValues = {
  origin: 'Chicago, IL',
  destination: 'Denver, CO',
  departure: '2026-10-24T09:00',
  loadLb: '42000',
  intervalMi: 25,
}

function errorsFor(changes: Partial<PlanFormValues>) {
  return validatePlanForm({ ...VALID, ...changes }, NOW)
}

describe('validatePlanForm', () => {
  it('accepts valid values', () => {
    expect(errorsFor({})).toEqual({})
  })

  it('requires both places', () => {
    const errors = errorsFor({ origin: ' ', destination: '' })
    expect(errors.origin).toEqual(['Enter a starting place.'])
    expect(errors.destination).toEqual(['Enter a destination.'])
  })

  it('rejects the same place twice', () => {
    expect(errorsFor({ destination: ' chicago, il ' }).destination).toEqual([
      'Destination must be different from origin.',
    ])
  })

  it('checks the departure window', () => {
    expect(errorsFor({ departure: '' }).departure).toEqual(['Pick a departure time.'])
    expect(errorsFor({ departure: '2026-10-24T07:00' }).departure).toEqual([
      "Departure can't be in the past.",
    ])
    expect(errorsFor({ departure: '2026-10-24T08:16' }).departure).toBeUndefined()
    expect(errorsFor({ departure: '2026-11-01T09:00' }).departure).toEqual([
      'Departure must be within the next 7 days.',
    ])
  })

  it('checks the load', () => {
    expect(errorsFor({ loadLb: '' }).load_lb).toEqual(['Enter the load in pounds.'])
    expect(errorsFor({ loadLb: '12.5' }).load_lb).toEqual(['Enter the load in pounds.'])
    expect(errorsFor({ loadLb: '45001' }).load_lb).toEqual([
      'Load must be between 0 and 45,000 lb.',
    ])
    expect(errorsFor({ loadLb: '45,000' }).load_lb).toBeUndefined()
    expect(errorsFor({ loadLb: '0' }).load_lb).toBeUndefined()
  })
})

describe('departureInputLimits', () => {
  it('goes from now to 7 days ahead', () => {
    expect(departureInputLimits(NOW)).toEqual({
      min: '2026-10-24T08:20',
      max: '2026-10-31T08:20',
    })
  })
})
