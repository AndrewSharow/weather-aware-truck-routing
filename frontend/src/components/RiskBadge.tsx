import { RISK_COLORS, RISK_LABELS } from '@/risk'
import type { RiskLevel } from '@/types'

export function RiskDot({ level }: { level: RiskLevel }) {
  return (
    <span
      aria-hidden
      className="inline-block size-2.5 shrink-0 rounded-full"
      style={{ backgroundColor: RISK_COLORS[level] }}
    />
  )
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium">
      <RiskDot level={level} />
      {RISK_LABELS[level]}
    </span>
  )
}
