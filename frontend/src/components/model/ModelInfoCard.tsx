import { useAppStore } from '../../store/appStore'
import { formatBytes } from '../../utils/formatters'

export function ModelInfoCard() {
  const modelInfo = useAppStore((state) => state.modelInfo)

  if (!modelInfo) {
    return (
      <div className="rounded-2xl bg-white/55 px-4 py-3 text-sm text-[var(--muted)]">
        No IFC model loaded yet.
      </div>
    )
  }

  return (
    <div className="grid gap-2 rounded-[24px] bg-[var(--panel-strong)] px-4 py-4 text-sm shadow-[inset_0_0_0_1px_rgba(27,29,31,0.04)]">
      <div className="flex items-center justify-between gap-4"><span className="text-[var(--muted)]">File</span><span className="font-medium">{modelInfo.filename}</span></div>
      <div className="flex items-center justify-between gap-4"><span className="text-[var(--muted)]">Schema</span><span className="font-medium">{modelInfo.schema}</span></div>
      <div className="flex items-center justify-between gap-4"><span className="text-[var(--muted)]">Entities</span><span className="font-medium">{modelInfo.entity_count}</span></div>
      <div className="flex items-center justify-between gap-4"><span className="text-[var(--muted)]">Size</span><span className="font-medium">{formatBytes(modelInfo.size_bytes)}</span></div>
    </div>
  )
}
