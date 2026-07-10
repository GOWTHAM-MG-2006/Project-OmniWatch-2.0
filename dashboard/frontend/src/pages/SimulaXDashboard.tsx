export default function SimulaXDashboard() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">SimulaX Dashboard</h1>
      <p className="text-gray-400">Digital twin simulation and what-if analysis.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">Simulation Modes</h3>
          <ul className="mt-2 space-y-1 text-sm text-gray-300">
            <li>Remediation Simulation</li>
            <li>Capacity Simulation</li>
            <li>Deployment Simulation</li>
            <li>Chaos Simulation</li>
          </ul>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-400">Recent Simulations</h3>
          <p className="mt-2 text-sm text-gray-500">No simulations run yet.</p>
        </div>
      </div>
    </div>
  )
}
