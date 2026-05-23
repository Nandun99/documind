import { useState } from 'react'
import { BrainCircuit, Plus } from 'lucide-react'
import { ChatWindow } from './components/ChatWindow'
import { ConversationList } from './components/ConversationList'
import { DocumentList } from './components/DocumentList'
import { UploadDropzone } from './components/UploadDropzone'
import { useChat } from './hooks/useChat'
import { useConversations } from './hooks/useConversations'
import { useDocuments } from './hooks/useDocuments'

export default function App() {
  const docs = useDocuments()
  const conversations = useConversations()
  const chat = useChat(conversations.refresh)
  const [selected, setSelected] = useState<string[]>([])

  const readyDocs = docs.documents.filter((d) => d.status === 'ready')
  // ignore selections for documents that were deleted
  const activeSelection = selected.filter((id) => readyDocs.some((d) => d.id === id))

  const toggle = (id: string) =>
    setSelected((list) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id]))

  const scopeLabel = activeSelection.length
    ? `Searching ${activeSelection.length} selected ${activeSelection.length === 1 ? 'document' : 'documents'}`
    : `Searching all ${readyDocs.length} ${readyDocs.length === 1 ? 'document' : 'documents'}`

  const deleteConversation = async (id: string) => {
    await conversations.remove(id)
    if (chat.conversationId === id) chat.reset()
  }

  return (
    <div className="flex h-full bg-slate-50 font-sans text-slate-900">
      <aside className="flex w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
          <BrainCircuit className="h-6 w-6 text-indigo-600" />
          <h1 className="text-lg font-semibold">DocuMind</h1>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-4 py-4">
          <section>
            <h2 className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Documents</h2>
            <UploadDropzone uploading={docs.uploading} onFiles={docs.upload} />
            {docs.error && <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{docs.error}</p>}
            <div className="mt-3">
              <DocumentList
                documents={docs.documents}
                selected={activeSelection}
                onToggle={toggle}
                onDelete={docs.remove}
              />
            </div>
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between px-1">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Conversations</h2>
              <button
                onClick={chat.reset}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
              >
                <Plus className="h-3.5 w-3.5" /> New chat
              </button>
            </div>
            <ConversationList
              conversations={conversations.conversations}
              activeId={chat.conversationId}
              onOpen={chat.open}
              onDelete={deleteConversation}
            />
          </section>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <ChatWindow
          messages={chat.messages}
          busy={chat.busy}
          hasDocuments={readyDocs.length > 0}
          scopeLabel={scopeLabel}
          onSend={(question) => chat.send(question, activeSelection)}
          onStop={chat.stop}
        />
      </main>
    </div>
  )
}
