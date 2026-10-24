import { localInputToUtcIso } from './format'
import type { IntervalMiles, PlanRequest } from './types'

export interface PlanFormValues {
  origin: string
  destination: string
  departure: string
  loadLb: string
  intervalMi: IntervalMiles
}

export function buildPlanRequest(values: PlanFormValues): PlanRequest {
  return {
    origin: values.origin.trim(),
    destination: values.destination.trim(),
    departure: localInputToUtcIso(values.departure),
    load_lb: Number(values.loadLb.replaceAll(',', '')),
    interval_mi: values.intervalMi,
  }
}
