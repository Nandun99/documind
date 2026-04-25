import { useState } from 'react'
import { BrainCircuit } from 'lucide-react'
import { DocumentList } from './components/DocumentList'
import { UploadDropzone } from './components/UploadDropzone'
import { useDocuments } from './hooks/useDocuments'

export default function App() {
  const docs = useDocuments()
  const [selected, setSelected] = useState<string[]>([])

  const toggle = (id: string) =>
    setSelected((list) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id]))

  return (
    <div className="flex h-full bg-slate-50 font-sans text-slate-900">
      <aside className="flex w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
          <BrainCircuit className="h-6 w-6 text-indigo-600" />
          <h1 className="text-lg font-semibold">DocuMind</h1>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          <h2 className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Documents</h2>
          <UploadDropzone uploading={docs.uploading} onFiles={docs.upload} />
          {docs.error && <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{docs.error}</p>}
          <div className="mt-3">
            <DocumentList documents={docs.documents} selected={selected} onToggle={toggle} onDelete={docs.remove} />
          </div>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 items-center justify-center text-slate-400">Chat coming soon</main>
    </div>
  )
}
