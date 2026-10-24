import { RiskDot } from '@/components/RiskBadge'
import { RISK_LABELS, RISK_LEVELS } from '@/risk'

export function Legend() {
  return (
    <div className="rounded-xl bg-background/95 px-3 py-2 text-xs shadow-lg ring-1 ring-foreground/10 backdrop-blur">
      <p className="mb-1 font-medium">Risk level</p>
      <ul className="grid grid-cols-2 gap-x-3 gap-y-0.5">
        {RISK_LEVELS.map((level) => (
          <li key={level} className="flex items-center gap-1.5">
            <RiskDot level={level} />
            {RISK_LABELS[level]}
          </li>
        ))}
      </ul>
    </div>
  )
}
