import { describe, expect, it } from 'vitest'
import { buildPlanRequest, type PlanFormValues } from './plan-request'

const VALUES: PlanFormValues = {
  origin: '  Chicago, IL ',
  destination: 'Denver, CO',
  departure: '2026-10-24T08:00',
  loadLb: '42000',
  intervalMi: 25,
}

describe('buildPlanRequest', () => {
  it('trims places, converts departure to UTC and load to a number', () => {
    expect(buildPlanRequest(VALUES)).toEqual({
      origin: 'Chicago, IL',
      destination: 'Denver, CO',
      departure: '2026-10-24T08:00:00.000Z',
      load_lb: 42_000,
      interval_mi: 25,
    })
  })

  it('accepts a load with thousands separators', () => {
    expect(buildPlanRequest({ ...VALUES, loadLb: '42,000' }).load_lb).toBe(42_000)
  })
})
