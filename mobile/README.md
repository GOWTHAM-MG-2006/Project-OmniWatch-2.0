# OmniWatch 2.0 — Mobile App

React Native Expo mobile application for OmniWatch 2.0 AIOps platform.

## Features

- **Dashboard**: Real-time incident list with stats cards and pull-to-refresh
- **Incident Details**: Evidence chain, blast radius, and approve/reject remediation actions
- **Topology**: Service topology view with health status and anomaly scores
- **Settings**: Server configuration, notification preferences, and auto-refresh options

## Tech Stack

- React Native 0.74.0
- Expo 51.0.0
- TypeScript 5.3
- React Navigation 6 (Bottom Tabs + Stack)

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run on specific platform
npm run android
npm run ios
```

## Project Structure

```
mobile/
├── src/
│   ├── App.tsx                 # Main app with navigation
│   ├── screens/
│   │   ├── DashboardScreen.tsx
│   │   ├── IncidentDetailScreen.tsx
│   │   ├── TopologyScreen.tsx
│   │   └── SettingsScreen.tsx
│   └── services/
│       ├── api.ts              # API client with JWT auth
│       └── notifications.ts   # Push notification handling
├── app.json
├── package.json
├── tsconfig.json
└── babel.config.js
```

## API Integration

The mobile app connects to the OmniWatch 2.0 backend API:

- REST endpoints for incident, topology, and settings data
- WebSocket support for real-time event streaming
- JWT authentication for secure access

## Configuration

Configure server URL in Settings screen or via environment variables:

```
EXPO_PUBLIC_API_URL=http://localhost:8000
```
