import { useApi } from '../hooks/useApi'
import EmptyState from '../components/ux/EmptyState'
import ErrorAlert from '../components/ux/ErrorAlert'
import MetricCard from '../components/ux/MetricCard'
import SeverityBadge from '../components/ux/SeverityBadge'

interface SecurityEvent {
  event_id: string
  attack_type: string
  entity_id: string
  severity: string
  confidence: number
  source_ip?: string
  recommended_action?: string
  timestamp: string
}

interface Vulnerability {
  cve_id: string
  severity: string
  entity_id: string
  cvss_score?: number
  affected_package?: string
  reachability?: string
  remediation?: string
}

interface CSPMStatus {
  compliance_pct?: number
  total_checks?: number
  passed_checks?: number
  failed_checks?: number
  categories?: Record<string, { passed: number; total: number }>
}

interface SecurityEventListResponse {
  events: SecurityEvent[]
  total: number
}

interface VulnerabilityListResponse {
  vulnerabilities: Vulnerability[]
  total: number
}



function VulnMatrix({ vulns }: { vulns: Vulnerability[] }) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0 }
  for (const v of vulns) {
    const s = v.severity?.toLowerCase() ?? ''
    if (s === 'critical') counts.critical++
    else if (s === 'high') counts.high++
    else if (s === 'medium' || s === 'moderate') counts.medium++
    else counts.low++
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="bg-red-900/30 rounded p-3 text-center">
        <div className="text-2xl font-bold text-red-400">{counts.critical}</div>
        <div className="text-xs text-gray-400">Critical</div>
      </div>
      <div className="bg-orange-900/30 rounded p-3 text-center">
        <div className="text-2xl font-bold text-orange-400">{counts.high}</div>
        <div className="text-xs text-gray-400">High</div>
      </div>
      <div className="bg-yellow-900/30 rounded p-3 text-center">
        <div className="text-2xl font-bold text-yellow-400">{counts.medium}</div>
        <div className="text-xs text-gray-400">Medium</div>
      </div>
      <div className="bg-blue-900/30 rounded p-3 text-center">
        <div className="text-2xl font-bold text-blue-400">{counts.low}</div>
        <div className="text-xs text-gray-400">Low</div>
      </div>
    </div>
  )
}

export default function SecurityMode() {
  const { data: eventData, loading: eventsLoading, error: eventsError } = useApi<SecurityEventListResponse>(
    '/api/v1/security/events'
  )
  const { data: vulnData, loading: vulnsLoading, error: vulnsError } = useApi<VulnerabilityListResponse>(
    '/api/v1/security/vulnerabilities'
  )
  const { data: cspmData, loading: cspmLoading, error: cspmError } = useApi<CSPMStatus>(
    '/api/v1/security/cspm'
  )

  const loading = eventsLoading || vulnsLoading || cspmLoading
  const error = eventsError || vulnsError || cspmError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Security Mode</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[0, 1, 2].map((idx) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-gray-700 h-28 animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg border border-gray-700 h-80 animate-pulse" />
          <div className="bg-gray-800 rounded-lg border border-gray-700 h-80 animate-pulse" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Security Mode</h1>
        </div>
        <ErrorAlert message={`Failed to load security data: ${error}`} />
      </div>
    )
  }

  const events: SecurityEvent[] = eventData?.events ?? []
  const vulns: Vulnerability[] = vulnData?.vulnerabilities ?? []
  const cspm: CSPMStatus = cspmData ?? {}

  const criticalCVEs = vulns.filter((v) => v.severity?.toLowerCase() === 'critical').length
  const activeThreats = events.filter((e) => {
    const s = e.severity?.toLowerCase()
    return s === 'critical' || s === 'high'
  }).length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Security Mode</h1>
        <p className="text-gray-400 text-sm">CVE tracking, CSPM status, and threat detection.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Critical CVEs" value={criticalCVEs} />
        <MetricCard title="CSPM Compliance" value={cspm.compliance_pct != null ? `${cspm.compliance_pct.toFixed(1)}%` : '--'} />
        <MetricCard title="Active Threats" value={activeThreats} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Security Events List */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Security Events</h2>
          </div>
          {events.length === 0 ? (
            <EmptyState title="No security events" description="No security events detected." />
          ) : (
            <div className="divide-y divide-gray-700 max-h-80 overflow-y-auto">
              {events.slice(0, 10).map((evt) => (
                <div key={evt.event_id} className="px-4 py-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={evt.severity} />
                      <span className="text-sm font-medium">{evt.attack_type}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : '--'}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                    <span>{evt.entity_id}</span>
                    {evt.source_ip && <span>IP: {evt.source_ip}</span>}
                    <span>Confidence: {(evt.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {evt.recommended_action && (
                    <div className="mt-1 text-xs text-cyan-400">
                      Action: {evt.recommended_action}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Vulnerability Matrix */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">Vulnerability Matrix</h2>
          </div>
          <div className="p-4 space-y-4">
            <VulnMatrix vulns={vulns} />
            {vulns.length === 0 ? (
              <EmptyState title="No vulnerability data" description="No vulnerability data available." />
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {vulns.slice(0, 8).map((v) => (
                  <div key={v.cve_id} className="flex items-center justify-between bg-gray-900 rounded px-3 py-2">
                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={v.severity} />
                      <span className="font-mono text-xs">{v.cve_id}</span>
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-3">
                      {v.cvss_score != null && <span>CVSS: {v.cvss_score}</span>}
                      <span>{v.entity_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CSPM Categories */}
      {cspm.categories && Object.keys(cspm.categories).length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-semibold">CSPM Check Categories</h2>
          </div>
          <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(cspm.categories).map(([cat, info]) => (
              <div key={cat} className="bg-gray-900 rounded p-3">
                <div className="text-xs text-gray-500 mb-1">{cat}</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{
                        width: `${info.total > 0 ? (info.passed / info.total) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-400">
                    {info.passed}/{info.total}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
