import { useState } from 'react'
import { useApi } from '../hooks'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'

interface TopologyNode {
  id: string
  name: string
  type: string
  status: string
  layer?: number
  cloud_provider?: string
  anomaly_score?: number
}

interface TopologyEdge {
  source: string
  target: string
  relationship: string
}

interface TopologyGraph {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
}

function statusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'healthy':
      return 'bg-green-500 hover:bg-green-400'
    case 'degraded':
      return 'bg-yellow-500 hover:bg-yellow-400'
    case 'unhealthy':
      return 'bg-red-500 hover:bg-red-400'
    default:
      return 'bg-gray-500 hover:bg-gray-400'
  }
}



export default function TopologyViewer() {
  const { data: topology, loading, error } = useApi<TopologyGraph>('/api/v1/topology/graph')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Topology Viewer</h1>
        </div>
        <div className="flex gap-3">
          <div className="bg-gray-800 rounded-lg p-4 h-10 w-48 animate-pulse" />
          <div className="bg-gray-800 rounded-lg p-4 h-10 w-32 animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from<number>({ length: 12 }).map((_: number, idx: number) => (
            <div key={idx} className="bg-gray-800 rounded-lg h-10 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Topology Viewer</h1>
        <ErrorAlert message={`Failed to load topology: ${error}`} />
      </div>
    )
  }

  const nodes: TopologyNode[] = topology?.nodes ?? []
  const edges: TopologyEdge[] = topology?.edges ?? []
  const nodeTypes: string[] = Array.from(new Set(nodes.map((n: TopologyNode) => n.type))).sort()
  const filteredNodes: TopologyNode[] = typeFilter === 'all'
    ? nodes
    : nodes.filter((n: TopologyNode) => n.type === typeFilter)
  const selectedNode: TopologyNode | undefined = nodes.find((n: TopologyNode) => n.id === selectedId)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">Topology Viewer</h1>
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>{nodes.length} nodes</span>
          <span>{edges.length} edges</span>
          <select
            value={typeFilter}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
              setTypeFilter(e.target.value)
              setSelectedId(null)
            }}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="all">All Types</option>
            {nodeTypes.map((t: string) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Node Grid */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <div className="flex flex-wrap gap-2">
              {filteredNodes.length === 0 ? (
                <EmptyState title="No nodes found" description="No topology nodes match the current filter." />
              ) : (
                filteredNodes.map((node: TopologyNode) => (
                  <button
                    key={node.id}
                    onClick={() => setSelectedId(node.id)}
                    className={`px-3 py-2 rounded text-sm font-medium text-white transition-colors ${
                      selectedId === node.id
                        ? 'ring-2 ring-cyan-400'
                        : ''
                    } ${statusColor(node.status)}`}
                    title={`${node.name} (${node.type})`}
                  >
                    {node.name}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Node Detail Panel */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Node Details</h2>
          </div>
          {selectedNode ? (
            <div className="p-4 space-y-3 text-sm">
              <div>
                <span className="text-gray-500">Name:</span>{' '}
                <span className="font-medium">{selectedNode.name}</span>
              </div>
              <div>
                <span className="text-gray-500">ID:</span>{' '}
                <span className="font-mono text-xs">{selectedNode.id}</span>
              </div>
              <div>
                <span className="text-gray-500">Type:</span> {selectedNode.type}
              </div>
              <div>
                <span className="text-gray-500">Status:</span>{' '}
                <span
                  className={
                    selectedNode.status === 'healthy'
                      ? 'text-green-400'
                      : selectedNode.status === 'degraded'
                        ? 'text-yellow-400'
                        : 'text-red-400'
                  }
                >
                  {selectedNode.status}
                </span>
              </div>
              {selectedNode.layer != null && (
                <div>
                  <span className="text-gray-500">Layer:</span> {selectedNode.layer}
                </div>
              )}
              {selectedNode.cloud_provider && (
                <div>
                  <span className="text-gray-500">Cloud:</span> {selectedNode.cloud_provider}
                </div>
              )}
              {selectedNode.anomaly_score != null && (
                <div>
                  <span className="text-gray-500">Anomaly Score:</span>{' '}
                  {(selectedNode.anomaly_score * 100).toFixed(1)}%
                </div>
              )}

              {/* Connections */}
              {(() => {
                const conns: TopologyEdge[] = edges.filter(
                  (e: TopologyEdge) => e.source === selectedNode.id || e.target === selectedNode.id,
                )
                if (conns.length === 0) return null
                return (
                  <div>
                    <span className="text-gray-500">Connections:</span>
                    <div className="mt-1 space-y-1">
                      {conns.map((e: TopologyEdge, idx: number) => {
                        const peer: string =
                          e.source === selectedNode.id ? e.target : e.source
                        const peerNode: TopologyNode | undefined = nodes.find(
                          (n: TopologyNode) => n.id === peer,
                        )
                        return (
                          <div key={idx} className="bg-gray-900 rounded p-2 flex justify-between">
                            <span>{peerNode?.name ?? peer}</span>
                            <span className="text-gray-500 text-xs">{e.relationship}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })()}
            </div>
          ) : (
            <EmptyState title="No node selected" description="Select a node to view details." />
          )}
        </div>
      </div>
    </div>
  )
}
