import type { DocumentInfo, Source, Timings, Usage } from '../types'

const BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, init)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  listDocuments: () => request<DocumentInfo[]>('/api/documents'),

  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<DocumentInfo>('/api/documents', { method: 'POST', body: form })
  },

  deleteDocument: (id: string) => request<void>(`/api/documents/${id}`, { method: 'DELETE' }),
}

export interface StreamHandlers {
  onConversation: (id: string) => void
  onSources: (sources: Source[]) => void
  onToken: (token: string) => void
  onDone: (result: { answer: string; sources: Source[]; usage: Usage; timings: Timings }) => void
}

export interface ChatPayload {
  question: string
  conversation_id?: string | null
  document_ids?: string[] | null
}

/** Sends a question and reads the server-sent events from /api/chat/stream. */
export async function streamChat(payload: ChatPayload, handlers: StreamHandlers, signal?: AbortSignal) {
  const response = await fetch(`${BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!response.ok || !response.body) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      // ignore
    }
    throw new ApiError(response.status, message)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const raw = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      handleEvent(raw, handlers)
      boundary = buffer.indexOf('\n\n')
    }
  }
}

function handleEvent(raw: string, handlers: StreamHandlers) {
  let event = 'message'
  let data = ''
  for (const line of raw.split('\n')) {
    if (line.startsWith('event: ')) event = line.slice(7)
    else if (line.startsWith('data: ')) data += line.slice(6)
  }
  if (!data) return
  const parsed = JSON.parse(data)

  switch (event) {
    case 'conversation':
      handlers.onConversation(parsed.conversation_id)
      break
    case 'sources':
      handlers.onSources(parsed.sources)
      break
    case 'token':
      handlers.onToken(parsed.content)
      break
    case 'done':
      handlers.onDone(parsed)
      break
    case 'error':
      throw new ApiError(500, parsed.detail ?? 'Something went wrong')
  }
}
