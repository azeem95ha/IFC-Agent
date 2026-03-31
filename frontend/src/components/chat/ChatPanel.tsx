import { useAppStore } from '../../store/appStore'
import { formatDate } from '../../utils/formatters'
import { ChatInput } from './ChatInput'
import { MessageList } from './MessageList'
import { Card } from '../ui/primitives'

export function ChatPanel() {
  const messages = useAppStore((state) => state.messages)
  const error = useAppStore((state) => state.error)
  const modelInfo = useAppStore((state) => state.modelInfo)

  return (
    <section className="flex min-h-[70vh] flex-col gap-5">
      <Card className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Conversation</p>
            <h2 className="text-lg font-semibold">Model dialogue</h2>
          </div>
          <div className="text-right text-xs text-[var(--muted)]">
            <div>{modelInfo ? `Loaded: ${modelInfo.filename}` : 'No model loaded'}</div>
            <div>{messages.length ? `Updated ${formatDate(messages[messages.length - 1].createdAt)}` : 'Waiting for first message'}</div>
          </div>
        </div>
        {error ? <div className="rounded-2xl bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div> : null}
        <MessageList messages={messages} />
      </Card>
      <ChatInput />
    </section>
  )
}
