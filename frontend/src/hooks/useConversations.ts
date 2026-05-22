import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Conversation } from '../types'

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])

  const refresh = useCallback(async () => {
    try {
      setConversations(await api.listConversations())
    } catch {
      // the sidebar just stays empty if the API is down
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const remove = useCallback(async (id: string) => {
    await api.deleteConversation(id)
    setConversations((list) => list.filter((c) => c.id !== id))
  }, [])

  return { conversations, refresh, remove }
}
