import { AlertCircle, Clock } from 'lucide-react'
import { PlanForm } from '@/components/PlanForm'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { usePlan } from '@/hooks/usePlan'

export default function App() {
  const { submit, data, error, loading, slow } = usePlan()

  return (
    <div className="flex h-dvh flex-col md:flex-row">
      <aside className="flex w-full flex-col gap-5 overflow-y-auto border-b p-5 md:w-95 md:shrink-0 md:border-r md:border-b-0">
        <header>
          <h1 className="text-lg font-semibold">Weather-Aware Truck Routing</h1>
          <p className="text-sm text-muted-foreground">
            Pick the safest route by weather, load and travel time.
          </p>
        </header>

        <PlanForm loading={loading} fieldErrors={error?.fields ?? {}} onSubmit={submit} />

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
          <p className="text-sm">
            {data.routes.length} routes · recommended {data.recommended_route_id} (
            {data.recommendation_reason})
          </p>
        )}
      </aside>

      <main className="flex flex-1 items-center justify-center bg-muted text-muted-foreground">
        Map comes in step 5d
      </main>
    </div>
  )
}
