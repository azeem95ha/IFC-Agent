import { create } from 'zustand'
import { startTransition } from 'react'
import axios from 'axios'
import { clearChat as clearChatApi, streamChat } from '../api/chat'
import { downloadModel as downloadModelApi, removeModel as removeModelApi, uploadFile as uploadFileApi } from '../api/files'
import { createSession, deleteSession, getSession } from '../api/sessions'
import type { Message, SSEEvent } from '../types/chat'
import type { ModelInfo } from '../types/session'
import { LOCAL_SESSION_KEY, SESSION_STORAGE_KEY } from '../utils/constants'

interface AppStore {
  sessionId: string | null
  initSession: () => Promise<void>
  clearSession: () => Promise<void>
  apiKey: string
  setApiKey: (key: string) => void
  modelInfo: ModelInfo | null
  isUploading: boolean
  uploadFile: (file: File) => Promise<void>
  downloadModel: () => Promise<void>
  removeModel: () => Promise<void>
  messages: Message[]
  isStreaming: boolean
  sendMessage: (text: string) => Promise<void>
  clearChat: () => Promise<void>
  error: string | null
  setError: (message: string | null) => void
}

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function createAssistantMessage(): Message {
  return {
    id: createId(),
    role: 'assistant',
    content: '',
    thinking: [],
    toolCalls: [],
    createdAt: new Date(),
  }
}

function upsertAssistantEvent(messages: Message[], assistantId: string, event: SSEEvent): Message[] {
  return messages.map((message) => {
    if (message.id !== assistantId) {
      return message
    }

    const nextThinking = [...(message.thinking ?? [])]
    const nextToolCalls = [...(message.toolCalls ?? [])]

    switch (event.type) {
      case 'thinking':
        nextThinking.push(event.content)
        return { ...message, thinking: nextThinking }
      case 'tool_call':
        nextToolCalls.push({ tool: event.tool, input: event.input })
        return { ...message, toolCalls: nextToolCalls }
      case 'tool_result': {
        const toolIndex = [...nextToolCalls].reverse().findIndex((item) => item.tool === event.tool && item.output === undefined)
        if (toolIndex >= 0) {
          const resolvedIndex = nextToolCalls.length - 1 - toolIndex
          nextToolCalls[resolvedIndex] = { ...nextToolCalls[resolvedIndex], output: event.output }
        } else {
          nextToolCalls.push({ tool: event.tool, input: {}, output: event.output })
        }
        return { ...message, toolCalls: nextToolCalls }
      }
      case 'message':
        return { ...message, content: event.content }
      case 'error':
        return { ...message, content: event.message }
      case 'done':
        return message
      default:
        return message
    }
  })
}

async function ensureSession(): Promise<string> {
  const existing = localStorage.getItem(LOCAL_SESSION_KEY)
  if (existing) {
    try {
      await getSession(existing)
      return existing
    } catch (error) {
      if (!axios.isAxiosError(error) || error.response?.status !== 404) {
        throw error
      }
    }
  }

  const created = await createSession()
  localStorage.setItem(LOCAL_SESSION_KEY, created.session_id)
  return created.session_id
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export const useAppStore = create<AppStore>((set, get) => ({
  sessionId: null,
  apiKey: sessionStorage.getItem(SESSION_STORAGE_KEY) ?? '',
  modelInfo: null,
  isUploading: false,
  messages: [],
  isStreaming: false,
  error: null,

  setApiKey: (key) => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, key)
    set({ apiKey: key })
  },

  setError: (message) => set({ error: message }),

  initSession: async () => {
    const sessionId = await ensureSession()
    const meta = await getSession(sessionId)
    startTransition(() => {
      set({
        sessionId,
        modelInfo: meta.has_model && meta.ifc_filename
          ? { filename: meta.ifc_filename, size_bytes: 0, schema: 'Unknown', entity_count: 0 }
          : null,
        error: null,
      })
    })
  },

  clearSession: async () => {
    const current = get().sessionId
    if (current) {
      await deleteSession(current)
    }
    const created = await createSession()
    localStorage.setItem(LOCAL_SESSION_KEY, created.session_id)
    set({
      sessionId: created.session_id,
      modelInfo: null,
      messages: [],
      isStreaming: false,
      error: null,
    })
  },

  uploadFile: async (file) => {
    const sessionId = get().sessionId ?? (await ensureSession())
    set({ isUploading: true, error: null })
    try {
      const modelInfo = await uploadFileApi(sessionId, file)
      set({ sessionId, modelInfo })
    } finally {
      set({ isUploading: false })
    }
  },

  downloadModel: async () => {
    const { sessionId, modelInfo } = get()
    if (!sessionId) {
      throw new Error('No active session')
    }
    const blob = await downloadModelApi(sessionId)
    triggerDownload(blob, modelInfo?.filename ?? 'model.ifc')
  },

  removeModel: async () => {
    const sessionId = get().sessionId
    if (!sessionId) {
      return
    }
    await removeModelApi(sessionId)
    set({ modelInfo: null })
  },

  sendMessage: async (text) => {
    const { sessionId, apiKey, isStreaming } = get()
    if (!sessionId) {
      throw new Error('No active session')
    }
    if (!apiKey.trim()) {
      throw new Error('Google API key is required')
    }
    if (isStreaming) {
      return
    }

    const userMessage: Message = {
      id: createId(),
      role: 'user',
      content: text,
      createdAt: new Date(),
    }
    const assistantMessage = createAssistantMessage()

    set((state) => ({
      isStreaming: true,
      error: null,
      messages: [...state.messages, userMessage, assistantMessage],
    }))

    try {
      await streamChat(sessionId, text, apiKey, (event) => {
        startTransition(() => {
          set((state) => ({
            messages: upsertAssistantEvent(state.messages, assistantMessage.id, event),
          }))
        })
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Streaming failed'
      set((state) => ({
        error: message,
        messages: upsertAssistantEvent(state.messages, assistantMessage.id, { type: 'error', message }),
      }))
    } finally {
      set({ isStreaming: false })
    }
  },

  clearChat: async () => {
    const sessionId = get().sessionId
    if (!sessionId) {
      return
    }
    await clearChatApi(sessionId)
    set({ messages: [] })
  },
}))
