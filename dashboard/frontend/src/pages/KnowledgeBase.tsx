import { useState, useMemo } from 'react'
import { useApi } from '../hooks/useApi'
import LoadingSkeleton from '../components/ux/LoadingSkeleton'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'

interface KnowledgeEntry {
  id: string
  incident_id: string
  root_cause: string
  resolution: string
  confidence: number
  root_cause_entity_type?: string
  resolution_time_minutes?: number
  created_at: string
  tags?: string[]
}

function ConfidenceBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  let color = 'bg-gray-500'
  if (pct >= 80) color = 'bg-green-500'
  else if (pct >= 50) color = 'bg-yellow-500'
  else color = 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400">{pct}%</span>
    </div>
  )
}



export default function KnowledgeBase() {
  const { data: entries, loading, error } = useApi<KnowledgeEntry[]>('/api/v1/knowledge/')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const list = entries ?? []
    if (!search.trim()) return list
    const q = search.toLowerCase()
    return list.filter(
      (e) =>
        e.incident_id.toLowerCase().includes(q) ||
        e.root_cause.toLowerCase().includes(q) ||
        e.resolution.toLowerCase().includes(q) ||
        (e.tags ?? []).some((t) => t.toLowerCase().includes(q)),
    )
  }, [entries, search])

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Knowledge Base</h1>
        <div className="bg-gray-800 rounded-lg h-10 w-full border border-gray-700 animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="bg-gray-800 rounded-lg p-4 border border-gray-700 animate-pulse">
              <div className="flex justify-between mb-2">
                <div className="h-4 bg-gray-700 rounded w-32" />
                <div className="h-4 bg-gray-700 rounded w-16" />
              </div>
              <div className="h-3 bg-gray-700 rounded w-full mb-2" />
              <div className="h-3 bg-gray-700 rounded w-3/4" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Knowledge Base</h1>
        <ErrorAlert message={`Failed to load knowledge base: ${error}`} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Knowledge Base</h1>
      <p className="text-gray-400">Historical incidents, runbooks, and learned patterns.</p>

      {/* Search */}
      <input
        type="text"
        placeholder="Search by incident ID, root cause, resolution, or tag..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
      />

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-gray-400">
        <span>
          Showing <span className="text-gray-100 font-medium">{filtered.length}</span> of{' '}
          {(entries ?? []).length} entries
        </span>
      </div>

      {/* Entries List */}
      {filtered.length === 0 ? (
        <EmptyState title="No knowledge entries found" description="Entries are created when incidents are resolved." />
      ) : (
        <div className="space-y-3">
          {filtered.map((entry) => (
            <div
              key={entry.id}
              className="bg-gray-800 rounded-lg border border-gray-700 p-4 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-sm text-cyan-400">{entry.incident_id}</span>
                    {entry.root_cause_entity_type && (
                      <span className="inline-block px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                        {entry.root_cause_entity_type}
                      </span>
                    )}
                    {entry.resolution_time_minutes != null && (
                      <span className="text-xs text-gray-500">
                        Resolved in {entry.resolution_time_minutes}m
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-medium text-gray-100 mb-1">{entry.root_cause}</h3>
                  <p className="text-sm text-gray-400 line-clamp-2">{entry.resolution}</p>

                  {entry.tags && entry.tags.length > 0 && (
                    <div className="flex gap-1.5 mt-2 flex-wrap">
                      {entry.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-1.5 py-0.5 rounded text-xs bg-gray-700 text-gray-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0 text-right">
                  <ConfidenceBar score={entry.confidence} />
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(entry.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
