const HOUR_MS = 3_600_000

export function formatMiles(miles: number): string {
  return `${Math.round(miles).toLocaleString('en-US')} mi`
}

export function formatDuration(seconds: number): string {
  const totalMinutes = Math.round(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return hours ? `${hours} h ${minutes} min` : `${minutes} min`
}

export function formatTime(iso: string, timeZone?: string): string {
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
    timeZone,
  })
    .format(new Date(iso))
    .replace(',', '')
}

export function hourLabel(startIso: string, hour: number, timeZone?: string): string {
  const time = new Date(new Date(startIso).getTime() + hour * HOUR_MS)
  return formatTime(time.toISOString(), timeZone)
}

export function localInputToUtcIso(value: string): string {
  return new Date(value).toISOString()
}

export function defaultDepartureInput(now: Date = new Date()): string {
  const next = new Date(now)
  next.setMinutes(0, 0, 0)
  next.setHours(next.getHours() + 1)
  const pad = (n: number) => String(n).padStart(2, '0')
  const date = `${next.getFullYear()}-${pad(next.getMonth() + 1)}-${pad(next.getDate())}`
  return `${date}T${pad(next.getHours())}:00`
}
