interface SeverityBadgeProps {
  severity: 'P1' | 'P2' | 'P3' | 'P4' | string
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const colors: Record<string, string> = {
    P1: 'bg-red-600',
    P2: 'bg-orange-600',
    P3: 'bg-yellow-600',
    P4: 'bg-blue-600',
    CRITICAL: 'bg-red-600',
    HIGH: 'bg-orange-600',
    MEDIUM: 'bg-yellow-600',
    LOW: 'bg-blue-600',
  }
  return (
    <span className={`px-2 py-0.5 text-xs font-bold rounded ${colors[severity] || 'bg-gray-600'}`}>
      {severity}
    </span>
  )
}