import { useEffect, useRef, useState } from 'react'
import { ArrowUp, FileSearch } from 'lucide-react'
import type { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'

const EXAMPLES = [
  'Summarise the main points of this document',
  'What are the key dates and deadlines?',
  'List any numbers or figures mentioned',
]

interface Props {
  messages: ChatMessage[]
  busy: boolean
  hasDocuments: boolean
  scopeLabel: string
  onSend: (question: string) => void
}

export function ChatWindow({ messages, busy, hasDocuments, scopeLabel, onSend }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = (text = input) => {
    const question = text.trim()
    if (!question || busy || !hasDocuments) return
    onSend(question)
    setInput('')
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="mx-auto flex h-full max-w-lg flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-2xl bg-indigo-100 p-4">
              <FileSearch className="h-8 w-8 text-indigo-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-800">Ask your documents anything</h2>
            <p className="mt-2 text-sm text-slate-500">
              {hasDocuments
                ? 'Answers are generated only from your uploaded files, with citations to the exact source.'
                : 'Upload a PDF, Word or text file on the left to get started.'}
            </p>
            {hasDocuments && (
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((example) => (
                  <button
                    key={example}
                    onClick={() => submit(example)}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 hover:border-indigo-300 hover:text-indigo-700"
                  >
                    {example}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="border-t border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white px-3 py-2 focus-within:border-indigo-400 focus-within:ring-2 focus-within:ring-indigo-100">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  submit()
                }
              }}
              rows={1}
              placeholder={hasDocuments ? 'Ask a question about your documents...' : 'Upload a document first'}
              disabled={!hasDocuments}
              className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm outline-none placeholder:text-slate-400"
            />
            <button
              onClick={() => submit()}
              disabled={!input.trim() || !hasDocuments || busy}
              className="rounded-xl bg-indigo-600 p-2 text-white hover:bg-indigo-500 disabled:bg-slate-300"
              title="Send"
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2 text-center text-[11px] text-slate-400">{scopeLabel}</p>
        </div>
      </div>
    </div>
  )
}
