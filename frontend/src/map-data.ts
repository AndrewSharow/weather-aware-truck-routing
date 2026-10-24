import type { FeatureCollection, LineString, Point } from 'geojson'
import type { ExpressionSpecification } from 'maplibre-gl'
import { RISK_COLORS } from './risk'
import type { RiskLevel, Route } from './types'

export interface CheckpointProperties {
  routeId: string
  index: number
  risk: RiskLevel
}

export type Bounds = [[number, number], [number, number]]

export function routesGeoJson(
  routes: Route[],
): FeatureCollection<LineString, { id: string }> {
  return {
    type: 'FeatureCollection',
    features: routes.map((route) => ({
      type: 'Feature',
      properties: { id: route.id },
      geometry: { type: 'LineString', coordinates: route.geometry },
    })),
  }
}

export function routeBounds(routes: Route[]): Bounds | null {
  const points = routes.flatMap((route) => route.geometry)
  if (!points.length) return null
  const lons = points.map(([lon]) => lon)
  const lats = points.map(([, lat]) => lat)
  return [
    [Math.min(...lons), Math.min(...lats)],
    [Math.max(...lons), Math.max(...lats)],
  ]
}

export function checkpointsGeoJson(
  routes: Route[],
): FeatureCollection<Point, CheckpointProperties> {
  return {
    type: 'FeatureCollection',
    features: routes.flatMap((route) =>
      route.checkpoints.map((checkpoint, index) => ({
        type: 'Feature',
        properties: { routeId: route.id, index, risk: checkpoint.risk },
        geometry: { type: 'Point', coordinates: [checkpoint.lon, checkpoint.lat] },
      })),
    ),
  }
}

export function riskColorExpression(): ExpressionSpecification {
  return [
    'match',
    ['get', 'risk'],
    'low',
    RISK_COLORS.low,
    'moderate',
    RISK_COLORS.moderate,
    'high',
    RISK_COLORS.high,
    'severe',
    RISK_COLORS.severe,
    'no_travel',
    RISK_COLORS.no_travel,
    RISK_COLORS.unknown,
  ]
}
