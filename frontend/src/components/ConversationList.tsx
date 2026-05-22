import { MessageSquare, Trash2 } from 'lucide-react'
import type { Conversation } from '../types'

interface Props {
  conversations: Conversation[]
  activeId: string | null
  onOpen: (id: string) => void
  onDelete: (id: string) => void
}

export function ConversationList({ conversations, activeId, onOpen, onDelete }: Props) {
  if (!conversations.length) {
    return <p className="px-1 text-sm text-slate-500">No conversations yet.</p>
  }

  return (
    <ul className="space-y-1">
      {conversations.map((c) => (
        <li
          key={c.id}
          className={`group flex items-center gap-2 rounded-lg px-2 py-2 text-sm ${
            c.id === activeId ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-100'
          }`}
        >
          <MessageSquare className="h-4 w-4 shrink-0 opacity-60" />
          <button onClick={() => onOpen(c.id)} className="min-w-0 flex-1 truncate text-left" title={c.title}>
            {c.title}
          </button>
          <button
            onClick={() => onDelete(c.id)}
            className="rounded p-1 text-slate-400 opacity-0 transition group-hover:opacity-100 hover:text-rose-600"
            title="Delete conversation"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </li>
      ))}
    </ul>
  )
}
