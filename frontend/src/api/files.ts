import { client } from './client'
import type { ModelInfo } from '../types/session'

export async function uploadFile(sessionId: string, file: File): Promise<ModelInfo> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post<ModelInfo>(`/api/sessions/${sessionId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return data
}

export async function downloadModel(sessionId: string): Promise<Blob> {
  const { data } = await client.get<Blob>(`/api/sessions/${sessionId}/download`, {
    responseType: 'blob',
  })
  return data
}

export async function removeModel(sessionId: string): Promise<void> {
  await client.delete(`/api/sessions/${sessionId}/model`)
}
