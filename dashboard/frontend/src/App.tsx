import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import SREMode from './pages/SREMode'
import DeveloperMode from './pages/DeveloperMode'
import ExecutiveMode from './pages/ExecutiveMode'
import SecurityMode from './pages/SecurityMode'
import AIFirstChat from './pages/AIFirstChat'
import IncidentExplorer from './pages/IncidentExplorer'
import TopologyViewer from './pages/TopologyViewer'
import KnowledgeBase from './pages/KnowledgeBase'
import PolicyManager from './pages/PolicyManager'
import SimulaXDashboard from './pages/SimulaXDashboard'
import ConfigDriftView from './pages/ConfigDriftView'

const navItems = [
  { path: '/', label: 'SRE Mode' },
  { path: '/developer', label: 'Developer' },
  { path: '/executive', label: 'Executive' },
  { path: '/security', label: 'Security' },
  { path: '/ai-chat', label: 'AI Chat' },
  { path: '/incidents', label: 'Incidents' },
  { path: '/topology', label: 'Topology' },
  { path: '/knowledge', label: 'Knowledge' },
  { path: '/policies', label: 'Policies' },
  { path: '/simulations', label: 'SimulaX' },
  { path: '/config-drift', label: 'Config Drift' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        {/* Navigation */}
        <nav className="bg-gray-900 border-b border-gray-800">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center h-14">
              <span className="text-xl font-bold text-cyan-400 mr-8">OmniWatch</span>
              <div className="flex space-x-1 overflow-x-auto">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/'}
                    className={({ isActive }) =>
                      `px-3 py-2 rounded text-sm whitespace-nowrap transition-colors ${
                        isActive
                          ? 'bg-gray-700 text-cyan-400'
                          : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                      }`
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<SREMode />} />
              <Route path="/developer" element={<DeveloperMode />} />
              <Route path="/executive" element={<ExecutiveMode />} />
              <Route path="/security" element={<SecurityMode />} />
              <Route path="/ai-chat" element={<AIFirstChat />} />
              <Route path="/incidents" element={<IncidentExplorer />} />
              <Route path="/topology" element={<TopologyViewer />} />
              <Route path="/knowledge" element={<KnowledgeBase />} />
              <Route path="/policies" element={<PolicyManager />} />
              <Route path="/simulations" element={<SimulaXDashboard />} />
              <Route path="/config-drift" element={<ConfigDriftView />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  )
}
