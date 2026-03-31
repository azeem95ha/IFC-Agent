import type { ToolCallEvent } from '../../types/chat'
import { Accordion } from '../ui/accordion'

export function ToolCallAccordion({ toolCall }: { toolCall: ToolCallEvent }) {
  return (
    <Accordion title={`Tool: ${toolCall.tool}`}>
      <div className="space-y-3 font-mono text-xs text-[var(--foreground)]">
        <div>
          <div className="mb-1 text-[10px] uppercase tracking-[0.18em] text-[var(--muted)]">Input</div>
          <pre className="whitespace-pre-wrap rounded-xl bg-[var(--accent-soft)] p-3">{JSON.stringify(toolCall.input, null, 2)}</pre>
        </div>
        {toolCall.output ? (
          <div>
            <div className="mb-1 text-[10px] uppercase tracking-[0.18em] text-[var(--muted)]">Output</div>
            <pre className="whitespace-pre-wrap rounded-xl bg-[var(--accent-soft)] p-3">{toolCall.output}</pre>
          </div>
        ) : null}
      </div>
    </Accordion>
  )
}
