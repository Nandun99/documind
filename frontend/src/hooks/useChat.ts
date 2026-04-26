import { useCallback, useState } from 'react'
import { api } from '../api/client'
import type { ChatMessage } from '../types'

let counter = 0
const nextId = () => `local-${++counter}`

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const send = useCallback(
    async (question: string, documentIds: string[]) => {
      const assistantId = nextId()
      setMessages((list) => [
        ...list,
        { id: nextId(), role: 'user', content: question, sources: [] },
        { id: assistantId, role: 'assistant', content: '', sources: [], pending: true },
      ])
      setBusy(true)

      try {
        const result = await api.chat({
          question,
          conversation_id: conversationId,
          document_ids: documentIds.length ? documentIds : null,
        })
        setConversationId(result.conversation_id)
        setMessages((list) =>
          list.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: result.answer,
                  sources: result.sources,
                  usage: result.usage,
                  latencyMs: result.timings.total_ms,
                  pending: false,
                }
              : m,
          ),
        )
      } catch (err) {
        setMessages((list) =>
          list.map((m) =>
            m.id === assistantId ? { ...m, content: (err as Error).message, pending: false, error: true } : m,
          ),
        )
      } finally {
        setBusy(false)
      }
    },
    [conversationId],
  )

  const reset = useCallback(() => {
    setConversationId(null)
    setMessages([])
  }, [])

  return { messages, conversationId, busy, send, reset }
}
