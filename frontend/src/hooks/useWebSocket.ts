import { useEffect, useRef, useState, useCallback } from 'react'
import { WebSocketMessage } from '../types'

interface UseWebSocketOptions {
  batchId?: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { batchId, onMessage, onConnect, onDisconnect } = options
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/batch-progress`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      onConnect?.()

      // Subscribe to batch if specified
      if (batchId) {
        ws.send(JSON.stringify({ type: 'subscribe', batch_id: batchId }))
      }
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        setLastMessage(message)
        onMessage?.(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      onDisconnect?.()
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    // Keepalive ping
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)

    return () => {
      clearInterval(pingInterval)
      ws.close()
    }
  }, [batchId, onConnect, onDisconnect, onMessage])

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const subscribeToBatch = useCallback((newBatchId: string) => {
    sendMessage({ type: 'subscribe', batch_id: newBatchId })
  }, [sendMessage])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    subscribeToBatch,
  }
}
