export interface ToolCallEvent {
  tool: string
  input: Record<string, unknown>
  output?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string[]
  toolCalls?: ToolCallEvent[]
  createdAt: Date
}

export type SSEEvent =
  | { type: 'thinking'; content: string }
  | { type: 'tool_call'; tool: string; input: Record<string, unknown> }
  | { type: 'tool_result'; tool: string; output: string }
  | { type: 'message'; content: string }
  | { type: 'error'; message: string }
  | { type: 'done' }
