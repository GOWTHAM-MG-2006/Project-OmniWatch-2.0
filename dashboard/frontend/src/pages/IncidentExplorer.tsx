import { useState } from 'react'
import { useApi } from '../hooks'
import LoadingSkeleton from '../components/ux/LoadingSkeleton'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'
import SeverityBadge from '../components/ux/SeverityBadge'

interface EvidenceStep {
  step: number
  observation: string
  timestamp: string
  signal_type: string
  confidence?: number
}

interface BlastRadius {
  entity: string
  impact: string
}

interface Incident {
  incident_id: string
  created_at: string
  severity: string
  status: string
  root_cause?: string
  business_impact_score?: number
  blast_radius?: BlastRadius[]
  evidence_chain?: EvidenceStep[]
  sla_breach_risk?: string
  assigned_to?: string
}



export default function IncidentExplorer() {
  const { data: incidents, loading, error } = useApi<Incident[]>('/api/v1/incidents/')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Incident Explorer</h1>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-[500px] animate-pulse" />
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-[500px] animate-pulse" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Incident Explorer</h1>
        <ErrorAlert message={`Failed to load incidents: ${error}`} />
      </div>
    )
  }

  const incidentList = incidents ?? []
  const selected = incidentList.find((inc: Incident) => inc.incident_id === selectedId) ?? null

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Incident Explorer</h1>
      <p className="text-gray-400">Drill-down incident timeline with evidence chains.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Incident List */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Incidents ({incidentList.length})</h2>
          </div>
          {incidentList.length === 0 ? (
            <EmptyState title="No active incidents" description="No incidents to display." />
          ) : (
            <div className="divide-y divide-gray-700 max-h-[500px] overflow-y-auto">
              {incidentList.map((inc: Incident) => (
                <button
                  key={inc.incident_id}
                  onClick={() => setSelectedId(inc.incident_id)}
                  className={`w-full text-left px-4 py-3 transition-colors ${
                    selectedId === inc.incident_id
                      ? 'bg-gray-700'
                      : 'hover:bg-gray-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={inc.severity} />
                      <span className="font-mono text-sm">{inc.incident_id}</span>
                    </div>
                    <span className="text-xs text-gray-500">{inc.status}</span>
                  </div>
                  {inc.root_cause && (
                    <p className="text-sm text-gray-400 mt-1 truncate">{inc.root_cause}</p>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Incident Detail */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Incident Details</h2>
          </div>
          {selected ? (
            <div className="p-4 space-y-4">
              <div className="flex items-center gap-3">
                <SeverityBadge severity={selected.severity} />
                <span className="font-mono text-sm">{selected.incident_id}</span>
                <span className="text-xs text-gray-500">{selected.status}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-500">Created:</span>{' '}
                  {new Date(selected.created_at).toLocaleString()}
                </div>
                {selected.sla_breach_risk && (
                  <div>
                    <span className="text-gray-500">SLA Risk:</span>{' '}
                    <span
                      className={
                        selected.sla_breach_risk === 'HIGH'
                          ? 'text-red-400'
                          : 'text-yellow-400'
                      }
                    >
                      {selected.sla_breach_risk}
                    </span>
                  </div>
                )}
                {selected.business_impact_score != null && (
                  <div>
                    <span className="text-gray-500">Impact Score:</span>{' '}
                    {selected.business_impact_score}
                  </div>
                )}
                {selected.assigned_to && (
                  <div>
                    <span className="text-gray-500">Assigned:</span> {selected.assigned_to}
                  </div>
                )}
              </div>

              {/* Blast Radius */}
              {selected.blast_radius && selected.blast_radius.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Blast Radius</h3>
                  <div className="space-y-1">
                    {selected.blast_radius.map((b: BlastRadius, idx: number) => (
                      <div
                        key={idx}
                        className="bg-gray-900 rounded p-2 text-sm flex justify-between"
                      >
                        <span>{b.entity}</span>
                        <span className="text-gray-400">{b.impact}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Evidence Chain */}
              {selected.evidence_chain && selected.evidence_chain.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Evidence Chain</h3>
                  <div className="relative ml-3 border-l-2 border-gray-600 space-y-3 pl-4">
                    {selected.evidence_chain.map((step: EvidenceStep) => (
                      <div key={step.step} className="relative">
                        <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-gray-600 border-2 border-cyan-400" />
                        <div className="bg-gray-900 rounded p-3">
                          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                            <span>
                              Step {step.step} &middot; {step.signal_type}
                            </span>
                            <span>{new Date(step.timestamp).toLocaleTimeString()}</span>
                          </div>
                          <p className="text-sm">{step.observation}</p>
                          {step.confidence != null && (
                            <div className="text-xs text-gray-500 mt-1">
                              Confidence: {(step.confidence * 100).toFixed(0)}%
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-2">
                <button className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded text-sm font-medium transition-colors">
                  Run Simulation
                </button>
                <button className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded text-sm font-medium transition-colors">
                  Approve Remediation
                </button>
                <button className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded text-sm font-medium transition-colors">
                  View Topology
                </button>
              </div>
            </div>
          ) : (
            <EmptyState title="No incident selected" description="Select an incident from the list to view details." />
          )}
        </div>
      </div>
    </div>
  )
}
