interface MetricCardProps {
  title: string
  value: string | number
  trend?: 'up' | 'down' | 'flat'
  trendValue?: string
}

export default function MetricCard({ title, value, trend, trendValue }: MetricCardProps) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-400">{title}</h3>
      <div className="flex items-end justify-between mt-2">
        <p className="text-3xl font-bold text-cyan-400">{value}</p>
        {trend && (
          <span className={`text-sm ${trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </span>
        )}
      </div>
    </div>
  )
}