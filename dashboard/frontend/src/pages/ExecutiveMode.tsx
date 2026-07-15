import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import ErrorAlert from '../components/ux/ErrorAlert'
import MetricCard from '../components/ux/MetricCard'

interface SLOSummary {
  compliance_pct?: number
  slo_target?: number
  breaches?: number
  total_services?: number
}

interface MTTRData {
  mttr_minutes?: number
  mttr_target?: number
  incidents_resolved?: number
  period?: string
}

interface CostCarbon {
  hourly_cost_usd?: number
  daily_cost_usd?: number
  carbon_grams_per_hour?: number
  revenue_at_risk_usd?: number
  cost_trend?: Array<{ timestamp: string; cost: number }>
}

const TIME_RANGES = [
  { label: '1h', value: '1h' },
  { label: '24h', value: '24h' },
  { label: '7d', value: '7d' },
  { label: '30d', value: '30d' },
] as const

type TimeRange = typeof TIME_RANGES[number]['value']



export default function ExecutiveMode() {
  const [timeRange, setTimeRange] = useState<TimeRange>('24h')

  const { data: sloData, loading: sloLoading, error: sloError } = useApi<SLOSummary>(
    `/api/v1/metrics/summary?range=${timeRange}`
  )
  const { data: mttrData, loading: mttrLoading, error: mttrError } = useApi<MTTRData>(
    `/api/v1/reports/mttr?range=${timeRange}`
  )
  const { data: costData, loading: costLoading, error: costError } = useApi<CostCarbon>(
    `/api/v1/metrics/cost-carbon?range=${timeRange}`
  )

  const loading = sloLoading || mttrLoading || costLoading
  const error = sloError || mttrError || costError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Executive Mode</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((idx) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-28 animate-pulse" />
          ))}
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-64 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Executive Mode</h1>
        </div>
        <ErrorAlert message={`Failed to load executive data: ${error}`} />
      </div>
    )
  }

  const slo = sloData ?? {}
  const mttr = mttrData ?? {}
  const cost = costData ?? {}

  const compliance = slo.compliance_pct != null ? `${slo.compliance_pct.toFixed(1)}%` : '--'
  const mttrMin = mttr.mttr_minutes != null ? `${mttr.mttr_minutes}m` : '--'
  const hourlyCost = cost.hourly_cost_usd != null ? `$${cost.hourly_cost_usd.toFixed(2)}` : '--'
  const revenueAtRisk = cost.revenue_at_risk_usd != null ? `$${cost.revenue_at_risk_usd.toLocaleString()}` : '$0'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Executive Mode</h1>
          <p className="text-gray-400 text-sm">SLO compliance, revenue impact, cost &amp; carbon tracking.</p>
        </div>
        <div className="flex gap-1 bg-gray-900 rounded-lg p-1 border border-gray-700">
          {TIME_RANGES.map((tr) => (
            <button
              key={tr.value}
              onClick={() => setTimeRange(tr.value)}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                timeRange === tr.value
                  ? 'bg-cyan-600 text-white'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              {tr.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="SLO Compliance" value={compliance} />
        <MetricCard title="MTTR" value={mttrMin} />
        <MetricCard title="Hourly Cost" value={hourlyCost} />
        <MetricCard title="Revenue at Risk" value={revenueAtRisk} />
      </div>

      {/* Cost Trend Chart Placeholder */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold">Cost Trend</h2>
        </div>
        <div className="p-8 flex items-center justify-center h-64">
          <div className="text-center text-gray-500">
            <div className="text-4xl mb-2">📊</div>
            <p className="text-sm">Cost trend chart coming soon</p>
            <p className="text-xs text-gray-600 mt-1">Requires Recharts integration</p>
          </div>
        </div>
      </div>
    </div>
  )
}
