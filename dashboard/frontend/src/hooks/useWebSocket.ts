import { useState, useEffect, useCallback, useRef } from 'react'

interface UseWebSocketOptions {
  reconnectAttempts?: number
  reconnectInterval?: number
  onMessage?: (data: MessageEvent) => void
}

interface UseWebSocketResult {
  connected: boolean
  lastMessage: MessageEvent | null
  send: (data: string) => void
  reconnect: () => void
}

export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {},
): UseWebSocketResult {
  const { reconnectAttempts = 5, reconnectInterval = 3000, onMessage } = options
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const attemptsRef = useRef(0)
  const mountedRef = useRef(true)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const buildUrl = useCallback(() => {
    const token = localStorage.getItem('auth_token')
    const wsBase = url.startsWith('ws') ? url : `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}${url}`
    if (token) {
      const separator = wsBase.includes('?') ? '&' : '?'
      return `${wsBase}${separator}token=${token}`
    }
    return wsBase
  }, [url])

  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    try {
      const ws = new WebSocket(buildUrl())
      wsRef.current = ws

      ws.onopen = () => {
        if (mountedRef.current) {
          setConnected(true)
          attemptsRef.current = 0
        }
      }

      ws.onmessage = (event) => {
        if (mountedRef.current) {
          setLastMessage(event)
          onMessageRef.current?.(event)
        }
      }

      ws.onclose = () => {
        if (mountedRef.current) {
          setConnected(false)
          if (attemptsRef.current < reconnectAttempts) {
            attemptsRef.current += 1
            setTimeout(connect, reconnectInterval)
          }
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      if (mountedRef.current && attemptsRef.current < reconnectAttempts) {
        attemptsRef.current += 1
        setTimeout(connect, reconnectInterval)
      }
    }
  }, [buildUrl, reconnectAttempts, reconnectInterval])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      attemptsRef.current = reconnectAttempts
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect, reconnectAttempts])

  const send = useCallback((data: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
    }
  }, [])

  const reconnect = useCallback(() => {
    attemptsRef.current = 0
    connect()
  }, [connect])

  return { connected, lastMessage, send, reconnect }
}
