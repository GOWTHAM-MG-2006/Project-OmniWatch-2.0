import { useState } from 'react'
import { useApi, useApiPost } from '../hooks/useApi'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'
import StatusBadge from '../components/ux/StatusBadge'

interface Simulation {
  simulation_id: string
  mode: string
  status: string
  created_at: string
  resolution_confidence?: number
  risk_score?: number
  recommendation?: string
}

interface SimulationRequest {
  mode: string
  incident_id: string
  parameters?: Record<string, string>
}

interface SimulationResponse {
  simulation_id: string
  mode: string
  status: string
  predicted_outcome?: {
    resolution_confidence: number
    recovery_time_minutes: number
    side_effects?: string[]
    revenue_recovery_usd?: number
  }
  risk_score?: number
  recommendation?: string
}

interface SimulationListResponse {
  simulations: Simulation[]
  total: number
}

interface SimulationModesResponse {
  modes: string[]
}

const DEFAULT_MODES = [
  { id: 'REMEDIATION_SIMULATION', name: 'Remediation Simulation', description: 'Simulate proposed fixes' },
  { id: 'CAPACITY_SIMULATION', name: 'Capacity Simulation', description: 'Simulate traffic growth' },
  { id: 'DEPLOYMENT_SIMULATION', name: 'Deployment Simulation', description: 'Simulate deployment rollout' },
  { id: 'CHAOS_SIMULATION', name: 'Chaos Simulation', description: 'Simulate failure injection' },
]

export default function SimulaXDashboard() {
  const { data: modesData, loading: modesLoading, error: modesError } =
    useApi<SimulationModesResponse>('/api/v1/simulations/modes')
  const { data: simData, loading: simsLoading, error: simsError, refetch } =
    useApi<SimulationListResponse>('/api/v1/simulations/')
  const { loading: postLoading, error: postError, execute: runSimulation } =
    useApiPost<SimulationResponse, SimulationRequest>('/api/v1/simulations/')

  const [selectedMode, setSelectedMode] = useState('')
  const [incidentId, setIncidentId] = useState('')
  const [customParams, setCustomParams] = useState('')
  const [lastResult] = useState<SimulationResponse | null>(null)

  const modeList = modesData?.modes
    ? modesData.modes.map(m => DEFAULT_MODES.find(d => d.id === m) ?? { id: m, name: m, description: '' })
    : DEFAULT_MODES

  const simList = simData?.simulations ?? []

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedMode || !incidentId) return
    let params: Record<string, string> = {}
    if (customParams.trim()) {
      try {
        params = JSON.parse(customParams)
      } catch {
        return
      }
    }
    await runSimulation({ mode: selectedMode, incident_id: incidentId, parameters: params })
    // Refetch simulation list after completion
    refetch()
  }

  const isLoading = modesLoading || simsLoading

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">SimulaX Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg h-48 border border-gray-700 animate-pulse" />
          <div className="bg-gray-800 rounded-lg h-48 border border-gray-700 animate-pulse" />
        </div>
        <div className="bg-gray-800 rounded-lg h-96 border border-gray-700 animate-pulse" />
      </div>
    )
  }

  if (modesError || simsError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">SimulaX Dashboard</h1>
        <ErrorAlert message={`Failed to load: ${modesError || simsError}`} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">SimulaX Dashboard</h1>
      <p className="text-gray-400">Digital twin simulation and what-if analysis.</p>

      {/* Simulation Modes + Trigger Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Modes */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Simulation Modes</h2>
          </div>
          <div className="p-4 space-y-2">
            {modeList.map((mode) => (
              <button
                key={mode.id}
                onClick={() => setSelectedMode(mode.id)}
                className={`w-full text-left px-3 py-2.5 rounded transition-colors ${
                  selectedMode === mode.id
                    ? 'bg-cyan-900/40 border border-cyan-600'
                    : 'hover:bg-gray-900 border border-transparent'
                }`}
              >
                <div className="text-sm font-medium text-gray-100">{mode.name}</div>
                <div className="text-xs text-gray-500">{mode.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Trigger Form */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Run Simulation</h2>
          </div>
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Mode</label>
              <select
                value={selectedMode}
                onChange={(e) => setSelectedMode(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="">Select a mode...</option>
                {modeList.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Incident ID</label>
              <input
                type="text"
                value={incidentId}
                onChange={(e) => setIncidentId(e.target.value)}
                placeholder="INC-2026-07-001"
                className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Parameters <span className="text-gray-600">(JSON, optional)</span>
              </label>
              <textarea
                value={customParams}
                onChange={(e) => setCustomParams(e.target.value)}
                placeholder='{"from_version": "v2.1.3", "to_version": "v2.1.4"}'
                className="w-full h-24 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm font-mono text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500 resize-none"
              />
            </div>
            {postError && (
              <div className="bg-red-900/30 border border-red-700 rounded px-3 py-2 text-sm text-red-400">
                {postError}
              </div>
            )}
            <button
              type="submit"
              disabled={!selectedMode || !incidentId || postLoading}
              className="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
            >
              {postLoading ? 'Running Simulation...' : 'Run Simulation'}
            </button>
          </form>
        </div>
      </div>

      {/* Last Result */}
      {lastResult && (
        <div className="bg-gray-800 rounded-lg border border-cyan-700 p-4">
          <h2 className="font-semibold mb-3 text-cyan-400">Latest Simulation Result</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">ID:</span>{' '}
              <span className="font-mono">{lastResult.simulation_id}</span>
            </div>
            <div>
              <span className="text-gray-500">Mode:</span> {lastResult.mode}
            </div>
            {lastResult.predicted_outcome && (
              <>
                <div>
                  <span className="text-gray-500">Confidence:</span>{' '}
                  {Math.round(lastResult.predicted_outcome.resolution_confidence * 100)}%
                </div>
                <div>
                  <span className="text-gray-500">Recovery:</span>{' '}
                  {lastResult.predicted_outcome.recovery_time_minutes}m
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Recent Simulations */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold">Recent Simulations ({simList.length})</h2>
        </div>
        {simList.length === 0 ? (
          <EmptyState title="No simulations run yet" description="Run a simulation to see results here." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="px-4 py-3 font-medium">ID</th>
                  <th className="px-4 py-3 font-medium">Mode</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Confidence</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Recommendation</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {simList.map((sim) => (
                  <tr key={sim.simulation_id} className="hover:bg-gray-900 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-cyan-400">
                      {sim.simulation_id}
                    </td>
                    <td className="px-4 py-3">{sim.mode}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={sim.status} />
                    </td>
                    <td className="px-4 py-3">
                      {sim.resolution_confidence != null
                        ? `${Math.round(sim.resolution_confidence * 100)}%`
                        : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {sim.risk_score != null ? `${Math.round(sim.risk_score * 100)}%` : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {sim.recommendation && (
                        <span
                          className={`text-xs font-medium ${
                            sim.recommendation === 'PROCEED'
                              ? 'text-green-400'
                              : 'text-yellow-400'
                          }`}
                        >
                          {sim.recommendation}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(sim.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
