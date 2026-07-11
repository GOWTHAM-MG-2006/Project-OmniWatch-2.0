interface LineChartProps {
  data: Array<{ name: string; value: number }>
  title: string
  color?: string
  height?: number
}

export default function LineChart({ data, title, color = '#22d3ee', height = 200 }: LineChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
        <div className="h-[200px] flex items-center justify-center text-gray-500">No data available</div>
      </div>
    )
  }
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
      <div className="h-[200px]">
        {/* Recharts LineChart would render here */}
        <div className="h-full flex items-end gap-1">
          {data.map((item, i) => (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t"
                style={{
                  height: `${(item.value / Math.max(...data.map(d => d.value))) * 100}%`,
                  backgroundColor: color,
                  opacity: 0.8,
                }}
              />
              <span className="text-xs text-gray-500 mt-1 truncate w-full text-center">{item.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}