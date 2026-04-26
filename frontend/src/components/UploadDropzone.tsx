import { useRef, useState } from 'react'
import { Loader2, Upload } from 'lucide-react'

const ACCEPT = '.pdf,.txt,.md,.docx'

interface Props {
  uploading: boolean
  onFiles: (files: File[]) => void
}

export function UploadDropzone({ uploading, onFiles }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const handleFiles = (list: FileList | null) => {
    if (list && list.length) onFiles(Array.from(list))
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      className={`flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed px-4 py-5 text-center transition ${
        dragging ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 hover:border-indigo-300 hover:bg-slate-50'
      }`}
    >
      {uploading ? (
        <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
      ) : (
        <Upload className="h-6 w-6 text-indigo-500" />
      )}
      <p className="text-sm font-medium text-slate-700">{uploading ? 'Uploading...' : 'Drop files or click to upload'}</p>
      <p className="text-xs text-slate-500">PDF, DOCX, TXT or Markdown</p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        multiple
        hidden
        onChange={(e) => {
          handleFiles(e.target.files)
          e.target.value = ''
        }}
      />
    </div>
  )
}
