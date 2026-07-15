interface BarChartProps {
  data: Array<{ name: string; value: number; color?: string }>
  title: string
  height?: number
}

export default function BarChart({ data, title }: BarChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
        <div className="h-[200px] flex items-center justify-center text-gray-500">No data available</div>
      </div>
    )
  }
  const maxValue = Math.max(...data.map(d => d.value))
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
      <div className="h-[200px] flex items-end gap-2">
        {data.map((item, i) => (
          <div key={i} className="flex-1 flex flex-col items-center">
            <span className="text-xs text-gray-400 mb-1">{item.value}</span>
            <div
              className="w-full rounded-t transition-all"
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                backgroundColor: item.color || '#22d3ee',
              }}
            />
            <span className="text-xs text-gray-500 mt-1 truncate w-full text-center">{item.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}