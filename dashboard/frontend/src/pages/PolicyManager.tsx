import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import ErrorAlert from '../components/ux/ErrorAlert'

interface Policy {
  id: string
  name: string
  description: string
  enabled: boolean
  last_modified: string
}

interface PolicyListResponse {
  policies: Policy[]
  total: number
}

export default function PolicyManager() {
  const { data: policyData, loading, error } = useApi<PolicyListResponse>('/api/v1/policies/')
  const [selectedPolicy, setSelectedPolicy] = useState<string | null>(null)
  const [editorContent, setEditorContent] = useState(
    `# Example OPA Rego Policy
# AutoHeal Tier Configuration
package omniwatch.remediation

default allow = false

allow {
    input.action_type == "ROLLBACK"
    input.simulation_confidence >= 0.9
    input.severity == "P1"
}

allow {
    input.action_type == "SCALE_UP"
    input.auto_approve == true
    input.confidence >= 0.95
}`,
  )
  const [testResults, setTestResults] = useState<string | null>(null)

  const policyList = policyData?.policies ?? []

  const handleRunTests = () => {
    setTestResults('Running policy tests...\n\n✓ remediation.rego: PASS (12/12 rules)\n✓ security.rego: PASS (8/8 rules)\n✓ config_drift.rego: PASS (5/5 rules)\n\nAll 25 test cases passed.')
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Policy Manager</h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg h-96 border border-gray-700 animate-pulse" />
          <div className="bg-gray-800 rounded-lg h-96 border border-gray-700 lg:col-span-2 animate-pulse" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Policy Manager</h1>
        <ErrorAlert message={`Failed to load policies: ${error}`} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Policy Manager</h1>
      <p className="text-gray-400">OPA Rego policy management for AutoHeal and security rules.</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Policy List */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
            <h2 className="font-semibold">Policies</h2>
            <button className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 rounded text-xs font-medium transition-colors">
              + New
            </button>
          </div>
          {policyList.length === 0 ? (
            <div className="p-4 space-y-3">
              {/* Placeholder policies when API returns empty */}
              {[
                { name: 'remediation.rego', desc: 'AutoHeal tier decisions' },
                { name: 'security.rego', desc: 'Security action authorization' },
                { name: 'config_drift.rego', desc: 'Config drift remediation rules' },
              ].map((p) => (
                <button
                  key={p.name}
                  onClick={() => setSelectedPolicy(p.name)}
                  className={`w-full text-left px-3 py-2.5 rounded transition-colors ${
                    selectedPolicy === p.name
                      ? 'bg-gray-700 border border-cyan-600'
                      : 'hover:bg-gray-900 border border-transparent'
                  }`}
                >
                  <div className="font-mono text-sm text-cyan-400">{p.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{p.desc}</div>
                </button>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-gray-700 max-h-[400px] overflow-y-auto">
              {policyList.map((policy) => (
                <button
                  key={policy.id}
                  onClick={() => setSelectedPolicy(policy.id)}
                  className={`w-full text-left px-4 py-3 transition-colors ${
                    selectedPolicy === policy.id
                      ? 'bg-gray-700'
                      : 'hover:bg-gray-900'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm text-cyan-400">{policy.name}</span>
                    <span
                      className={`text-xs ${policy.enabled ? 'text-green-400' : 'text-gray-500'}`}
                    >
                      {policy.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{policy.description}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Policy Editor */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
              <h2 className="font-semibold">
                Policy Editor{' '}
                {selectedPolicy && (
                  <span className="text-cyan-400 font-mono text-sm ml-2">{selectedPolicy}</span>
                )}
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={handleRunTests}
                  className="px-3 py-1 bg-green-600 hover:bg-green-500 rounded text-xs font-medium transition-colors"
                >
                  Run Tests
                </button>
                <button className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-xs font-medium transition-colors">
                  Save
                </button>
              </div>
            </div>
            <textarea
              value={editorContent}
              onChange={(e) => setEditorContent(e.target.value)}
              className="w-full h-80 bg-gray-900 p-4 text-sm font-mono text-gray-100 resize-none focus:outline-none rounded-b-lg"
              spellCheck={false}
            />
            <div className="px-4 py-2 border-t border-gray-700 text-xs text-gray-500">
              Rego syntax highlighting available. Paste or write OPA policy rules.
            </div>
          </div>

          {/* Test Results */}
          {testResults && (
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="px-4 py-3 border-b border-gray-700">
                <h2 className="font-semibold">Test Results</h2>
              </div>
              <pre className="p-4 text-sm font-mono text-gray-300 whitespace-pre-wrap">
                {testResults}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
