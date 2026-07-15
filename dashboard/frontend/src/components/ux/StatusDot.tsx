interface StatusDotProps {
  status: 'healthy' | 'degraded' | 'down' | string
}

const STATUS_COLORS: Record<string, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  down: 'bg-red-500',
}

export default function StatusDot({ status }: StatusDotProps) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${STATUS_COLORS[status] || 'bg-gray-500'}`}
      title={status}
    />
  )
}
