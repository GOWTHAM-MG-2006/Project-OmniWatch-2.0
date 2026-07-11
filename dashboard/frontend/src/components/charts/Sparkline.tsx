interface SparklineProps {
  data: number[]
  color?: string
  height?: number
}

export default function Sparkline({ data, color = '#22d3ee', height = 40 }: SparklineProps) {
  if (!data || data.length === 0) return null
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  
  return (
    <svg width="100%" height={height} viewBox="0 0 100 40" preserveAspectRatio="none">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        points={data.map((v, i) => `${(i / (data.length - 1)) * 100},${40 - ((v - min) / range) * 35}`).join(' ')}
      />
    </svg>
  )
}