export type RiskLevel = 'low' | 'moderate' | 'high' | 'severe' | 'no_travel' | 'unknown'

export type IntervalMiles = 10 | 25 | 50

export interface PlanRequest {
  origin: string
  destination: string
  departure: string
  load_lb: number
  interval_mi: IntervalMiles
}

export interface Place {
  label: string
  lat: number
  lon: number
}

export interface Checkpoint {
  mile: number
  lat: number
  lon: number
  eta: string
  wind_mph: number | null
  gust_mph: number | null
  rain_in_hr: number | null
  snow_in_hr: number | null
  risk: RiskLevel
}

export interface RouteSummary {
  miles_by_level: Record<RiskLevel, number>
  avg_risk: number | null
  has_no_travel: boolean
}

export interface Route {
  id: string
  distance_mi: number
  duration_s: number
  geometry: [number, number][]
  summary: RouteSummary
  checkpoints: Checkpoint[]
}

export interface HeatmapPoint {
  lat: number
  lon: number
  risk: (number | null)[]
}

export interface PlanResponse {
  origin: Place
  destination: Place
  recommended_route_id: string
  recommendation_reason: string
  routes: Route[]
  heatmap: {
    start: string
    points: HeatmapPoint[]
  }
}
