/**
 * OmniWatch 2.0 — Unified Theme System
 * All colors, spacing, and design tokens used across the frontend.
 */

export const colors = {
  primary: '#00e5ff',
  success: '#00e676',
  warning: '#ffc107',
  error: '#ff1744',
  info: '#2196f3',
  background: '#0a0a1a',
  card: '#1a1a2e',
  border: '#2a2a3e',
  accent: '#7f5af0',
  text: {
    primary: '#ffffff',
    secondary: '#e0e0e0',
    muted: '#9e9e9e',
    subtle: '#616161',
  },
} as const

export const severityColors: Record<string, string> = {
  P1: colors.error,
  CRITICAL: colors.error,
  P2: '#ff6d00',
  HIGH: '#ff6d00',
  P3: colors.warning,
  MEDIUM: colors.warning,
  P4: '#66bb6a',
  LOW: '#66bb6a',
}

export const statusColors: Record<string, string> = {
  healthy: colors.success,
  degraded: colors.warning,
  down: colors.error,
  OPEN: colors.error,
  INVESTIGATING: colors.warning,
  RESOLVED: colors.success,
  MONITORING: colors.info,
}

export const confidenceColor = (score: number): string => {
  if (score >= 0.8) return colors.success
  if (score >= 0.6) return colors.warning
  return colors.error
}
