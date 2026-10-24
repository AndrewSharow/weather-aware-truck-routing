import { RiskDot } from '@/components/RiskBadge'
import { formatMiles } from '@/format'
import { RISK_COLORS, RISK_LABELS, riskSegments } from '@/risk'
import type { RiskLevel } from '@/types'

export function RiskBar({ milesByLevel }: { milesByLevel: Record<RiskLevel, number> }) {
  const segments = riskSegments(milesByLevel)

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex h-2.5 overflow-hidden rounded-full bg-muted">
        {segments.map(({ level, miles, percent }) => (
          <div
            key={level}
            title={`${RISK_LABELS[level]}: ${formatMiles(miles)}`}
            style={{ width: `${percent}%`, backgroundColor: RISK_COLORS[level] }}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
        {segments.map(({ level, miles }) => (
          <li key={level} className="flex items-center gap-1">
            <RiskDot level={level} />
            {RISK_LABELS[level]} {formatMiles(miles)}
          </li>
        ))}
      </ul>
    </div>
  )
}
