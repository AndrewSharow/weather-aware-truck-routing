import { Popup } from 'react-map-gl/maplibre'
import { RiskBadge } from '@/components/RiskBadge'
import { formatTime, formatValue } from '@/format'
import type { Checkpoint } from '@/types'

interface CheckpointPopupProps {
  routeId: string
  checkpoint: Checkpoint
  onClose: () => void
}

export function CheckpointPopup({ routeId, checkpoint, onClose }: CheckpointPopupProps) {
  const gusts =
    checkpoint.gust_mph === null ? '' : ` (gusts ${Math.round(checkpoint.gust_mph)})`

  return (
    <Popup
      longitude={checkpoint.lon}
      latitude={checkpoint.lat}
      anchor="bottom"
      offset={10}
      closeOnClick={false}
      onClose={onClose}
      maxWidth="280px"
    >
      <div className="flex flex-col gap-2 p-1 text-sm">
        <div className="flex items-center justify-between gap-3">
          <span className="font-semibold">
            Route {routeId} · mile {Math.round(checkpoint.mile)}
          </span>
          <RiskBadge level={checkpoint.risk} />
        </div>
        <p className="text-muted-foreground">ETA {formatTime(checkpoint.eta)}</p>
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
          <dt className="text-muted-foreground">Wind</dt>
          <dd>
            {formatValue(checkpoint.wind_mph, 'mph', 0)}
            {gusts}
          </dd>
          <dt className="text-muted-foreground">Rain</dt>
          <dd>{formatValue(checkpoint.rain_in_hr, 'in/hr', 2)}</dd>
          <dt className="text-muted-foreground">Snow</dt>
          <dd>{formatValue(checkpoint.snow_in_hr, 'in/hr', 2)}</dd>
        </dl>
      </div>
    </Popup>
  )
}
