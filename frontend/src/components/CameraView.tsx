import { useEffect, useRef, useState, useCallback } from 'react'
import { CameraSource } from '../App'
import { connectWebSocket, disconnectWebSocket } from '../services/webrtc'
import { getSessionStatus, stopSession, SessionStatus } from '../services/api'
import './CameraView.css'

interface CameraViewProps {
  sessionId: string
  source: CameraSource
  onStop: () => void
}

interface Detection {
  x: number
  y: number
  width: number
  height: number
  confidence: number
  class_name: string
}

interface SegmentationMask {
  mask_data: string  // Base64 encoded PNG
  width: number
  height: number
  confidence: number
  bbox: Detection
  area: number
}

function CameraView({ sessionId, source, onStop }: CameraViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [status, setStatus] = useState<SessionStatus | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])
  const [masks, setMasks] = useState<SegmentationMask[]>([])
  const [fps, setFps] = useState(0)
  const [latency, setLatency] = useState(0)
  const animationFrameRef = useRef<number>()
  const maskImagesRef = useRef<Map<number, HTMLImageElement>>(new Map())

  // Initialize webcam or WebSocket connection
  useEffect(() => {
    let stream: MediaStream | null = null
    let ws: WebSocket | null = null

    const initializeCamera = async () => {
      if (source === 'webcam' && videoRef.current) {
        try {
          // Get webcam stream
          stream = await navigator.mediaDevices.getUserMedia({
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              frameRate: { ideal: 30 },
            },
            audio: false,
          })
          
          videoRef.current.srcObject = stream
          await videoRef.current.play()
        } catch (error) {
          console.error('Failed to access webcam:', error)
        }
      }

      // Connect to WebSocket for inference results
      ws = connectWebSocket(sessionId, (data) => {
        if (data.detections) {
          setDetections(data.detections)
        }
        if (data.masks) {
          setMasks(data.masks)
          // Preload mask images
          data.masks.forEach((mask: SegmentationMask, idx: number) => {
            if (mask.mask_data) {
              const img = new Image()
              img.src = `data:image/png;base64,${mask.mask_data}`
              maskImagesRef.current.set(idx, img)
            }
          })
        }
        if (data.fps) {
          setFps(data.fps)
        }
        if (data.latency_ms) {
          setLatency(data.latency_ms)
        }
      })
    }

    initializeCamera()

    return () => {
      // Cleanup
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
      if (ws) {
        disconnectWebSocket()
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [sessionId, source])

  // Poll for session status
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const statusData = await getSessionStatus(sessionId)
        setStatus(statusData)
      } catch (error) {
        console.error('Failed to get session status:', error)
      }
    }

    pollStatus()
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [sessionId])

  // Poll for demo masks (shows masks immediately for testing)
  useEffect(() => {
    const fetchDemoMasks = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/inference/demo-masks', {
          method: 'POST'
        })
        const data = await response.json()
        
        if (data.masks) {
          setMasks(data.masks)
          // Preload mask images
          data.masks.forEach((mask: SegmentationMask, idx: number) => {
            if (mask.mask_data) {
              const img = new Image()
              img.src = `data:image/png;base64,${mask.mask_data}`
              img.onload = () => {
                maskImagesRef.current.set(idx, img)
              }
            }
          })
        }
      } catch (error) {
        console.error('Failed to fetch demo masks:', error)
      }
    }

    // Fetch every 2 seconds to show changing masks
    fetchDemoMasks()
    const interval = setInterval(fetchDemoMasks, 2000)

    return () => clearInterval(interval)
  }, [])

  // Draw segmentation masks on canvas
  const drawDetections = useCallback(() => {
    const video = videoRef.current
    const canvas = canvasRef.current
    
    if (!video || !canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Match canvas size to video
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
    }

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw segmentation masks
    masks.forEach((mask, idx) => {
      const maskImg = maskImagesRef.current.get(idx)
      if (!maskImg || !maskImg.complete) return

      // Create temporary canvas for mask
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = mask.width
      tempCanvas.height = mask.height
      const tempCtx = tempCanvas.getContext('2d')
      if (!tempCtx) return

      // Draw mask
      tempCtx.drawImage(maskImg, 0, 0)
      const imageData = tempCtx.getImageData(0, 0, mask.width, mask.height)
      
      // Apply colored overlay where mask is present
      const colors = [
        [16, 185, 129],    // Green
        [59, 130, 246],    // Blue
        [239, 68, 68],     // Red
        [245, 158, 11],    // Orange
        [168, 85, 247],    // Purple
      ]
      const color = colors[idx % colors.length]
      
      for (let i = 0; i < imageData.data.length; i += 4) {
        if (imageData.data[i] > 128) {  // If mask pixel is white
          imageData.data[i] = color[0]       // R
          imageData.data[i + 1] = color[1]   // G
          imageData.data[i + 2] = color[2]   // B
          imageData.data[i + 3] = 128        // Semi-transparent
        } else {
          imageData.data[i + 3] = 0  // Fully transparent
        }
      }
      
      tempCtx.putImageData(imageData, 0, 0)
      
      // Scale and draw overlay on main canvas
      ctx.drawImage(tempCanvas, 0, 0, canvas.width, canvas.height)

      // Draw bounding box outline
      const bbox = mask.bbox
      const x = bbox.x * canvas.width
      const y = bbox.y * canvas.height
      const w = bbox.width * canvas.width
      const h = bbox.height * canvas.height

      ctx.strokeStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`
      ctx.lineWidth = 2
      ctx.strokeRect(x, y, w, h)

      // Draw confidence label
      const label = `${(mask.confidence * 100).toFixed(0)}%`
      ctx.font = '14px sans-serif'
      const textWidth = ctx.measureText(label).width
      
      ctx.fillStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.8)`
      ctx.fillRect(x, y - 22, textWidth + 8, 22)

      ctx.fillStyle = '#ffffff'
      ctx.fillText(label, x + 4, y - 6)
    })

    // Also draw bounding boxes if available (for backward compatibility)
    detections.forEach((det) => {
      const x = det.x * canvas.width
      const y = det.y * canvas.height
      const w = det.width * canvas.width
      const h = det.height * canvas.height

      ctx.strokeStyle = '#10b981'
      ctx.lineWidth = 2
      ctx.strokeRect(x, y, w, h)
    })

    animationFrameRef.current = requestAnimationFrame(drawDetections)
  }, [masks, detections])

  useEffect(() => {
    drawDetections()
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [drawDetections])

  const handleStop = async () => {
    try {
      await stopSession(sessionId)
    } catch (error) {
      console.error('Failed to stop session:', error)
    }
    onStop()
  }

  return (
    <div className="camera-view">
      <div className="camera-header">
        <div className="camera-info">
          <h2>
            {source === 'webcam' ? '🎬 Webcam' : '📹 IP Camera'}
          </h2>
          <span className={`status-badge ${status?.is_streaming ? 'streaming' : 'stopped'}`}>
            {status?.is_streaming ? '● Streaming' : '○ Stopped'}
          </span>
        </div>
        <button className="btn btn-danger" onClick={handleStop}>
          Stop
        </button>
      </div>

      <div className="video-container">
        <video
          ref={videoRef}
          className="video-feed"
          autoPlay
          playsInline
          muted
        />
        <canvas
          ref={canvasRef}
          className="detection-overlay"
        />
      </div>

      <div className="metrics-panel">
        <div className="metric">
          <span className="metric-label">FPS</span>
          <span className="metric-value">{status?.current_fps?.toFixed(1) || fps.toFixed(1) || '0.0'}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Latency</span>
          <span className="metric-value">{status?.avg_latency_ms?.toFixed(0) || latency.toFixed(0) || '0'} ms</span>
        </div>
        <div className="metric">
          <span className="metric-label">Frames</span>
          <span className="metric-value">{status?.frames_processed || 0}</span>
        </div>
        <div className="metric">
          <span className="metric-label">Masks</span>
          <span className="metric-value">{masks.length}</span>
        </div>
      </div>

      {masks.length > 0 && (
        <div className="detections-list">
          <h3>Segmentation Masks</h3>
          <div className="detection-items">
            {masks.map((mask, idx) => (
              <div key={idx} className="detection-item">
                <span className="detection-class">Mask {idx + 1}</span>
                <span className="detection-confidence">
                  {(mask.confidence * 100).toFixed(0)}% • {mask.area.toLocaleString()}px
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default CameraView

