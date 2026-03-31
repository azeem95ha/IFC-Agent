import { MessageSquareOff, RefreshCw } from 'lucide-react'
import { useAppStore } from '../../store/appStore'
import { Button, GhostButton } from '../ui/primitives'

export function SessionControls() {
  const clearChat = useAppStore((state) => state.clearChat)
  const clearSession = useAppStore((state) => state.clearSession)
  const setError = useAppStore((state) => state.setError)

  return (
    <div className="grid gap-3">
      <GhostButton
        onClick={async () => {
          try {
            await clearChat()
          } catch (error) {
            setError(error instanceof Error ? error.message : 'Unable to clear chat')
          }
        }}
      >
        <MessageSquareOff className="h-4 w-4" />
        Clear Chat
      </GhostButton>
      <Button
        className="bg-[var(--success)] hover:bg-[var(--success)]/90"
        onClick={async () => {
          try {
            await clearSession()
          } catch (error) {
            setError(error instanceof Error ? error.message : 'Unable to create a new session')
          }
        }}
      >
        <RefreshCw className="h-4 w-4" />
        New Session
      </Button>
    </div>
  )
}
