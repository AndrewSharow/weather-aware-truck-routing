import { useEffect, useMemo, useRef, useState } from 'react'
import type { ExpressionSpecification } from 'maplibre-gl'
import Map, {
  Layer,
  Marker,
  NavigationControl,
  Source,
  type MapLayerMouseEvent,
  type MapRef,
} from 'react-map-gl/maplibre'
import { CheckpointPopup } from '@/components/CheckpointPopup'
import {
  checkpointsGeoJson,
  riskColorExpression,
  routeBounds,
  routesGeoJson,
} from '@/map-data'
import type { PlanResponse } from '@/types'

const MAP_STYLE = 'https://tiles.openfreemap.org/styles/positron'
const USA_VIEW = { longitude: -98.5, latitude: 39.5, zoom: 3.6 }
const INTERACTIVE_LAYERS = ['checkpoints', 'routes-other', 'routes-selected']
const RISK_COLOR = riskColorExpression()
const SELECTED_COLOR = '#2563eb'
const OTHER_COLOR = '#94a3b8'

interface MapViewProps {
  plan: PlanResponse | null
  selectedRouteId: string | null
  onSelectRoute: (routeId: string) => void
}

export function MapView({ plan, selectedRouteId, onSelectRoute }: MapViewProps) {
  const mapRef = useRef<MapRef>(null)
  const [hovering, setHovering] = useState(false)
  const [popup, setPopup] = useState<OpenPopup | null>(null)
  const routes = useMemo(() => routesGeoJson(plan?.routes ?? []), [plan])
  const checkpoints = useMemo(() => checkpointsGeoJson(plan?.routes ?? []), [plan])

  useEffect(() => {
    const bounds = routeBounds(plan?.routes ?? [])
    if (bounds) mapRef.current?.fitBounds(bounds, { padding: 60, duration: 800 })
  }, [plan])

  const isSelected: ExpressionSpecification = ['==', ['get', 'id'], selectedRouteId ?? '']
  const isOther: ExpressionSpecification = ['!', isSelected]
  const onSelectedRoute: ExpressionSpecification = [
    '==',
    ['get', 'routeId'],
    selectedRouteId ?? '',
  ]

  const popupCheckpoint =
    popup && popup.plan === plan && popup.routeId === selectedRouteId
      ? plan?.routes.find((route) => route.id === popup.routeId)?.checkpoints[popup.index]
      : undefined

  const handleClick = (event: MapLayerMouseEvent) => {
    const feature = event.features?.[0]
    if (!feature || !plan) return
    if (feature.layer.id === 'checkpoints') {
      const { routeId, index } = feature.properties
      setPopup({ plan, routeId, index })
    } else {
      onSelectRoute(feature.properties.id)
    }
  }

  return (
    <Map
      ref={mapRef}
      initialViewState={USA_VIEW}
      mapStyle={MAP_STYLE}
      interactiveLayerIds={INTERACTIVE_LAYERS}
      cursor={hovering ? 'pointer' : 'grab'}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      onClick={handleClick}
      style={{ width: '100%', height: '100%' }}
    >
      <NavigationControl position="top-right" showCompass={false} />

      <Source id="routes" type="geojson" data={routes}>
        <Layer
          id="routes-other"
          type="line"
          filter={isOther}
          layout={{ 'line-join': 'round', 'line-cap': 'round' }}
          paint={{ 'line-color': OTHER_COLOR, 'line-width': 4, 'line-opacity': 0.9 }}
        />
        <Layer
          id="routes-selected-casing"
          type="line"
          filter={isSelected}
          layout={{ 'line-join': 'round', 'line-cap': 'round' }}
          paint={{ 'line-color': '#ffffff', 'line-width': 9 }}
        />
        <Layer
          id="routes-selected"
          type="line"
          filter={isSelected}
          layout={{ 'line-join': 'round', 'line-cap': 'round' }}
          paint={{ 'line-color': SELECTED_COLOR, 'line-width': 6 }}
        />
      </Source>

      <Source id="checkpoints" type="geojson" data={checkpoints}>
        <Layer
          id="checkpoints"
          type="circle"
          filter={onSelectedRoute}
          paint={{
            'circle-color': RISK_COLOR,
            'circle-radius': 6,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 1.5,
          }}
        />
      </Source>

      {popupCheckpoint && popup && (
        <CheckpointPopup
          routeId={popup.routeId}
          checkpoint={popupCheckpoint}
          onClose={() => setPopup(null)}
        />
      )}

      {plan && (
        <>
          <PlaceMarker lon={plan.origin.lon} lat={plan.origin.lat} label="A" />
          <PlaceMarker lon={plan.destination.lon} lat={plan.destination.lat} label="B" />
        </>
      )}
    </Map>
  )
}

interface OpenPopup {
  plan: PlanResponse
  routeId: string
  index: number
}

function PlaceMarker({ lon, lat, label }: { lon: number; lat: number; label: string }) {
  return (
    <Marker longitude={lon} latitude={lat}>
      <div className="flex size-7 items-center justify-center rounded-full border-2 border-white bg-neutral-900 text-xs font-semibold text-white shadow">
        {label}
      </div>
    </Marker>
  )
}
