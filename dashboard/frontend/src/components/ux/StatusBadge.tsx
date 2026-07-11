interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'down' | string
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colors: Record<string, string> = {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    down: 'bg-red-500',
  }
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full ${colors[status] || 'bg-gray-500'}`} />
      <span className="text-sm capitalize">{status}</span>
    </span>
  )
}