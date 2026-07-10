export default function ConfigDriftView() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Config Drift View</h1>
      <p className="text-gray-400">Configuration drift detection and remediation status.</p>
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <p className="text-gray-400">No drifts detected.</p>
      </div>
    </div>
  )
}
