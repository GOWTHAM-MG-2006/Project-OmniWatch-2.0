import { useState, useEffect } from 'react'
import { useApi, useWebSocket } from '../hooks'
import LoadingSkeleton from '../components/ux/LoadingSkeleton'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'
import MetricCard from '../components/ux/MetricCard'
import StatusBadge from '../components/ux/StatusBadge'
import SeverityBadge from '../components/ux/SeverityBadge'

interface Incident {
  incident_id: string
  severity: string
  status: string
  created_at: string
  root_cause?: string
  blast_radius?: number
  business_impact_score?: number
}

interface LayerInfo {
  status: string
  latency_ms?: number
}

interface SystemStatus {
  health: string
  layers: Record<string, LayerInfo>
}





export default function SREMode() {
  const { data: incidents, loading: incLoading, error: incError, refetch: refetchIncidents } =
    useApi<Incident[]>('/api/v1/incidents/')
  const { data: status, loading: statusLoading, error: statusError, refetch: refetchStatus } =
    useApi<SystemStatus>('/api/v1/status')
  const { connected } = useWebSocket('ws://localhost:8000/ws')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    void refreshKey
  }, [refreshKey])

  const handleRefresh = () => {
    refetchIncidents()
    refetchStatus()
    setRefreshKey((k: number) => k + 1)
  }

  if (incLoading || statusLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">SRE Mode</h1>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((idx: number) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-24 animate-pulse" />
          ))}
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-64 animate-pulse" />
      </div>
    )
  }

  if (incError || statusError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">SRE Mode</h1>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
          >
            Refresh
          </button>
        </div>
        <ErrorAlert message={`Failed to load data: ${incError || statusError}`} onRetry={handleRefresh} />
      </div>
    )
  }

  const incidentList = incidents ?? []
  const activeIncidents = incidentList.filter((inc: Incident) => inc.status === 'OPEN')
  const p1Count = activeIncidents.filter((inc: Incident) => inc.severity?.toUpperCase() === 'P1').length
  const p2Count = activeIncidents.filter((inc: Incident) => inc.severity?.toUpperCase() === 'P2').length
  const healthLabel = status?.health ?? 'Unknown'
  const layerEntries: Array<[string, LayerInfo]> = status?.layers
    ? Object.entries(status.layers) as Array<[string, LayerInfo]>
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">SRE Mode</h1>
          <p className="text-gray-400 text-sm">
            WebSocket: {connected ? (
              <span className="text-green-400">Connected</span>
            ) : (
              <span className="text-red-400">Disconnected</span>
            )}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Active Incidents" value={activeIncidents.length} />
        <MetricCard title="P1 Critical" value={p1Count} />
        <MetricCard title="P2 High" value={p2Count} />
        <MetricCard title="System Health" value={healthLabel} />
      </div>

      {/* Incident List */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold">Recent Incidents</h2>
        </div>
        {incidentList.length === 0 ? (
          <EmptyState title="No active incidents" description="All systems are operating normally." />
        ) : (
          <div className="divide-y divide-gray-700">
            {incidentList.slice(0, 20).map((inc: Incident) => (
              <div key={inc.incident_id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={inc.severity} />
                  <span className="font-mono text-sm">{inc.incident_id}</span>
                  <span className="text-gray-400 text-sm">{inc.root_cause ?? 'Unknown'}</span>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">{inc.status}</span>
                  {inc.blast_radius != null && (
                    <span className="ml-3 text-xs text-gray-500">{inc.blast_radius} affected</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Layer Status Grid */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold">Layer Status</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4">
          {layerEntries.length > 0 ? (
            layerEntries.map(([layer, info]: [string, LayerInfo]) => (
              <div key={layer} className="bg-gray-900 rounded p-3">
                <div className="text-xs text-gray-500 mb-1">{layer}</div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={info.status} />
                </div>
                {info.latency_ms != null && (
                  <div className="text-xs text-gray-500 mt-1">{info.latency_ms}ms</div>
                )}
              </div>
            ))
          ) : (
            <EmptyState title="No layer data" description="Layer status information is not available." />
          )}
        </div>
      </div>
    </div>
  )
}
