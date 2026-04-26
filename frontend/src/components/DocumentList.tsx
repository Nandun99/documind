import { AlertCircle, CheckCircle2, FileText, Loader2, Trash2 } from 'lucide-react'
import type { DocumentInfo } from '../types'

interface Props {
  documents: DocumentInfo[]
  selected: string[]
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function DocumentList({ documents, selected, onToggle, onDelete }: Props) {
  if (!documents.length) {
    return <p className="px-1 text-sm text-slate-500">No documents yet.</p>
  }

  return (
    <ul className="space-y-1">
      {documents.map((doc) => (
        <li key={doc.id} className="group flex items-start gap-2 rounded-lg px-2 py-2 hover:bg-slate-100">
          <input
            type="checkbox"
            className="mt-1 accent-indigo-600"
            checked={selected.includes(doc.id)}
            disabled={doc.status !== 'ready'}
            onChange={() => onToggle(doc.id)}
            title="Only search selected documents"
          />
          <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-800" title={doc.filename}>
              {doc.filename}
            </p>
            <p className="flex items-center gap-1 text-xs text-slate-500">
              {doc.status === 'processing' && (
                <>
                  <Loader2 className="h-3 w-3 animate-spin" /> Processing
                </>
              )}
              {doc.status === 'ready' && (
                <>
                  <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                  {doc.pages} {doc.pages === 1 ? 'page' : 'pages'} · {doc.chunk_count} chunks · {formatSize(doc.size_bytes)}
                </>
              )}
              {doc.status === 'failed' && (
                <span className="flex items-center gap-1 text-rose-600" title={doc.error ?? ''}>
                  <AlertCircle className="h-3 w-3" /> Failed
                </span>
              )}
            </p>
          </div>
          <button
            onClick={() => onDelete(doc.id)}
            className="rounded p-1 text-slate-400 opacity-0 transition group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-600"
            title="Delete document"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  )
}
