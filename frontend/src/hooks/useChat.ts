import { useCallback, useRef, useState } from 'react'
import { streamChat } from '../api/client'
import type { ChatMessage } from '../types'

let counter = 0
const nextId = () => `local-${++counter}`

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const updateMessage = (id: string, change: (m: ChatMessage) => ChatMessage) =>
    setMessages((list) => list.map((m) => (m.id === id ? change(m) : m)))

  const send = useCallback(
    async (question: string, documentIds: string[]) => {
      const assistantId = nextId()
      setMessages((list) => [
        ...list,
        { id: nextId(), role: 'user', content: question, sources: [] },
        { id: assistantId, role: 'assistant', content: '', sources: [], pending: true },
      ])
      setBusy(true)
      const controller = new AbortController()
      abortRef.current = controller

      try {
        await streamChat(
          {
            question,
            conversation_id: conversationId,
            document_ids: documentIds.length ? documentIds : null,
          },
          {
            onConversation: (id) => setConversationId(id),
            onSources: (sources) => updateMessage(assistantId, (m) => ({ ...m, sources })),
            onToken: (token) => updateMessage(assistantId, (m) => ({ ...m, content: m.content + token })),
            onDone: (result) =>
              updateMessage(assistantId, (m) => ({
                ...m,
                content: result.answer,
                sources: result.sources,
                usage: result.usage,
                latencyMs: result.timings.total_ms,
                pending: false,
              })),
          },
          controller.signal,
        )
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          updateMessage(assistantId, (m) => ({ ...m, pending: false }))
        } else {
          updateMessage(assistantId, (m) => ({
            ...m,
            content: (err as Error).message,
            pending: false,
            error: true,
          }))
        }
      } finally {
        setBusy(false)
        abortRef.current = null
      }
    },
    [conversationId],
  )

  const stop = useCallback(() => abortRef.current?.abort(), [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setConversationId(null)
    setMessages([])
  }, [])

  return { messages, conversationId, busy, send, stop, reset }
}
