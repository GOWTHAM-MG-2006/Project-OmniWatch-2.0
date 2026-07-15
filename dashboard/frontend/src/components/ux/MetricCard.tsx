interface MetricCardProps {
  title: string
  value: string | number
  trend?: 'up' | 'down' | 'flat'
  trendValue?: string
  icon?: string
  className?: string
}

export default function MetricCard({ title, value, trend, trendValue, icon, className = '' }: MetricCardProps) {
  return (
    <div className={`bg-[#1a1a2e] rounded-xl p-5 border border-[#2a2a3e] hover:border-[#7f5af0] transition-colors duration-200 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className="flex items-end justify-between mt-3">
        <p className="text-3xl font-bold text-cyan-400">{value}</p>
        {trend && (
          <span className={`text-sm font-medium ${
            trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'
          }`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </span>
        )}
      </div>
    </div>
  )
}
