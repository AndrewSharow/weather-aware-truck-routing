import type { FieldErrors } from './api'
import { toLocalInputValue } from './format'
import type { PlanFormValues } from './plan-request'

export const MAX_LOAD_LB = 45_000
export const MAX_DAYS_AHEAD = 7
const PAST_TOLERANCE_MS = 5 * 60_000
const DAY_MS = 86_400_000

export function validatePlanForm(values: PlanFormValues, now = new Date()): FieldErrors {
  const errors: FieldErrors = {}
  const origin = values.origin.trim()
  const destination = values.destination.trim()

  if (!origin) errors.origin = ['Enter a starting place.']
  if (!destination) errors.destination = ['Enter a destination.']
  else if (origin.toLowerCase() === destination.toLowerCase()) {
    errors.destination = ['Destination must be different from origin.']
  }

  const departure = new Date(values.departure).getTime()
  if (!values.departure || Number.isNaN(departure)) {
    errors.departure = ['Pick a departure time.']
  } else if (departure < now.getTime() - PAST_TOLERANCE_MS) {
    errors.departure = ["Departure can't be in the past."]
  } else if (departure > now.getTime() + MAX_DAYS_AHEAD * DAY_MS) {
    errors.departure = [`Departure must be within the next ${MAX_DAYS_AHEAD} days.`]
  }

  const load = Number(values.loadLb.replaceAll(',', ''))
  if (!values.loadLb.trim() || !Number.isInteger(load)) {
    errors.load_lb = ['Enter the load in pounds.']
  } else if (load < 0 || load > MAX_LOAD_LB) {
    errors.load_lb = ['Load must be between 0 and 45,000 lb.']
  }

  return errors
}

export function departureInputLimits(now = new Date()): { min: string; max: string } {
  return {
    min: toLocalInputValue(now),
    max: toLocalInputValue(new Date(now.getTime() + MAX_DAYS_AHEAD * DAY_MS)),
  }
}
