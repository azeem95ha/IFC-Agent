import { Trash2, UploadCloud } from 'lucide-react'
import { useRef } from 'react'
import { useAppStore } from '../../store/appStore'
import { formatBytes } from '../../utils/formatters'
import { Button, GhostButton } from '../ui/primitives'

export function FileUploader() {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const uploadFile = useAppStore((state) => state.uploadFile)
  const removeModel = useAppStore((state) => state.removeModel)
  const isUploading = useAppStore((state) => state.isUploading)
  const modelInfo = useAppStore((state) => state.modelInfo)
  const setError = useAppStore((state) => state.setError)

  async function handleFiles(fileList: FileList | null) {
    const file = fileList?.[0]
    if (!file) {
      return
    }

    try {
      await uploadFile(file)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed')
    }
  }

  return (
    <div className="space-y-3">
      <div
        className="rounded-[24px] border border-dashed border-[var(--accent)] bg-[var(--accent-soft)] p-4 text-sm text-[var(--foreground)]"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault()
          void handleFiles(event.dataTransfer.files)
        }}
      >
        <div className="flex items-start gap-3">
          <UploadCloud className="mt-0.5 h-5 w-5 text-[var(--accent-strong)]" />
          <div className="space-y-1">
            <p className="font-medium">Upload an IFC model</p>
            <p className="text-[var(--muted)]">Drag a `.ifc` file here or choose one from disk.</p>
            <Button className="mt-2" onClick={() => inputRef.current?.click()} disabled={isUploading}>
              {isUploading ? 'Uploading...' : 'Choose File'}
            </Button>
            <input
              ref={inputRef}
              type="file"
              accept=".ifc"
              className="hidden"
              onChange={(event) => void handleFiles(event.target.files)}
            />
          </div>
        </div>
      </div>
      {modelInfo ? (
        <div className="flex items-center justify-between rounded-2xl bg-white/70 px-4 py-3 text-sm">
          <div>
            <div className="font-medium">{modelInfo.filename}</div>
            <div className="text-[var(--muted)]">{formatBytes(modelInfo.size_bytes)}</div>
          </div>
          <GhostButton className="px-3 py-2" onClick={() => void removeModel()}>
            <Trash2 className="h-4 w-4" />
          </GhostButton>
        </div>
      ) : null}
    </div>
  )
}
