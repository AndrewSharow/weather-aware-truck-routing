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
import { MAX_LOAD_LB, departureInputLimits, validatePlanForm } from '@/validate'

const INTERVALS: IntervalMiles[] = [10, 25, 50]

const ERROR_KEYS: Record<keyof PlanFormValues, string> = {
  origin: 'origin',
  destination: 'destination',
  departure: 'departure',
  loadLb: 'load_lb',
  intervalMi: 'interval_mi',
}

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
  const [clientErrors, setClientErrors] = useState<FieldErrors>({})
  const [departureLimits] = useState(() => departureInputLimits())

  const errorFor = (key: string) => clientErrors[key] ?? fieldErrors[key]

  const update = (changes: Partial<PlanFormValues>) => {
    setValues((previous) => ({ ...previous, ...changes }))
    setClientErrors((previous) => {
      const next = { ...previous }
      for (const field of Object.keys(changes) as (keyof PlanFormValues)[]) {
        delete next[ERROR_KEYS[field]]
      }
      return next
    })
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const errors = validatePlanForm(values)
    setClientErrors(errors)
    if (Object.keys(errors).length === 0) onSubmit(buildPlanRequest(values))
  }

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Field id="origin" label="From" error={errorFor('origin')}>
        <Input
          id="origin"
          placeholder="Chicago, IL"
          aria-invalid={Boolean(errorFor('origin'))}
          value={values.origin}
          onChange={(event) => update({ origin: event.target.value })}
        />
      </Field>

      <Field id="destination" label="To" error={errorFor('destination')}>
        <Input
          id="destination"
          placeholder="Denver, CO"
          aria-invalid={Boolean(errorFor('destination'))}
          value={values.destination}
          onChange={(event) => update({ destination: event.target.value })}
        />
      </Field>

      <Field
        id="departure"
        label="Departure (your local time)"
        error={errorFor('departure')}
      >
        <Input
          id="departure"
          type="datetime-local"
          className="cursor-pointer"
          min={departureLimits.min}
          max={departureLimits.max}
          aria-invalid={Boolean(errorFor('departure'))}
          value={values.departure}
          onClick={(event) => event.currentTarget.showPicker?.()}
          onChange={(event) => update({ departure: event.target.value })}
        />
      </Field>

      <Field
        id="load"
        label="Load weight (lb)"
        hint="Cargo only. Max 45,000 lb (80,000 lb with the truck)."
        error={errorFor('load_lb')}
      >
        <Input
          id="load"
          type="number"
          inputMode="numeric"
          min={0}
          max={MAX_LOAD_LB}
          step={500}
          aria-invalid={Boolean(errorFor('load_lb'))}
          value={values.loadLb}
          onChange={(event) => update({ loadLb: event.target.value })}
        />
      </Field>

      <Field id="interval" label="Check weather every" error={errorFor('interval_mi')}>
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
  hint?: string
  error?: string[]
  children: ReactNode
}

function Field({ id, label, hint, error, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && !error && <p className="text-xs text-muted-foreground">{hint}</p>}
      {error?.map((message) => (
        <p key={message} className="text-sm text-destructive">
          {message}
        </p>
      ))}
    </div>
  )
}
