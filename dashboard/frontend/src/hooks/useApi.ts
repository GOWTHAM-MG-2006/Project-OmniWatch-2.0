import { useState, useEffect, useCallback, useRef } from 'react'

interface UseApiOptions extends RequestInit {
  immediate?: boolean
}

interface UseApiResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

interface UseApiPostResult<T, B> {
  data: T | null
  loading: boolean
  error: string | null
  execute: (body: B) => Promise<void>
}

export function useApi<T>(url: string, options: UseApiOptions = {}): UseApiResult<T> {
  const { immediate = true, ...fetchOptions } = options
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)
  const optionsRef = useRef(fetchOptions)

  // Keep ref in sync with latest options
  optionsRef.current = fetchOptions

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...((optionsRef.current.headers as Record<string, string>) ?? {}),
      }
      const res = await fetch(url, { ...optionsRef.current, headers })
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }
      const json: T = await res.json()
      if (mountedRef.current) {
        setData(json)
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }, [url]) // Only depend on url — options accessed via ref

  useEffect(() => {
    mountedRef.current = true
    if (immediate) {
      void fetchData()
    }
    return () => {
      mountedRef.current = false
    }
  }, [fetchData, immediate])

  return { data, loading, error, refetch: fetchData }
}

export function useApiPost<T, B>(url: string): UseApiPostResult<T, B> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    return () => {
      mountedRef.current = false
    }
  }, [])

  const execute = useCallback(
    async (body: B) => {
      setLoading(true)
      setError(null)
      try {
        const token = localStorage.getItem('auth_token')
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }
        const res = await fetch(url, {
          method: 'POST',
          headers,
          body: JSON.stringify(body),
        })
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`)
        }
        const json: T = await res.json()
        if (mountedRef.current) {
          setData(json)
        }
      } catch (err) {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : 'Unknown error')
        }
      } finally {
        if (mountedRef.current) {
          setLoading(false)
        }
      }
    },
    [url],
  )

  return { data, loading, error, execute }
}
