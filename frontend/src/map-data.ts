import type { FeatureCollection, LineString, Point } from 'geojson'
import type { ExpressionSpecification } from 'maplibre-gl'
import { RISK_COLORS } from './risk'
import type { HeatmapPoint, RiskLevel, Route } from './types'

export interface CheckpointProperties {
  routeId: string
  index: number
  risk: RiskLevel
}

export type Bounds = [[number, number], [number, number]]

const PIXELS_PER_DEGREE_AT_ZOOM_0 = 512 / 360
const MAX_ZOOM = 20
const DEFAULT_GRID_SPACING = 0.5

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

export function heatmapGeoJson(
  points: HeatmapPoint[],
): FeatureCollection<Point, { risk: number[] }> {
  return {
    type: 'FeatureCollection',
    features: points.map((point) => ({
      type: 'Feature',
      properties: { risk: point.risk.map((score) => score ?? -1) },
      geometry: { type: 'Point', coordinates: [point.lon, point.lat] },
    })),
  }
}

export function heatmapColorExpression(hour: number): ExpressionSpecification {
  return [
    'match',
    ['at', hour, ['array', 'number', ['get', 'risk']]],
    0,
    RISK_COLORS.low,
    1,
    RISK_COLORS.moderate,
    2,
    RISK_COLORS.high,
    3,
    RISK_COLORS.severe,
    4,
    RISK_COLORS.no_travel,
    RISK_COLORS.unknown,
  ]
}

export function gridSpacing(points: HeatmapPoint[]): number {
  const lats = [...new Set(points.map((point) => point.lat))].sort((a, b) => a - b)
  const steps = lats.slice(1).map((lat, i) => lat - lats[i])
  return steps.length ? Math.min(...steps) : DEFAULT_GRID_SPACING
}

export function heatmapRadiusExpression(spacingDegrees: number): ExpressionSpecification {
  const radiusAtZoom0 = spacingDegrees * PIXELS_PER_DEGREE_AT_ZOOM_0
  return [
    'interpolate',
    ['exponential', 2],
    ['zoom'],
    0,
    radiusAtZoom0,
    MAX_ZOOM,
    radiusAtZoom0 * 2 ** MAX_ZOOM,
  ]
}
