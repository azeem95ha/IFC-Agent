import { Accordion } from '../ui/accordion'

export function ThinkingAccordion({ thinking }: { thinking: string[] }) {
  return (
    <Accordion title="Reasoning trace" defaultOpen={false}>
      <div className="space-y-2 font-mono text-xs text-[var(--foreground)]">
        {thinking.map((item, index) => (
          <pre key={`${item}-${index}`} className="whitespace-pre-wrap rounded-xl bg-[var(--accent-soft)] p-3">{item}</pre>
        ))}
      </div>
    </Accordion>
  )
}
