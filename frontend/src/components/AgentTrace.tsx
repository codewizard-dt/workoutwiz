export interface AgentStep {
  agent: string
  confidence?: number
  latency_ms?: number
  timestamp?: string
  detail?: string
}

interface AgentTraceProps {
  steps: AgentStep[]
  defaultOpen?: boolean
}

export function AgentTrace({ steps, defaultOpen = false }: AgentTraceProps) {
  return (
    <details open={defaultOpen} style={{ marginTop: 'var(--space-2)' }}>
      <summary
        style={{
          cursor: 'pointer',
          fontSize: 'var(--text-xs)',
          color: 'var(--muted-foreground)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 'var(--space-1)',
          listStyle: 'none',
          userSelect: 'none',
        }}
      >
        Show reasoning
        <span className="ww-num" style={{ opacity: 0.6 }}>
          · {steps.length} agent{steps.length !== 1 ? 's' : ''}
        </span>
      </summary>

      <div
        style={{
          marginTop: 'var(--space-2)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-1-5)',
          paddingLeft: 'var(--space-2)',
          borderLeft: '2px solid var(--border)',
        }}
      >
        {steps.map((step, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1px',
              fontSize: 'var(--text-xs)',
              color: 'var(--muted-foreground)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 'var(--weight-semibold)', color: 'var(--foreground)' }}>
                {step.agent}
              </span>
              {step.confidence != null && (
                <span className="ww-num">conf {step.confidence.toFixed(2)}</span>
              )}
              {step.latency_ms != null && (
                <span className="ww-num">{step.latency_ms} ms</span>
              )}
            </div>
            {step.detail && (
              <span style={{ opacity: 0.75, lineHeight: 1.4 }}>{step.detail}</span>
            )}
          </div>
        ))}
      </div>
    </details>
  )
}
