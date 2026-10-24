import { Layers } from 'lucide-react'
import { Slider } from '@/components/ui/slider'
import { Toggle } from '@/components/ui/toggle'
import { hourLabel } from '@/format'

export const HEATMAP_HOURS = 48

interface HeatmapControlProps {
  start: string
  hour: number
  visible: boolean
  onHourChange: (hour: number) => void
  onVisibleChange: (visible: boolean) => void
}

export function HeatmapControl({
  start,
  hour,
  visible,
  onHourChange,
  onVisibleChange,
}: HeatmapControlProps) {
  return (
    <div className="flex w-full flex-col gap-2.5 rounded-xl bg-background/95 p-3 text-sm shadow-lg ring-1 ring-foreground/10 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-medium">Weather risk heatmap</p>
          <p className="text-xs text-muted-foreground">
            +{hour} h after departure · {hourLabel(start, hour)}
          </p>
        </div>
        <Toggle
          size="sm"
          variant="outline"
          pressed={visible}
          onPressedChange={onVisibleChange}
          aria-label="Show heatmap"
        >
          <Layers />
          {visible ? 'On' : 'Off'}
        </Toggle>
      </div>
      <Slider
        min={0}
        max={HEATMAP_HOURS}
        step={1}
        value={[hour]}
        disabled={!visible}
        onValueChange={([value]) => onHourChange(value)}
        aria-label="Forecast hour"
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Departure</span>
        <span>+24 h</span>
        <span>+48 h</span>
      </div>
    </div>
  )
}
