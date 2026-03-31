import { Badge } from '../ui/primitives'
import { useAppStore } from '../../store/appStore'

export function TopBar() {
  const sessionId = useAppStore((state) => state.sessionId)

  return (
    <header className="flex items-center justify-between rounded-[30px] border border-[var(--border)] bg-[var(--panel)] px-6 py-4 shadow-[var(--shadow)] backdrop-blur-sm">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[var(--accent-strong)]">IFC Translator V4</p>
        <h1 className="text-2xl font-semibold">IFC AI Assistant</h1>
      </div>
      <Badge>{sessionId ? `Session ${sessionId.slice(0, 8)}` : 'Booting'}</Badge>
    </header>
  )
}
