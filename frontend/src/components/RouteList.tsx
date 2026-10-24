import { RouteCard } from '@/components/RouteCard'
import type { PlanResponse } from '@/types'

interface RouteListProps {
  plan: PlanResponse
  selectedRouteId: string | null
  onSelectRoute: (routeId: string) => void
}

export function RouteList({ plan, selectedRouteId, onSelectRoute }: RouteListProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="text-sm">
        <h2 className="font-semibold">
          {plan.routes.length} {plan.routes.length === 1 ? 'route' : 'routes'} found
        </h2>
        <p className="text-muted-foreground">
          {plan.origin.label} → {plan.destination.label}
        </p>
      </div>

      {plan.routes.map((route) => (
        <RouteCard
          key={route.id}
          route={route}
          recommended={route.id === plan.recommended_route_id}
          reason={plan.recommendation_reason}
          selected={route.id === selectedRouteId}
          onSelect={() => onSelectRoute(route.id)}
        />
      ))}
    </section>
  )
}
