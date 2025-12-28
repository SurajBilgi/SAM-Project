import { useState, useEffect } from 'react'
import CameraView from './components/CameraView'
import IPCameraForm from './components/IPCameraForm'
import { createSession, SessionConfig } from './services/api'
import './App.css'

export type CameraSource = 'webcam' | 'ip-camera'

function App() {
  const [activeSource, setActiveSource] = useState<CameraSource>('webcam')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'Real-Time Vision Platform'
  }, [])

  const handleStartWebcam = async () => {
    setIsConnecting(true)
    setError(null)

    try {
      // Create session for webcam
      const config: SessionConfig = {
        camera: {
          camera_id: 'webcam-0',
          camera_type: 'webcam',
          fps: 30,
          resolution: '1280x720',
        },
        enable_inference: true,
        max_latency_ms: 200,
      }

      const session = await createSession(config)
      setSessionId(session.session_id)
      setActiveSource('webcam')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start webcam')
      console.error('Failed to start webcam:', err)
    } finally {
      setIsConnecting(false)
    }
  }

  const handleStartIPCamera = async (url: string, username?: string, password?: string) => {
    setIsConnecting(true)
    setError(null)

    try {
      // Determine camera type from URL
      const cameraType = url.startsWith('rtsp://') || url.startsWith('rtsps://') 
        ? 'rtsp' 
        : 'http'

      // Create session for IP camera
      const config: SessionConfig = {
        camera: {
          camera_id: `camera-${Date.now()}`,
          camera_type: cameraType,
          url,
          username,
          password,
          fps: 30,
          resolution: '1280x720',
        },
        enable_inference: true,
        max_latency_ms: 200,
      }

      const session = await createSession(config)
      setSessionId(session.session_id)
      setActiveSource('ip-camera')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to IP camera')
      console.error('Failed to start IP camera:', err)
    } finally {
      setIsConnecting(false)
    }
  }

  const handleStop = () => {
    setSessionId(null)
    setError(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🎥 Real-Time Vision Platform</h1>
          <p className="subtitle">Ultra-Low Latency Segmentation with SAM</p>
        </div>
      </header>

      <main className="app-main">
        {!sessionId ? (
          <div className="start-screen">
            <div className="source-selector">
              <h2>Select Camera Source</h2>
              
              <div className="source-options">
                <div className="source-option">
                  <h3>🎬 Webcam</h3>
                  <p>Use your device's built-in webcam</p>
                  <button
                    className="btn btn-primary"
                    onClick={handleStartWebcam}
                    disabled={isConnecting}
                  >
                    {isConnecting && activeSource === 'webcam' 
                      ? 'Connecting...' 
                      : 'Start Webcam'}
                  </button>
                </div>

                <div className="source-option">
                  <h3>📹 IP Camera</h3>
                  <p>Connect to RTSP or HTTP camera stream</p>
                  <IPCameraForm
                    onSubmit={handleStartIPCamera}
                    isConnecting={isConnecting && activeSource === 'ip-camera'}
                  />
                </div>
              </div>

              {error && (
                <div className="error-message">
                  <strong>Error:</strong> {error}
                </div>
              )}
            </div>
          </div>
        ) : (
          <CameraView 
            sessionId={sessionId} 
            source={activeSource}
            onStop={handleStop}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>
          Built with React + TypeScript • FastAPI • PyTorch • WebRTC
        </p>
      </footer>
    </div>
  )
}

export default App

