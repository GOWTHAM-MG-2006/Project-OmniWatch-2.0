export default function SecurityMode() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Security Mode</h1>
      <p className="text-gray-400">CVE tracking, CSPM status, and MITRE ATT&CK threat map.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">Critical CVEs</h3>
          <p className="text-3xl font-bold text-red-400">0</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">CSPM Compliance</h3>
          <p className="text-3xl font-bold text-green-400">100%</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">Active Threats</h3>
          <p className="text-3xl font-bold text-gray-400">0</p>
        </div>
      </div>
    </div>
  )
}
