/**
 * API service for communicating with the backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface CameraConfig {
  camera_id: string
  camera_type: 'webcam' | 'rtsp' | 'http'
  url?: string
  username?: string
  password?: string
  fps?: number
  resolution?: string
}

export interface SessionConfig {
  camera: CameraConfig
  enable_inference: boolean
  max_latency_ms: number
}

export interface SessionResponse extends SessionConfig {
  session_id: string
  created_at: string
}

export interface SessionStatus {
  session_id: string
  camera_status: 'connected' | 'disconnected' | 'connecting' | 'error'
  is_streaming: boolean
  current_fps?: number
  avg_latency_ms?: number
  frames_processed: number
  errors: string[]
  last_updated: string
}

/**
 * Create a new vision session.
 */
export async function createSession(config: SessionConfig): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/session/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config.camera),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create session' }))
    throw new Error(error.detail || 'Failed to create session')
  }

  return response.json()
}

/**
 * Get session status.
 */
export async function getSessionStatus(sessionId: string): Promise<SessionStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/status`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get session status' }))
    throw new Error(error.detail || 'Failed to get session status')
  }

  return response.json()
}

/**
 * Start streaming for a session.
 */
export async function startSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/start`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to start session' }))
    throw new Error(error.detail || 'Failed to start session')
  }
}

/**
 * Stop streaming for a session.
 */
export async function stopSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}/stop`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to stop session' }))
    throw new Error(error.detail || 'Failed to stop session')
  }
}

/**
 * Delete a session.
 */
export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/session/${sessionId}`, {
    method: 'DELETE',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete session' }))
    throw new Error(error.detail || 'Failed to delete session')
  }
}

/**
 * Get API health status.
 */
export async function getHealthStatus(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error('Health check failed')
  }

  return response.json()
}

