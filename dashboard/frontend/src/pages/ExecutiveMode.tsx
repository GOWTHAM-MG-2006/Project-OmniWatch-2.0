export default function ExecutiveMode() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Executive Mode</h1>
      <p className="text-gray-400">SLO compliance, revenue impact, cost tracking, and MTTR metrics.</p>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">SLO Compliance</h3>
          <p className="text-3xl font-bold text-green-400">99.9%</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">MTTR</h3>
          <p className="text-3xl font-bold text-blue-400">--</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">Hourly Cost</h3>
          <p className="text-3xl font-bold text-yellow-400">$0</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">Revenue at Risk</h3>
          <p className="text-3xl font-bold text-red-400">$0</p>
        </div>
      </div>
    </div>
  )
}
