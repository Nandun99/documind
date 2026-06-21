import { useState } from 'react'
import Markdown from 'react-markdown'
import { Bot, Loader2, User } from 'lucide-react'
import type { ChatMessage } from '../types'
import { SourceList } from './SourceList'
import { UsageBadge } from './UsageBadge'

// turn [1] citations into links so they can be rendered as clickable chips
const withCitationLinks = (text: string) => text.replace(/\[(\d+)\](?!\()/g, '[$1](#source-$1)')

export function MessageBubble({ message }: { message: ChatMessage }) {
  const [highlighted, setHighlighted] = useState<number | null>(null)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end gap-3">
        <div className="max-w-[75%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-indigo-600 px-4 py-2.5 text-sm text-white">
          {message.content}
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200">
          <User className="h-4 w-4 text-slate-600" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100">
        <Bot className="h-4 w-4 text-indigo-600" />
      </div>
      <div
        className={`max-w-[80%] rounded-2xl rounded-tl-sm border px-4 py-3 text-sm shadow-sm ${
          message.error ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-slate-200 bg-white text-slate-800'
        }`}
      >
        {message.pending && !message.content ? (
          <span className="flex items-center gap-2 text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Searching your documents...
          </span>
        ) : (
          <div className="prose-answer">
            <Markdown
              components={{
                a: ({ href, children }) => {
                  const match = href?.match(/^#source-(\d+)$/)
                  if (!match) {
                    return (
                      <a href={href} target="_blank" rel="noreferrer" className="text-indigo-600 underline">
                        {children}
                      </a>
                    )
                  }
                  const index = Number(match[1])
                  return (
                    <button
                      onClick={() => setHighlighted(highlighted === index ? null : index)}
                      className="mx-0.5 rounded bg-indigo-100 px-1 align-super text-[10px] font-semibold text-indigo-700 hover:bg-indigo-200"
                    >
                      {index}
                    </button>
                  )
                },
              }}
            >
              {withCitationLinks(message.content)}
            </Markdown>
          </div>
        )}
        {!message.pending && <SourceList sources={message.sources} highlighted={highlighted} />}
        {!message.pending && !message.error && <UsageBadge usage={message.usage} latencyMs={message.latencyMs} />}
      </div>
    </div>
  )
}
