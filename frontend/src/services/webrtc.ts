/**
 * WebSocket service for real-time communication.
 * 
 * Handles:
 * - WebSocket connection management
 * - Inference results streaming
 * - Auto-reconnection
 */

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

let websocket: WebSocket | null = null
let reconnectAttempts = 0
let reconnectTimer: number | null = null
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 2000

type MessageHandler = (data: any) => void
let messageHandler: MessageHandler | null = null

/**
 * Connect to WebSocket for a session.
 */
export function connectWebSocket(sessionId: string, onMessage: MessageHandler): WebSocket {
  // Close existing connection
  if (websocket) {
    disconnectWebSocket()
  }

  messageHandler = onMessage

  const wsUrl = `${WS_BASE_URL}/ws/${sessionId}`
  console.log(`Connecting to WebSocket: ${wsUrl}`)

  websocket = new WebSocket(wsUrl)

  websocket.onopen = () => {
    console.log('WebSocket connected')
    reconnectAttempts = 0
    
    // Clear any pending reconnect timer
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.error) {
        console.error('WebSocket error:', data.error)
        return
      }

      if (messageHandler) {
        messageHandler(data)
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  websocket.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  websocket.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason)
    websocket = null

    // Attempt to reconnect if not intentionally closed
    if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++
      console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`)
      
      reconnectTimer = window.setTimeout(() => {
        if (messageHandler) {
          connectWebSocket(sessionId, messageHandler)
        }
      }, RECONNECT_DELAY)
    } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max reconnection attempts reached')
    }
  }

  return websocket
}

/**
 * Disconnect from WebSocket.
 */
export function disconnectWebSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  if (websocket) {
    reconnectAttempts = MAX_RECONNECT_ATTEMPTS // Prevent auto-reconnect
    websocket.close(1000, 'Client disconnect')
    websocket = null
  }

  messageHandler = null
  console.log('WebSocket disconnected')
}

/**
 * Send a message through WebSocket.
 */
export function sendMessage(data: any) {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify(data))
  } else {
    console.warn('WebSocket not connected')
  }
}

/**
 * Get current WebSocket connection state.
 */
export function getConnectionState(): string {
  if (!websocket) return 'CLOSED'
  
  switch (websocket.readyState) {
    case WebSocket.CONNECTING:
      return 'CONNECTING'
    case WebSocket.OPEN:
      return 'OPEN'
    case WebSocket.CLOSING:
      return 'CLOSING'
    case WebSocket.CLOSED:
      return 'CLOSED'
    default:
      return 'UNKNOWN'
  }
}

