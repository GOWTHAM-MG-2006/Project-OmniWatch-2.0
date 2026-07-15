import { useState, useEffect } from 'react'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
}

let toastId = 0
const listeners: Set<(toasts: ToastMessage[]) => void> = new Set()
let toasts: ToastMessage[] = []

function notify() {
  listeners.forEach((fn) => fn([...toasts]))
}

export function showToast(type: ToastMessage['type'], message: string) {
  const id = String(++toastId)
  toasts = [...toasts, { id, type, message }]
  notify()
  setTimeout(() => {
    toasts = toasts.filter((t) => t.id !== id)
    notify()
  }, 5000)
}

const typeStyles = {
  success: 'bg-green-900/80 border-green-500 text-green-200',
  error: 'bg-red-900/80 border-red-500 text-red-200',
  warning: 'bg-amber-900/80 border-amber-500 text-amber-200',
  info: 'bg-blue-900/80 border-blue-500 text-blue-200',
}

const typeIcons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' }

export default function ToastContainer() {
  const [items, setItems] = useState<ToastMessage[]>([])

  useEffect(() => {
    const listener = (t: ToastMessage[]) => setItems(t)
    listeners.add(listener)
    return () => { listeners.delete(listener) }
  }, [])

  if (items.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {items.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg animate-slide-in ${typeStyles[toast.type]}`}
        >
          <span className="text-lg font-bold">{typeIcons[toast.type]}</span>
          <span className="text-sm">{toast.message}</span>
        </div>
      ))}
    </div>
  )
}
