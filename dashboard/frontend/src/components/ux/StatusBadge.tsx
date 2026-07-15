interface StatusBadgeProps {
  status: string
}

const STATUS_STYLES: Record<string, string> = {
  healthy: 'bg-green-500/20 text-green-400 border-green-500/30',
  OPEN: 'bg-red-500/20 text-red-400 border-red-500/30',
  INVESTIGATING: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  RESOLVED: 'bg-green-500/20 text-green-400 border-green-500/30',
  MONITORING: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  degraded: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  down: 'bg-red-500/20 text-red-400 border-red-500/30',
  active: 'bg-green-500/20 text-green-400 border-green-500/30',
  pending: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${style}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === 'healthy' || status === 'RESOLVED' || status === 'active' ? 'bg-green-400' :
        status === 'degraded' || status === 'INVESTIGATING' || status === 'pending' ? 'bg-amber-400' :
        status === 'down' || status === 'OPEN' ? 'bg-red-400' : 'bg-blue-400'
      }`} />
      {status}
    </span>
  )
}
