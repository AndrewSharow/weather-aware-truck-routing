import { ChevronDown } from 'lucide-react'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { RiskDot } from '@/components/RiskBadge'
import { RISK_LABELS } from '@/risk'
import type { RiskLevel } from '@/types'

const THRESHOLDS: { level: RiskLevel; wind: string; rain: string; snow: string }[] = [
  { level: 'low', wind: '<25', rain: '<0.10', snow: '<0.5' },
  { level: 'moderate', wind: '25–34', rain: '0.10–0.25', snow: '0.5–1.0' },
  { level: 'high', wind: '35–44', rain: '0.25–0.50', snow: '1.0–2.0' },
  { level: 'severe', wind: '45–54', rain: '0.50–1.00', snow: '2.0–3.0' },
  { level: 'no_travel', wind: '≥55', rain: '>1.00', snow: '>3.0' },
]

export function HowRiskWorks() {
  return (
    <Collapsible className="rounded-xl border text-sm">
      <CollapsibleTrigger className="group flex w-full items-center justify-between px-3 py-2 font-medium">
        How risk works
        <ChevronDown className="size-4 transition-transform group-data-[state=open]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent className="flex flex-col gap-3 px-3 pb-3 text-xs">
        <p>
          Every checkpoint gets the weather forecast for the hour the truck arrives there.
          Its risk is the worst of wind, rain and snow:
        </p>

        <table className="w-full text-left">
          <thead className="text-muted-foreground">
            <tr>
              <th className="font-normal">Level</th>
              <th className="font-normal">Wind mph</th>
              <th className="font-normal">Rain in/hr</th>
              <th className="font-normal">Snow in/hr</th>
            </tr>
          </thead>
          <tbody>
            {THRESHOLDS.map(({ level, wind, rain, snow }) => (
              <tr key={level}>
                <td className="py-0.5 pr-2">
                  <span className="flex items-center gap-1.5 whitespace-nowrap">
                    <RiskDot level={level} />
                    {RISK_LABELS[level]}
                  </span>
                </td>
                <td className="pr-2">{wind}</td>
                <td className="pr-2">{rain}</td>
                <td>{snow}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div>
          <p className="font-medium">Load rules</p>
          <ul className="list-disc pl-4">
            <li>Wind 35–44 mph with load over 40,000 lb → Severe</li>
            <li>Wind 45–54 mph with load over 30,000 lb → No Travel</li>
            <li>Wind 55 mph or more → No Travel for any load</li>
          </ul>
        </div>

        <div>
          <p className="font-medium">Recommended route</p>
          <ol className="list-decimal pl-4">
            <li>Avoid No Travel miles (if another route has none)</li>
            <li>Fewest Severe miles</li>
            <li>Fewest High miles</li>
            <li>Lowest average risk (Low = 0 … No Travel = 4, by miles)</li>
            <li>Shortest travel time</li>
          </ol>
        </div>

        <div>
          <p className="font-medium">Notes</p>
          <ul className="list-disc pl-4">
            <li>Wind = sustained wind; gusts are shown for information.</li>
            <li>Each checkpoint covers the miles since the previous one.</li>
            <li>Missing forecast = Unknown (grey), never Low.</li>
            <li>
              Heatmap: the same rules on a grid around the routes, by forecast hour.
            </li>
          </ul>
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
