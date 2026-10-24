import { describe, expect, it } from 'vitest'
import { routeBounds, routesGeoJson } from './map-data'
import type { Route } from './types'

function route(id: string, geometry: [number, number][]): Route {
  return {
    id,
    distance_mi: 100,
    duration_s: 3600,
    geometry,
    summary: {
      miles_by_level: {
        low: 100,
        moderate: 0,
        high: 0,
        severe: 0,
        no_travel: 0,
        unknown: 0,
      },
      avg_risk: 0,
      has_no_travel: false,
    },
    checkpoints: [],
  }
}

const ROUTES = [
  route('A', [
    [-87.6, 41.9],
    [-95, 40],
  ]),
  route('B', [
    [-87.6, 41.9],
    [-105, 39.7],
  ]),
]

describe('routesGeoJson', () => {
  it('makes one line feature per route with its id', () => {
    const geojson = routesGeoJson(ROUTES)
    expect(geojson.features).toHaveLength(2)
    expect(geojson.features[1].properties.id).toBe('B')
    expect(geojson.features[1].geometry).toEqual({
      type: 'LineString',
      coordinates: ROUTES[1].geometry,
    })
  })
})

describe('routeBounds', () => {
  it('covers every point of every route', () => {
    expect(routeBounds(ROUTES)).toEqual([
      [-105, 39.7],
      [-87.6, 41.9],
    ])
  })

  it('returns null without routes', () => {
    expect(routeBounds([])).toBeNull()
  })
})
