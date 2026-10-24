import type { PlanRequest, PlanResponse } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type FieldErrors = Record<string, string[]>

export class ApiError extends Error {
  code: string
  status: number
  fields: FieldErrors

  constructor(code: string, message: string, status = 0, fields: FieldErrors = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.fields = fields
  }
}

export async function planTrip(
  request: PlanRequest,
  signal?: AbortSignal,
): Promise<PlanResponse> {
  let response: Response
  try {
    response = await fetch(`${API_URL}/api/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError(
      'network_error',
      "Can't reach the server. Check your connection and try again.",
    )
  }

  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) throw toApiError(response.status, body)
  return body as PlanResponse
}

export function toApiError(status: number, body: unknown): ApiError {
  if (isErrorBody(body)) {
    return new ApiError(body.error, body.message, status, body.fields ?? {})
  }
  return new ApiError('server_error', 'Something went wrong. Please try again.', status)
}

interface ErrorBody {
  error: string
  message: string
  fields?: FieldErrors
}

function isErrorBody(body: unknown): body is ErrorBody {
  return (
    typeof body === 'object' &&
    body !== null &&
    typeof (body as ErrorBody).error === 'string' &&
    typeof (body as ErrorBody).message === 'string'
  )
}
