import { describe, expect, it } from 'vitest'
import {
  checkpointsGeoJson,
  riskColorExpression,
  routeBounds,
  routesGeoJson,
} from './map-data'
import { RISK_COLORS } from './risk'
import type { Checkpoint, Route } from './types'

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

function checkpoint(mile: number, risk: Checkpoint['risk']): Checkpoint {
  return {
    mile,
    lat: 40,
    lon: -90 - mile / 100,
    eta: '2026-10-24T13:00:00+00:00',
    wind_mph: 5,
    gust_mph: 8,
    rain_in_hr: 0,
    snow_in_hr: 0,
    risk,
  }
}

describe('checkpointsGeoJson', () => {
  it('makes a point per checkpoint with route id, index and risk', () => {
    const routes = [
      { ...ROUTES[0], checkpoints: [checkpoint(25, 'low'), checkpoint(50, 'severe')] },
      { ...ROUTES[1], checkpoints: [checkpoint(25, 'unknown')] },
    ]
    const geojson = checkpointsGeoJson(routes)
    expect(geojson.features.map((f) => f.properties)).toEqual([
      { routeId: 'A', index: 0, risk: 'low' },
      { routeId: 'A', index: 1, risk: 'severe' },
      { routeId: 'B', index: 0, risk: 'unknown' },
    ])
    expect(geojson.features[1].geometry.coordinates).toEqual([-90.5, 40])
  })
})

describe('riskColorExpression', () => {
  it('maps every level to its color with unknown as fallback', () => {
    const expression = riskColorExpression()
    expect(expression.slice(0, 2)).toEqual(['match', ['get', 'risk']])
    expect(expression).toContain(RISK_COLORS.severe)
    expect(expression.at(-1)).toBe(RISK_COLORS.unknown)
  })
})
