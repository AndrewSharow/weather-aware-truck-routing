import { useState } from 'react'
import { AlertCircle, Clock } from 'lucide-react'
import { MapView } from '@/components/MapView'
import { PlanForm } from '@/components/PlanForm'
import { RouteList } from '@/components/RouteList'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { usePlan } from '@/hooks/usePlan'
import type { PlanRequest } from '@/types'

export default function App() {
  const { submit, data, error, loading, slow } = usePlan()
  const [chosenRouteId, setChosenRouteId] = useState<string | null>(null)
  const selectedRouteId = chosenRouteId ?? data?.recommended_route_id ?? null

  const handleSubmit = (request: PlanRequest) => {
    setChosenRouteId(null)
    void submit(request)
  }

  return (
    <div className="flex h-dvh flex-col md:flex-row">
      <aside className="flex w-full flex-col gap-5 overflow-y-auto border-b p-5 md:w-95 md:shrink-0 md:border-r md:border-b-0">
        <header>
          <h1 className="text-lg font-semibold">Weather-Aware Truck Routing</h1>
          <p className="text-sm text-muted-foreground">
            Pick the safest route by weather, load and travel time.
          </p>
        </header>

        <PlanForm
          loading={loading}
          fieldErrors={error?.fields ?? {}}
          onSubmit={handleSubmit}
        />

        {slow && (
          <Alert>
            <Clock />
            <AlertTitle>Server is waking up</AlertTitle>
            <AlertDescription>
              The free server sleeps when idle. The first plan can take up to a minute.
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>Could not plan the trip</AlertTitle>
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}

        {data && (
          <RouteList
            plan={data}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setChosenRouteId}
          />
        )}
      </aside>

      <main className="relative min-h-96 flex-1">
        <MapView
          plan={data}
          selectedRouteId={selectedRouteId}
          onSelectRoute={setChosenRouteId}
        />
      </main>
    </div>
  )
}
