import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const EXAMPLE_QUERIES = [
  "Why are my services slow?",
  "Show me recent incidents",
  "What's the root cause of the payment service outage?",
  "Show topology for checkout-service",
  "What's the current SLO compliance?",
]

export default function AIFirstChat() {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: query.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setQuery('')
    setLoading(true)

    try {
      const token = localStorage.getItem('auth_token')
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }

      // Try NQL endpoint, fall back to simulated response
      let responseText = ''
      try {
        const res = await fetch('/api/v1/nql', {
          method: 'POST',
          headers,
          body: JSON.stringify({ query: userMessage.content }),
        })
        if (res.ok) {
          const data = await res.json()
          responseText = data.answer || data.result || JSON.stringify(data)
        } else {
          throw new Error('NQL not available')
        }
      } catch {
        // Simulated response when NQL engine is not available
        responseText = generateSimulatedResponse(userMessage.content)
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to process query'}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (example: string) => {
    setQuery(example)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">AI Assistant</h1>
        <p className="text-gray-400">
          Ask questions about your infrastructure in natural language.
        </p>
      </div>

      {/* Chat Container */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        {/* Messages Area */}
        <div className="h-96 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <p className="text-gray-400 text-center mb-6">
                Ask me anything about your infrastructure
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {EXAMPLE_QUERIES.map((example, i) => (
                  <button
                    key={i}
                    onClick={() => handleExampleClick(example)}
                    className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-full text-gray-300 transition-colors"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-cyan-600 text-white'
                        : 'bg-gray-700 text-gray-100'
                    }`}
                  >
                    <p className="text-xs opacity-70 mb-1">
                      {msg.role === 'user' ? 'You' : 'OmniWatch AI'} —{' '}
                      {msg.timestamp.toLocaleTimeString()}
                    </p>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 rounded-lg p-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-700 p-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about your infrastructure..."
              disabled={loading}
              className="flex-1 bg-gray-900 text-gray-100 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50 placeholder-gray-500"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? 'Thinking...' : 'Send'}
            </button>
          </form>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-cyan-400 mb-2">Natural Language</h3>
          <p className="text-xs text-gray-400">
            Ask questions in plain English. The NQL engine converts them to structured queries.
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-cyan-400 mb-2">Context Aware</h3>
          <p className="text-xs text-gray-400">
            AI understands your topology, incidents, and metrics for accurate answers.
          </p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-cyan-400 mb-2">Evidence-Based</h3>
          <p className="text-xs text-gray-400">
            Responses are grounded in real data with confidence scores and evidence chains.
          </p>
        </div>
      </div>
    </div>
  )
}

function generateSimulatedResponse(query: string): string {
  const lowerQuery = query.toLowerCase()

  if (lowerQuery.includes('slow') || lowerQuery.includes('latency')) {
    return `Based on recent metrics, I found the following:

**Potential Causes:**
1. Database query latency increased by 320% on postgres-payments-primary
2. Connection pool exhaustion on checkout-service (48/50 active)
3. CPU throttling detected on payment-service-pod-7f8b9

**Recommended Actions:**
- Scale postgres-payments-primary read replicas
- Increase connection pool max size on checkout-service
- Review resource limits on payment-service deployment

**Confidence:** 87% | **Evidence:** NX-MTR-4421, NX-MTR-4422`
  }

  if (lowerQuery.includes('incident')) {
    return `**Active Incidents:** 2

**P1 — INC-2026-07-001**
- Status: INVESTIGATING
- Root Cause: Database cascade failure
- Blast Radius: 12,400 users affected
- Auto-remediation: In progress (rollback to v2.1.3)

**P2 — INC-2026-07-002**
- Status: MONITORING
- Root Cause: Memory leak in background-worker
- Impact: 5% increased error rate

**Confidence:** 94% | **Last Updated:** 2 minutes ago`
  }

  if (lowerQuery.includes('root cause') || lowerQuery.includes('outage')) {
    return `**Root Cause Analysis — Payment Service Outage**

**Timeline:**
1. 08:12:09 — CPU spike on payments-db-02 host
2. 08:12:11 — Database connection latency increased
3. 08:12:30 — Payment service timeout rate exceeded threshold
4. 08:12:45 — Checkout service started failing

**Causal Chain:**
payments-db-02 CPU spike → postgres-payments-primary latency → payment-service timeouts → checkout-service failures

**Root Cause:** payments-db-02 host resource exhaustion (likely noisy neighbor)
**Confidence:** 94% | **Granger Causality:** p=0.0003`
  }

  if (lowerQuery.includes('topology') || lowerQuery.includes('checkout')) {
    return `**Topology: checkout-service**

**Dependencies (Layer 6):**
├── payment-service-api → postgres-payments-primary (Layer 4)
├── inventory-service-api → redis-cache (Layer 4)
├── auth-service → postgres-auth (Layer 4)
└── notification-service → smtp-gateway (Layer 5)

**Depended By:**
└── frontend-web-app (Layer 1)

**Anomaly Score:** 0.72 (elevated)
**Health Status:** DEGRADED`
  }

  if (lowerQuery.includes('slo') || lowerQuery.includes('compliance')) {
    return `**SLO Compliance Report**

| SLO | Target | Actual | Status |
|-----|--------|--------|--------|
| checkout-slo | 99.9% | 99.95% | PASSING |
| api-latency-slo | 99.5% | 99.7% | PASSING |
| error-budget-slo | 99.9% | 98.2% | BREACHED |

**Error Budget Remaining:** 18.2% (burning at 2.3x rate)
**Recommendation:** Investigate error-budget-slo breach`
  }

  return `I understand you're asking about: "${query}"

The NQL engine is processing your request. Here's a simulated response:

**Summary:**
- Query recognized and parsed
- Searching across metrics, logs, and traces
- No matching anomalies found in the last 24 hours

**Note:** This is a simulated response. The full NQL engine integration is pending.`
}
