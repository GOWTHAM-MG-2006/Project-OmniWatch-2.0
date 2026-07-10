# Dashboard Layer (Layer 11: NexusUX)

## Role-Adaptive Dashboard

5 user modes with role-based views:

### Backend (FastAPI)
- **main.py** — API gateway with /health endpoint
- **routes/** — Domain-specific REST endpoints
- **websocket.py** — Real-time event streaming

### Frontend (React 19)
- **SREMode.tsx** — Active problems, evidence, topology
- **DeveloperMode.tsx** — Traces, flame graphs, git blame
- **ExecutiveMode.tsx** — SLO, revenue, cost, MTTR
- **SecurityMode.tsx** — CVE, CSPM, MITRE ATT&CK
- **AIFirstChat.tsx** — Natural language → NQL + answers
- **IncidentExplorer.tsx** — Drill-down incident timeline
- **TopologyViewer.tsx** — 8-layer dependency graph (Sigma.js)
- **KnowledgeBase.tsx** — Historical incidents + runbooks
- **PolicyManager.tsx** — OPA policy management
- **SimulaXDashboard.tsx** — Digital twin simulation UI
- **ConfigDriftView.tsx** — Config drift status + remediation

## Technology

- React 19, TypeScript, Vite 6.x, TailwindCSS 4.x
- Sigma.js + Graphology (graph visualization)
- Recharts (metrics charts)
- D3.js (custom visualizations)
- FastAPI (backend API)
