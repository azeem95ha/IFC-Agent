import { useState } from 'react'
import { SendHorizontal } from 'lucide-react'
import { useAppStore } from '../../store/appStore'
import { Button, Textarea } from '../ui/primitives'

export function ChatInput() {
  const [value, setValue] = useState('')
  const isStreaming = useAppStore((state) => state.isStreaming)
  const sendMessage = useAppStore((state) => state.sendMessage)
  const setError = useAppStore((state) => state.setError)

  async function onSubmit() {
    const trimmed = value.trim()
    if (!trimmed) {
      return
    }

    try {
      await sendMessage(trimmed)
      setValue('')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unable to send message')
    }
  }

  return (
    <div className="rounded-[28px] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
      <div className="flex items-end gap-3">
        <Textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          rows={3}
          placeholder="Ask about your IFC file..."
          disabled={isStreaming}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void onSubmit()
            }
          }}
        />
        <Button className="h-12 w-12 rounded-full p-0" onClick={() => void onSubmit()} disabled={isStreaming}>
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
