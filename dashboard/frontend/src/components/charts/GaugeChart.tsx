interface GaugeChartProps {
  value: number
  max?: number
  title: string
  color?: string
}

export default function GaugeChart({ value, max = 100, title, color }: GaugeChartProps) {
  const percentage = (value / max) * 100
  const gaugeColor = color || (percentage >= 80 ? '#22c55e' : percentage >= 60 ? '#eab308' : '#ef4444')
  
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
      <div className="flex items-center justify-center">
        <div className="relative w-32 h-32">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#374151" strokeWidth="8" />
            <circle
              cx="50" cy="50" r="40" fill="none"
              stroke={gaugeColor}
              strokeWidth="8"
              strokeDasharray={`${percentage * 2.51} 251`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold" style={{ color: gaugeColor }}>{value}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}