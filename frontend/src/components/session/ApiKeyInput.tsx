import { KeyRound } from 'lucide-react'
import { useAppStore } from '../../store/appStore'
import { Input } from '../ui/primitives'

export function ApiKeyInput() {
  const apiKey = useAppStore((state) => state.apiKey)
  const setApiKey = useAppStore((state) => state.setApiKey)

  return (
    <label className="grid gap-2 text-sm">
      <span className="flex items-center gap-2 font-medium">
        <KeyRound className="h-4 w-4 text-[var(--accent-strong)]" />
        Google API Key
      </span>
      <Input
        type="password"
        value={apiKey}
        onChange={(event) => setApiKey(event.target.value)}
        placeholder="AIza..."
      />
    </label>
  )
}
