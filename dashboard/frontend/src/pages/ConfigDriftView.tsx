import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import LoadingSkeleton from '../components/ux/LoadingSkeleton'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'

interface DriftEvent {
  drift_id: string
  drift_source: string
  detection_method: string
  drifted_entity: string
  expected_state: Record<string, unknown>
  actual_state: Record<string, unknown>
  remediation_tool: string
  remediation_action: string
  confidence: number
  status: string
  timestamp: string
}

interface DriftSource {
  id: string
  name: string
  type: string
  status: string
  last_checked: string
}

function SeverityIndicator({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100)
  let color = 'text-gray-400'
  if (pct >= 90) color = 'text-red-400'
  else if (pct >= 70) color = 'text-yellow-400'
  return <span className={`text-sm font-medium ${color}`}>{pct}%</span>
}

function StateDiff({
  expected,
  actual,
}: {
  expected: Record<string, unknown>
  actual: Record<string, unknown>
}) {
  const keys = Object.keys(expected)
  return (
    <div className="bg-gray-900 rounded p-3 text-xs font-mono space-y-1">
      {keys.map((key) => {
        const exp = JSON.stringify(expected[key])
        const act = JSON.stringify(actual[key])
        const changed = exp !== act
        return (
          <div key={key} className={`flex gap-2 ${changed ? 'text-red-400' : 'text-gray-500'}`}>
            <span className="w-28 flex-shrink-0">{key}:</span>
            {changed ? (
              <>
                <span className="text-green-400">{exp}</span>
                <span>&rarr;</span>
                <span className="text-red-400">{act}</span>
              </>
            ) : (
              <span>{exp}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}



export default function ConfigDriftView() {
  const { data: drifts, loading: driftsLoading, error: driftsError, refetch } =
    useApi<DriftEvent[]>('/api/v1/config-drift/')
  const { data: sources, loading: sourcesLoading, error: sourcesError } =
    useApi<DriftSource[]>('/api/v1/config-drift/sources')

  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [remediating, setRemediating] = useState<string | null>(null)
  const [remediateError, setRemediateError] = useState<string | null>(null)

  const driftList = drifts ?? []
  const sourceList = sources ?? []

  const handleRemediate = async (driftId: string) => {
    setRemediating(driftId)
    setRemediateError(null)
    try {
      const token = localStorage.getItem('auth_token')
      const res = await fetch(`/api/v1/config-drift/${driftId}/remediate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      refetch()
    } catch (err) {
      setRemediateError(err instanceof Error ? err.message : 'Remediation failed')
    } finally {
      setRemediateError(null)
      setRemediating(null)
    }
  }

  const isLoading = driftsLoading || sourcesLoading

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Configuration Drift</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-800 rounded-lg h-24 border border-gray-700 animate-pulse" />
          ))}
        </div>
        <div className="bg-gray-800 rounded-lg h-96 border border-gray-700 animate-pulse" />
      </div>
    )
  }

  if (driftsError || sourcesError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Configuration Drift</h1>
        <ErrorAlert message={`Failed to load: ${driftsError || sourcesError}`} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Configuration Drift</h1>
      <p className="text-gray-400">
        Detect and remediate configuration drift across K8s, OS, Cloud, and Git layers.
      </p>

      {/* Source Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sourceList.length > 0 ? (
          sourceList.map((src) => (
            <div
              key={src.id}
              className="bg-gray-800 rounded-lg border border-gray-700 p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-100">{src.name}</span>
                <span
                  className={`text-xs ${src.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'}`}
                >
                  {src.status}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                Last checked: {new Date(src.last_checked).toLocaleString()}
              </div>
            </div>
          ))
        ) : (
          <>
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-100">Kubernetes</span>
                <span className="text-xs text-green-400">healthy</span>
              </div>
              <div className="text-xs text-gray-500">ArgoCD self-heal enabled</div>
            </div>
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-100">Terraform</span>
                <span className="text-xs text-green-400">healthy</span>
              </div>
              <div className="text-xs text-gray-500">State drift detection active</div>
            </div>
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-100">Ansible</span>
                <span className="text-xs text-green-400">healthy</span>
              </div>
              <div className="text-xs text-gray-500">OS config drift monitored</div>
            </div>
          </>
        )}
      </div>

      {/* Drift Events */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold">Drift Events ({driftList.length})</h2>
        </div>
        {driftList.length === 0 ? (
          <EmptyState title="No drifts detected" description="All systems match their declared configuration." />
        ) : (
          <div className="divide-y divide-gray-700">
            {driftList.map((drift) => (
              <div key={drift.drift_id} className="hover:bg-gray-900/50 transition-colors">
                <div
                  className="px-4 py-3 cursor-pointer"
                  onClick={() =>
                    setExpandedId(expandedId === drift.drift_id ? null : drift.drift_id)
                  }
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-mono text-xs text-cyan-400 flex-shrink-0">
                        {drift.drift_id}
                      </span>
                      <span className="text-sm font-medium text-gray-100 truncate">
                        {drift.drifted_entity}
                      </span>
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300 flex-shrink-0">
                        {drift.drift_source}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <SeverityIndicator confidence={drift.confidence} />
                      <span className="text-xs text-gray-500">
                        {new Date(drift.timestamp).toLocaleString()}
                      </span>
                      <svg
                        className={`w-4 h-4 text-gray-500 transition-transform ${expandedId === drift.drift_id ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span>
                      Tool: <span className="text-gray-300">{drift.remediation_tool}</span>
                    </span>
                    <span>
                      Action: <span className="text-gray-300">{drift.remediation_action}</span>
                    </span>
                    <span>
                      Method: <span className="text-gray-300">{drift.detection_method}</span>
                    </span>
                    {drift.status && (
                      <span
                        className={`font-medium ${
                          drift.status === 'remediated'
                            ? 'text-green-400'
                            : drift.status === 'pending'
                              ? 'text-yellow-400'
                              : 'text-gray-400'
                        }`}
                      >
                        {drift.status}
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded Detail */}
                {expandedId === drift.drift_id && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-700 pt-3">
                    <div>
                      <h4 className="text-xs font-medium text-gray-400 mb-1">State Diff</h4>
                      <StateDiff expected={drift.expected_state} actual={drift.actual_state} />
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRemediate(drift.drift_id)
                        }}
                        disabled={remediating === drift.drift_id || drift.status === 'remediated'}
                        className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
                      >
                        {remediating === drift.drift_id ? 'Remediating...' : 'Remediate'}
                      </button>
                      <button
                        onClick={(e) => e.stopPropagation()}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition-colors"
                      >
                        View Audit Log
                      </button>
                    </div>
                    {remediateError && (
                      <div className="bg-red-900/30 border border-red-700 rounded px-3 py-2 text-sm text-red-400">
                        {remediateError}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
