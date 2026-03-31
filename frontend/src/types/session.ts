export interface SessionMeta {
  session_id: string
  has_model: boolean
  ifc_filename: string | null
  created_at: string
  last_active: string
}

export interface ModelInfo {
  filename: string
  size_bytes: number
  schema: string
  entity_count: number
}
