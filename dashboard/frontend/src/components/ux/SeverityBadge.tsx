interface SeverityBadgeProps {
  severity: string
}

const SEVERITY_STYLES: Record<string, string> = {
  P1: 'bg-red-500/20 text-red-400 border-red-500/30',
  CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/30',
  P2: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  P3: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  MEDIUM: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  P4: 'bg-green-500/20 text-green-400 border-green-500/30',
  LOW: 'bg-green-500/20 text-green-400 border-green-500/30',
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const style = SEVERITY_STYLES[severity] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold border ${style}`}>
      {severity}
    </span>
  )
}
