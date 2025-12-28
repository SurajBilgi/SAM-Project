import { useState, FormEvent } from 'react'
import './IPCameraForm.css'

interface IPCameraFormProps {
  onSubmit: (url: string, username?: string, password?: string) => void
  isConnecting: boolean
}

function IPCameraForm({ onSubmit, isConnecting }: IPCameraFormProps) {
  const [url, setUrl] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showAuth, setShowAuth] = useState(false)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    
    if (!url.trim()) {
      alert('Please enter a valid URL')
      return
    }

    onSubmit(
      url.trim(),
      showAuth && username ? username : undefined,
      showAuth && password ? password : undefined
    )
  }

  return (
    <form className="ip-camera-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="camera-url">Camera URL</label>
        <input
          id="camera-url"
          type="text"
          placeholder="rtsp://192.168.1.100:554/stream"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="form-input"
          disabled={isConnecting}
        />
        <small className="form-help">
          Supports RTSP (rtsp://) and HTTP (http://) streams
        </small>
      </div>

      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={showAuth}
            onChange={(e) => setShowAuth(e.target.checked)}
            disabled={isConnecting}
          />
          <span>Requires authentication</span>
        </label>
      </div>

      {showAuth && (
        <>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              placeholder="admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="form-input"
              disabled={isConnecting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              disabled={isConnecting}
            />
          </div>
        </>
      )}

      <button
        type="submit"
        className="btn btn-primary"
        disabled={isConnecting || !url.trim()}
      >
        {isConnecting ? 'Connecting...' : 'Connect'}
      </button>
    </form>
  )
}

export default IPCameraForm

