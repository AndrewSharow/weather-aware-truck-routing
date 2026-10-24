import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, planTrip } from '@/api'
import type { PlanRequest, PlanResponse } from '@/types'

const SLOW_AFTER_MS = 10_000

export function usePlan() {
  const [data, setData] = useState<PlanResponse | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(false)
  const [slow, setSlow] = useState(false)
  const current = useRef<AbortController | null>(null)

  useEffect(() => () => current.current?.abort(), [])

  const submit = useCallback(async (request: PlanRequest) => {
    current.current?.abort()
    const controller = new AbortController()
    current.current = controller
    setLoading(true)
    setSlow(false)
    setError(null)
    const slowTimer = setTimeout(() => setSlow(true), SLOW_AFTER_MS)

    try {
      setData(await planTrip(request, controller.signal))
    } catch (caught) {
      if (controller.signal.aborted) return
      setData(null)
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError('server_error', 'Something went wrong. Please try again.'),
      )
    } finally {
      clearTimeout(slowTimer)
      if (current.current === controller) {
        setLoading(false)
        setSlow(false)
      }
    }
  }, [])

  return { submit, data, error, loading, slow }
}
