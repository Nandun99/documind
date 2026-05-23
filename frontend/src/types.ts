export type DocumentStatus = 'processing' | 'ready' | 'failed'

export interface DocumentInfo {
  id: string
  filename: string
  content_type: string | null
  size_bytes: number
  status: DocumentStatus
  error: string | null
  pages: number
  chunk_count: number
  created_at: string
}

export interface Source {
  index: number
  document_id: string
  filename: string
  page: number | null
  snippet: string
  score: number
  cited: boolean
}

export interface Usage {
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost_usd: number
}

export interface Timings {
  retrieval_ms: number
  generation_ms: number
  total_ms: number
}

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: Source[]
  usage?: Usage
  latencyMs?: number
  pending?: boolean
  error?: boolean
}

export interface StoredMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources: Source[]
  input_tokens: number
  output_tokens: number
  cost_usd: number
  latency_ms: number
  created_at: string
}
