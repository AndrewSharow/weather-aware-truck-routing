import { ChevronDown } from 'lucide-react'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'

const THRESHOLDS = [
  { condition: 'Wind (mph)', values: ['<25', '25–34', '35–44', '45–54', '≥55'] },
  {
    condition: 'Rain (in/hr)',
    values: ['<0.10', '0.10–0.25', '0.25–0.50', '0.50–1.00', '>1.00'],
  },
  {
    condition: 'Snow (in/hr)',
    values: ['<0.5', '0.5–1.0', '1.0–2.0', '2.0–3.0', '>3.0'],
  },
]

const LEVELS = ['Low', 'Moderate', 'High', 'Severe', 'No Travel']

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

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="text-muted-foreground">
              <tr>
                <th className="pr-2 font-normal" />
                {LEVELS.map((level) => (
                  <th key={level} className="pr-2 font-normal">
                    {level}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {THRESHOLDS.map(({ condition, values }) => (
                <tr key={condition}>
                  <td className="pr-2 font-medium whitespace-nowrap">{condition}</td>
                  {values.map((value) => (
                    <td key={value} className="pr-2 whitespace-nowrap">
                      {value}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

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
