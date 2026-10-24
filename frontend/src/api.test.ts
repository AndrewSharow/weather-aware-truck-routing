import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, planTrip, toApiError } from './api'
import type { PlanRequest } from './types'

const REQUEST: PlanRequest = {
  origin: 'Chicago, IL',
  destination: 'Denver, CO',
  departure: '2026-10-24T13:00:00.000Z',
  load_lb: 42_000,
  interval_mi: 25,
}

function mockFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('planTrip', () => {
  it('posts the request as JSON and returns the plan', async () => {
    const fetchMock = mockFetch(200, { recommended_route_id: 'A', routes: [] })
    const plan = await planTrip(REQUEST)
    expect(plan.recommended_route_id).toBe('A')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toMatch(/\/api\/plan$/)
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual(REQUEST)
  })

  it('throws ApiError with code, message and fields', async () => {
    mockFetch(400, {
      error: 'invalid_input',
      message: 'Please check the highlighted fields.',
      fields: { load_lb: ['Too heavy.'] },
    })
    const error = await planTrip(REQUEST).catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      code: 'invalid_input',
      status: 400,
      fields: { load_lb: ['Too heavy.'] },
    })
  })

  it('turns a network failure into network_error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const error = await planTrip(REQUEST).catch((e: unknown) => e)
    expect(error).toMatchObject({ code: 'network_error' })
  })

  it('lets an abort pass through', async () => {
    const abort = new DOMException('Aborted', 'AbortError')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abort))
    await expect(planTrip(REQUEST)).rejects.toBe(abort)
  })
})

describe('toApiError', () => {
  it('uses a generic message when the body is not ours', () => {
    const error = toApiError(500, null)
    expect(error.code).toBe('server_error')
    expect(error.message).toMatch(/something went wrong/i)
    expect(error.fields).toEqual({})
  })
})
