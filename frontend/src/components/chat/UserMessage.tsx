import type { Message } from '../../types/chat'
import { formatDate } from '../../utils/formatters'

export function UserMessage({ message }: { message: Message }) {
  return (
    <article className="ml-auto max-w-[75%] rounded-[26px] rounded-br-md bg-[var(--accent)] px-4 py-3 text-sm text-white shadow-[0_16px_32px_rgba(198,93,46,0.22)]">
      <div>{message.content}</div>
      <div className="mt-2 text-right text-[11px] uppercase tracking-[0.16em] text-white/70">{formatDate(message.createdAt)}</div>
    </article>
  )
}
