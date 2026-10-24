import { HelpCircle, OctagonAlert, Star } from 'lucide-react'
import { RiskBar } from '@/components/RiskBar'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDuration, formatMiles } from '@/format'
import { cn } from '@/lib/utils'
import type { Route } from '@/types'

interface RouteCardProps {
  route: Route
  recommended: boolean
  reason: string
  selected: boolean
  onSelect: () => void
}

export function RouteCard({
  route,
  recommended,
  reason,
  selected,
  onSelect,
}: RouteCardProps) {
  const { miles_by_level: miles, has_no_travel: hasNoTravel } = route.summary

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className="w-full rounded-xl text-left focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
    >
      <Card
        size="sm"
        className={cn(
          'transition-shadow hover:ring-foreground/25',
          selected && 'ring-2 ring-blue-600 hover:ring-blue-600',
        )}
      >
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-2">
            <span>Route {route.id}</span>
            {recommended && (
              <Badge>
                <Star className="fill-current" />
                Recommended
              </Badge>
            )}
          </CardTitle>
          <p className="text-muted-foreground">
            {formatMiles(route.distance_mi)} · {formatDuration(route.duration_s)}
          </p>
        </CardHeader>

        <CardContent className="flex flex-col gap-2.5">
          <RiskBar milesByLevel={miles} />

          {recommended && <p className="text-xs">Why: {reason}</p>}

          {hasNoTravel && (
            <p className="flex items-center gap-1.5 text-xs font-medium text-destructive">
              <OctagonAlert className="size-3.5 shrink-0" />
              No Travel conditions on {formatMiles(miles.no_travel)} of this route
            </p>
          )}

          {miles.unknown > 0 && (
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <HelpCircle className="size-3.5 shrink-0" />
              No forecast for {formatMiles(miles.unknown)}
            </p>
          )}
        </CardContent>
      </Card>
    </button>
  )
}
