import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DocumentInfo } from '../types'

const POLL_INTERVAL_MS = 1500

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments())
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // keep polling while any document is still being processed
  const processing = documents.some((d) => d.status === 'processing')
  useEffect(() => {
    if (!processing) return
    const timer = setInterval(refresh, POLL_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [processing, refresh])

  const upload = useCallback(
    async (files: File[]) => {
      setUploading(true)
      setError(null)
      try {
        for (const file of files) {
          await api.uploadDocument(file)
        }
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setUploading(false)
        refresh()
      }
    },
    [refresh],
  )

  const remove = useCallback(
    async (id: string) => {
      await api.deleteDocument(id)
      setDocuments((docs) => docs.filter((d) => d.id !== id))
    },
    [],
  )

  return { documents, error, uploading, upload, remove, refresh }
}
