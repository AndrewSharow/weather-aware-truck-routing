import { useState, type FormEvent, type ReactNode } from 'react'
import { Loader2, Route } from 'lucide-react'
import type { FieldErrors } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { defaultDepartureInput } from '@/format'
import { buildPlanRequest, type PlanFormValues } from '@/plan-request'
import type { IntervalMiles, PlanRequest } from '@/types'

const INTERVALS: IntervalMiles[] = [10, 25, 50]
const MAX_LOAD_LB = 45_000

interface PlanFormProps {
  loading: boolean
  fieldErrors: FieldErrors
  onSubmit: (request: PlanRequest) => void
}

export function PlanForm({ loading, fieldErrors, onSubmit }: PlanFormProps) {
  const [values, setValues] = useState<PlanFormValues>({
    origin: '',
    destination: '',
    departure: defaultDepartureInput(),
    loadLb: '40000',
    intervalMi: 25,
  })

  const update = (changes: Partial<PlanFormValues>) =>
    setValues((previous) => ({ ...previous, ...changes }))

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    onSubmit(buildPlanRequest(values))
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Field id="origin" label="From" error={fieldErrors.origin}>
        <Input
          id="origin"
          required
          placeholder="Chicago, IL"
          value={values.origin}
          onChange={(event) => update({ origin: event.target.value })}
        />
      </Field>

      <Field id="destination" label="To" error={fieldErrors.destination}>
        <Input
          id="destination"
          required
          placeholder="Denver, CO"
          value={values.destination}
          onChange={(event) => update({ destination: event.target.value })}
        />
      </Field>

      <Field
        id="departure"
        label="Departure (your local time)"
        error={fieldErrors.departure}
      >
        <Input
          id="departure"
          type="datetime-local"
          required
          value={values.departure}
          onChange={(event) => update({ departure: event.target.value })}
        />
      </Field>

      <Field id="load" label="Load weight (lb)" error={fieldErrors.load_lb}>
        <Input
          id="load"
          type="number"
          required
          min={0}
          max={MAX_LOAD_LB}
          step={500}
          value={values.loadLb}
          onChange={(event) => update({ loadLb: event.target.value })}
        />
      </Field>

      <Field id="interval" label="Check weather every" error={fieldErrors.interval_mi}>
        <ToggleGroup
          id="interval"
          type="single"
          variant="outline"
          value={String(values.intervalMi)}
          onValueChange={(value) => {
            if (value) update({ intervalMi: Number(value) as IntervalMiles })
          }}
        >
          {INTERVALS.map((miles) => (
            <ToggleGroupItem key={miles} value={String(miles)} className="px-4">
              {miles} mi
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </Field>

      <Button type="submit" size="lg" disabled={loading}>
        {loading ? <Loader2 className="animate-spin" /> : <Route />}
        {loading ? 'Planning…' : 'Plan routes'}
      </Button>
    </form>
  )
}

interface FieldProps {
  id: string
  label: string
  error?: string[]
  children: ReactNode
}

function Field({ id, label, error, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error?.map((message) => (
        <p key={message} className="text-sm text-destructive">
          {message}
        </p>
      ))}
    </div>
  )
}
