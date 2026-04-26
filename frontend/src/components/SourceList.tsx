import { useState } from 'react'
import { ChevronDown, FileText } from 'lucide-react'
import type { Source } from '../types'

interface Props {
  sources: Source[]
  highlighted: number | null
}

export function SourceList({ sources, highlighted }: Props) {
  const [open, setOpen] = useState(false)
  if (!sources.length) return null

  const cited = sources.filter((s) => s.cited).length
  const isOpen = open || highlighted !== null

  return (
    <div className="mt-3 border-t border-slate-100 pt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700"
      >
        <ChevronDown className={`h-3.5 w-3.5 transition ${isOpen ? 'rotate-180' : ''}`} />
        {sources.length} {sources.length === 1 ? 'source' : 'sources'}
        {cited > 0 && ` · ${cited} cited`}
      </button>
      {isOpen && (
        <ol className="mt-2 space-y-2">
          {sources.map((s) => (
            <li
              key={s.index}
              id={`source-${s.index}`}
              className={`rounded-lg border p-2 text-xs transition ${
                highlighted === s.index ? 'border-indigo-300 bg-indigo-50' : 'border-slate-200 bg-slate-50'
              } ${s.cited ? '' : 'opacity-70'}`}
            >
              <div className="mb-1 flex items-center gap-1.5 font-medium text-slate-700">
                <span className="rounded bg-indigo-600 px-1.5 text-[10px] text-white">{s.index}</span>
                <FileText className="h-3 w-3" />
                <span className="truncate">{s.filename}</span>
                {s.page && <span className="text-slate-400">p. {s.page}</span>}
                <span className="ml-auto text-slate-400">{Math.round(s.score * 100)}% match</span>
              </div>
              <p className="whitespace-pre-line text-slate-600">{s.snippet}</p>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
