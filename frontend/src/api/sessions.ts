import { client } from './client'
import type { SessionMeta } from '../types/session'

export async function createSession(): Promise<{ session_id: string }> {
  const { data } = await client.post<{ session_id: string }>('/api/sessions')
  return data
}

export async function getSession(sessionId: string): Promise<SessionMeta> {
  const { data } = await client.get<SessionMeta>(`/api/sessions/${sessionId}`)
  return data
}

export async function deleteSession(sessionId: string): Promise<void> {
  await client.delete(`/api/sessions/${sessionId}`)
}
