import { fetchEventSource } from '@microsoft/fetch-event-source'
import { API_BASE_URL } from '../utils/constants'
import type { SSEEvent } from '../types/chat'

export async function streamChat(
  sessionId: string,
  message: string,
  apiKey: string,
  onEvent: (event: SSEEvent) => void,
): Promise<void> {
  await fetchEventSource(`${API_BASE_URL}/api/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, api_key: apiKey }),
    openWhenHidden: true,
    onmessage(event) {
      if (!event.data) {
        return
      }
      onEvent(JSON.parse(event.data) as SSEEvent)
    },
    async onopen(response) {
      if (!response.ok) {
        throw new Error(`Chat request failed with status ${response.status}`)
      }
    },
  })
}

export async function clearChat(sessionId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/chat`, {
    method: 'DELETE',
  })
}
