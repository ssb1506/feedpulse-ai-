import { useEffect, useRef, useState, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_URL = API_BASE.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws/feed'

export default function useWebSocket() {
  const [posts, setPosts] = useState([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        console.log('[WS] Connected to live feed')
      }

      ws.onmessage = (event) => {
        try {
          const post = JSON.parse(event.data)
          setPosts((prev) => [post, ...prev].slice(0, 100)) // keep last 100
        } catch (e) {
          console.error('[WS] Parse error:', e)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        console.log('[WS] Disconnected. Reconnecting in 3s...')
        reconnectTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = (err) => {
        console.error('[WS] Error:', err)
        ws.close()
      }
    } catch (e) {
      console.error('[WS] Connection failed:', e)
      reconnectTimer.current = setTimeout(connect, 3000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  return { posts, connected }
}
