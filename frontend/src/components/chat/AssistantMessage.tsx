import type { Message } from '../../types/chat'
import { formatDate } from '../../utils/formatters'
import { MarkdownContent } from './MarkdownContent'
import { ThinkingAccordion } from './ThinkingAccordion'
import { ToolCallAccordion } from './ToolCallAccordion'

export function AssistantMessage({ message }: { message: Message }) {
  return (
    <article className="max-w-[85%] rounded-[26px] rounded-bl-md border border-[var(--border)] bg-white/78 px-4 py-4 shadow-[0_12px_28px_rgba(84,56,31,0.08)]">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent-strong)]">Assistant</span>
        <span className="text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]">{formatDate(message.createdAt)}</span>
      </div>
      <div className="space-y-3">
        {message.thinking?.length ? <ThinkingAccordion thinking={message.thinking} /> : null}
        {message.toolCalls?.map((toolCall, index) => <ToolCallAccordion key={`${toolCall.tool}-${index}`} toolCall={toolCall} />)}
        <MarkdownContent content={message.content || '...'} />
      </div>
    </article>
  )
}
