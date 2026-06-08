import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { PartyPopper, AlertTriangle } from 'lucide-react'
import { useCoachBrief } from '../hooks/useCoachBrief'
import { useCoachChat } from '../hooks/useCoachChat'
import { ChatBubble } from '@/components/ChatBubble'
import { TypingBubble } from '@/components/TypingBubble'

const QUICK_PROMPTS = [
  'Show me the brief',
  "How's adherence trending?",
  'Sleep this week',
  'What changed since last week?',
  'Churn risk summary',
  'Latest workout recap',
] as const

const CHURN_COLORS: Record<string, string> = {
  elevated: 'var(--color-danger, #ef4444)',
  moderate: 'var(--color-warning, #f59e0b)',
  low: 'var(--color-success, #22c55e)',
}

// ── Adherence bar chart (pure CSS) ──────────────────────────────────────────

function AdherenceChart({ weeks }: { weeks: { week_of: string; pct: number }[] }) {
  if (!weeks.length) return null

  const maxPct = 100
  const barColor = (pct: number) =>
    pct >= 90 ? 'var(--ember-500, #f97316)' : pct >= 60 ? '#f59e0b' : '#ef4444'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      {weeks.map((w) => (
        <div key={w.week_of} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ width: '5rem', fontSize: '0.75rem', color: 'var(--muted-foreground)', flexShrink: 0 }}>
            {w.week_of.slice(5)}
          </span>
          <div
            style={{
              flex: 1,
              height: '1.25rem',
              background: 'var(--muted)',
              borderRadius: '0.25rem',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${(w.pct / maxPct) * 100}%`,
                background: barColor(w.pct),
                borderRadius: '0.25rem',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <span
            style={{
              width: '2.5rem',
              textAlign: 'right',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: barColor(w.pct),
              flexShrink: 0,
            }}
          >
            {w.pct}%
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function CoachPage() {
  const { data: brief, isLoading: briefLoading, error: briefQueryError } = useCoachBrief()
  const briefError = briefQueryError?.message ?? null
  const { messages, sendMessage, isLoading: chatLoading, error: chatError } = useCoachChat()

  const [draft, setDraft] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatLoading])

  async function handleSend(text?: string) {
    const msg = (text ?? draft).trim()
    if (!msg || chatLoading) return
    setDraft('')
    await sendMessage(msg)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  const churnLevel = brief?.churn_risk.level ?? 'unknown'
  const churnColor = CHURN_COLORS[churnLevel] ?? 'var(--muted-foreground)'

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        padding: 'var(--space-5) var(--space-4)',
        gap: 'var(--space-5)',
        maxWidth: '56rem',
        margin: '0 auto',
        width: '100%',
      }}
    >
      {/* ── Page header ── */}
      <div>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>Coach View</h1>
        <p style={{ fontSize: '0.875rem', color: 'var(--muted-foreground)', margin: '0.25rem 0 0' }}>
          AI copilot for your 1:1 member session
        </p>
      </div>

      {briefLoading && (
        <div style={{ color: 'var(--muted-foreground)', fontSize: '0.875rem' }}>
          Loading member context…
        </div>
      )}

      {briefError && (
        <div
          style={{
            background: 'var(--destructive)',
            color: 'var(--destructive-foreground)',
            borderRadius: '0.5rem',
            padding: 'var(--space-3)',
            fontSize: '0.875rem',
          }}
        >
          {briefError}
        </div>
      )}

      {brief && (
        <>
          {/* ── Member header card ── */}
          <div
            style={{
              background: 'var(--card)',
              border: '1px solid var(--border)',
              borderRadius: '0.75rem',
              padding: 'var(--space-4)',
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--space-4)',
              alignItems: 'flex-start',
            }}
          >
            <div style={{ flex: 1, minWidth: '12rem' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{brief.member_name}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)', marginTop: '0.15rem' }}>
                Age {brief.member_age} · {brief.tier}
              </div>
              <div style={{ marginTop: 'var(--space-2)', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                {brief.goals
                  .sort((a: import('../types').GoalItem, b: import('../types').GoalItem) => a.priority - b.priority)
                  .map((g: import('../types').GoalItem) => (
                    <span
                      key={g.id}
                      style={{
                        fontSize: '0.7rem',
                        background: 'var(--accent)',
                        color: 'var(--accent-foreground)',
                        borderRadius: '999px',
                        padding: '0.15rem 0.55rem',
                      }}
                    >
                      {g.text}
                    </span>
                  ))}
              </div>
            </div>

            {/* Churn risk */}
            <div
              style={{
                flexShrink: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
                gap: 'var(--space-1)',
              }}
            >
              <div
                style={{
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: churnColor,
                  border: `1px solid ${churnColor}`,
                  borderRadius: '999px',
                  padding: '0.2rem 0.7rem',
                }}
              >
                Churn risk: {churnLevel}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--muted-foreground)', textAlign: 'right', maxWidth: '16rem' }}>
                {brief.churn_risk.reasons[0]}
              </div>
            </div>
          </div>

          {/* ── Two-column: Morning brief + Adherence ── */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }} className="coach-grid">
            {/* Morning brief */}
            <div
              style={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '0.75rem',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
                Morning Brief
              </div>
              {brief.morning_tasks.map((task: import('../types').MorningTask, i: number) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    gap: 'var(--space-2)',
                    alignItems: 'flex-start',
                    background: 'var(--muted)',
                    borderRadius: '0.5rem',
                    padding: 'var(--space-3)',
                  }}
                >
                  {task.type === 'celebrate'
                    ? <PartyPopper size={18} strokeWidth={1.75} style={{ flexShrink: 0 }} />
                    : <AlertTriangle size={18} strokeWidth={1.75} style={{ flexShrink: 0 }} />}
                  <div>
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', color: 'var(--muted-foreground)', marginBottom: '0.2rem' }}>
                      {task.type.replace('_', ' ')}
                    </div>
                    <div style={{ fontSize: '0.85rem', lineHeight: 1.4 }}>{task.text}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Adherence trend */}
            <div
              style={{
                background: 'var(--card)',
                border: '1px solid var(--border)',
                borderRadius: '0.75rem',
                padding: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
                Adherence — last 4 weeks
              </div>
              <AdherenceChart weeks={brief.adherence_weeks} />
              {brief.adherence_weeks.length > 1 && (
                <div style={{ fontSize: '0.75rem', color: 'var(--muted-foreground)' }}>
                  Trend:{' '}
                  {brief.adherence_weeks[brief.adherence_weeks.length - 1].pct <
                  brief.adherence_weeks[0].pct ? (
                    <span style={{ color: '#ef4444', fontWeight: 600 }}>↓ declining</span>
                  ) : (
                    <span style={{ color: '#22c55e', fontWeight: 600 }}>↑ improving</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* ── Injury + equipment row ── */}
          {(brief.injuries.length > 0 || brief.equipment.length > 0) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }} className="coach-grid">
              {brief.injuries.length > 0 && (
                <div
                  style={{
                    background: 'var(--card)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.75rem',
                    padding: 'var(--space-4)',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)', marginBottom: 'var(--space-2)' }}>
                    Injuries
                  </div>
                  {brief.injuries.map((inj, i) => (
                    <div key={i} style={{ fontSize: '0.85rem', marginBottom: 'var(--space-2)' }}>
                      <div style={{ fontWeight: 600 }}>{inj.region} — <span style={{ textTransform: 'capitalize' }}>{inj.status}</span></div>
                      <div style={{ color: 'var(--muted-foreground)', fontSize: '0.8rem' }}>{inj.notes}</div>
                    </div>
                  ))}
                </div>
              )}
              {brief.equipment.length > 0 && (
                <div
                  style={{
                    background: 'var(--card)',
                    border: '1px solid var(--border)',
                    borderRadius: '0.75rem',
                    padding: 'var(--space-4)',
                  }}
                >
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)', marginBottom: 'var(--space-2)' }}>
                    Equipment Available
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                    {brief.equipment.map((eq: string) => (
                      <span
                        key={eq}
                        style={{
                          fontSize: '0.75rem',
                          background: 'var(--muted)',
                          borderRadius: '0.25rem',
                          padding: '0.15rem 0.4rem',
                        }}
                      >
                        {eq}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ── Coach copilot chat ── */}
      <div
        style={{
          background: 'var(--card)',
          border: '1px solid var(--border)',
          borderRadius: '0.75rem',
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
          flex: 1,
          minHeight: '24rem',
        }}
      >
        <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
          Coach Copilot
        </div>

        {/* Quick-prompt chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="ww-btn ww-btn--ghost ww-btn--sm"
              style={{ fontSize: '0.75rem' }}
              disabled={chatLoading}
              onClick={() => { void handleSend(prompt) }}
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Message stream */}
        <div
          className="ww-scroll"
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-2)',
            minHeight: '10rem',
            maxHeight: '28rem',
            padding: '0.25rem 0',
          }}
        >
          {messages.length === 0 && (
            <div style={{ color: 'var(--muted-foreground)', fontSize: '0.875rem', textAlign: 'center', marginTop: 'var(--space-4)' }}>
              Ask me anything about {brief?.member_name ?? 'your member'}'s progress, or click a quick-prompt above.
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id}>
              <ChatBubble
                role={msg.role}
                content={msg.content}
              />
              {msg.role === 'assistant' && msg.grounded_facts && msg.grounded_facts.length > 0 && (
                <div
                  style={{
                    marginTop: '0.25rem',
                    marginLeft: '0.5rem',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 'var(--space-1)',
                  }}
                >
                  {msg.grounded_facts.map((fact: string, i: number) => (
                    <span
                      key={i}
                      style={{
                        fontSize: '0.65rem',
                        background: 'var(--accent)',
                        color: 'var(--accent-foreground)',
                        borderRadius: '999px',
                        padding: '0.1rem 0.45rem',
                      }}
                    >
                      {fact}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {chatLoading && <TypingBubble label="Thinking" />}
          {chatError && (
            <div style={{ color: 'var(--destructive)', fontSize: '0.875rem', padding: '0 0.5rem' }}>
              {chatError}
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input row */}
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-end' }}>
          <textarea
            className="ww-scroll"
            style={{
              flex: 1,
              resize: 'none',
              minHeight: '2.5rem',
              maxHeight: '8rem',
              borderRadius: '0.5rem',
              border: '1px solid var(--border)',
              background: 'var(--background)',
              padding: '0.5rem 0.75rem',
              fontSize: '0.875rem',
              fontFamily: 'inherit',
              color: 'inherit',
              outline: 'none',
            }}
            placeholder="Ask about Jordan's adherence, sleep, goals…"
            value={draft}
            rows={1}
            disabled={chatLoading}
            onChange={(e) => { setDraft(e.target.value) }}
            onKeyDown={handleKeyDown}
          />
          <button
            type="button"
            className="ww-btn ww-btn--gradient ww-btn--sm"
            disabled={chatLoading || !draft.trim()}
            onClick={() => { void handleSend() }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
