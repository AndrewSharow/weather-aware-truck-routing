import type { FeatureCollection, LineString } from 'geojson'
import type { Route } from './types'

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
