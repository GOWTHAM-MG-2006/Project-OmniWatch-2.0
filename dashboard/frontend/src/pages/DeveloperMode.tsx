import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import LoadingSkeleton from '../components/ux/LoadingSkeleton'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'
import StatusBadge from '../components/ux/StatusBadge'

interface ServiceNode {
  id: string
  name: string
  type: string
  status: string
  anomaly_score?: number
  cloud_provider?: string
  last_seen?: string
}

interface TopologyGraph {
  nodes: ServiceNode[]
}

interface Deployment {
  version: string
  deployed_at: string
  status: string
  service: string
}



export default function DeveloperMode() {
  const [selectedService, setSelectedService] = useState<string>('')

  const { data: topoData, loading: topoLoading, error: topoError } = useApi<TopologyGraph>(
    '/api/v1/topology/graph'
  )
  const { data: deployments, loading: depLoading, error: depError } = useApi<Deployment[]>(
    `/api/v1/metrics/deployments${selectedService ? `?service=${selectedService}` : ''}`,
    { immediate: false }
  )

  const loading = topoLoading
  const error = topoError || depError
  const services: ServiceNode[] = topoData?.nodes ?? []

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-8 w-48 bg-gray-800 rounded animate-pulse" />
          <div className="h-8 w-40 bg-gray-800 rounded animate-pulse" />
        </div>
        <div className="bg-gray-800 rounded-lg border border-gray-700 h-96 animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg border border-gray-700 h-64 animate-pulse" />
          <div className="bg-gray-800 rounded-lg border border-gray-700 h-64 animate-pulse" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Developer Mode</h1>
        </div>
        <ErrorAlert message={`Failed to load developer data: ${error}`} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Developer Mode</h1>
          <p className="text-gray-400 text-sm">Distributed traces, flame graphs, and deployment history.</p>
        </div>
        <select
          value={selectedService}
          onChange={(e) => setSelectedService(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
          <option value="">All Services</option>
          {services.map((svc) => (
            <option key={svc.id} value={svc.id}>
              {svc.name}
            </option>
          ))}
        </select>
      </div>

      {/* Service List */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700">
          <h2 className="font-semibold">Services</h2>
        </div>
        {services.length === 0 ? (
          <EmptyState title="No services found" description="No services found in topology graph." />
        ) : (
          <div className="divide-y divide-gray-700">
            {services
              .filter((svc) => !selectedService || svc.id === selectedService)
              .map((svc) => (
                <div key={svc.id} className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <StatusDot status={svc.status ?? 'unknown'} />
                    <div>
                      <span className="font-mono text-sm">{svc.name}</span>
                      <span className="ml-2 text-xs text-gray-500">{svc.type}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    {svc.cloud_provider && <span>{svc.cloud_provider}</span>}
                    {svc.anomaly_score != null && (
                      <span className={svc.anomaly_score > 0.7 ? 'text-red-400' : 'text-gray-400'}>
                        Score: {svc.anomaly_score.toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Trace Waterfall Placeholder */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Trace Waterfall</h2>
          </div>
          <div className="p-8 flex items-center justify-center h-64">
            <div className="text-center text-gray-500">
              <div className="text-4xl mb-2">🔍</div>
              <p className="text-sm">Trace waterfall coming soon</p>
              <p className="text-xs text-gray-600 mt-1">Requires Jaeger/OTel trace viewer</p>
            </div>
          </div>
        </div>

        {/* Deployment Timeline */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Deployment Timeline</h2>
          </div>
          {depLoading ? (
            <div className="p-4 space-y-3 animate-pulse">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-900 rounded" />
              ))}
            </div>
          ) : !deployments || deployments.length === 0 ? (
            <EmptyState title="No deployment data" description="Select a service to view deployments." />
          ) : (
            <div className="p-4 space-y-3">
              {deployments.slice(0, 8).map((dep, idx) => (
                <div key={idx} className="flex items-center justify-between bg-gray-900 rounded px-3 py-2">
                  <div className="flex items-center gap-2">
                    <StatusDot status={dep.status} />
                    <span className="font-mono text-sm">{dep.version}</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {dep.deployed_at ? new Date(dep.deployed_at).toLocaleString() : '--'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
