import { Clock, Coins, Hash } from 'lucide-react'
import type { Usage } from '../types'

interface Props {
  usage?: Usage
  latencyMs?: number
}

export function UsageBadge({ usage, latencyMs }: Props) {
  if (!usage && latencyMs === undefined) return null

  return (
    <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-400">
      {usage && (
        <>
          <span className="flex items-center gap-1" title={`${usage.input_tokens} in / ${usage.output_tokens} out`}>
            <Hash className="h-3 w-3" />
            {usage.total_tokens.toLocaleString()} tokens
          </span>
          <span className="flex items-center gap-1">
            <Coins className="h-3 w-3" />${usage.cost_usd.toFixed(5)}
          </span>
        </>
      )}
      {latencyMs !== undefined && (
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {(latencyMs / 1000).toFixed(2)}s
        </span>
      )}
    </div>
  )
}
