export interface RecommendRequest {
  movie_ids: number[]
}

export interface HealthResponse {
  status: string
  message?: string
}

export interface ModelInfoResponse {
  version?: string
  metrics?: Record<string, unknown>
  trained_at?: string
  [key: string]: unknown
}
