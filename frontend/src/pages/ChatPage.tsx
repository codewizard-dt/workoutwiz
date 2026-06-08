import { useRef, useEffect, useState, type KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, AlertTriangle } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { useWorkouts } from '../hooks/useWorkouts'
import { useMe } from '@/hooks'
import { ChatBubble } from '@/components/ChatBubble'
import { TypingBubble } from '@/components/TypingBubble'
import { WorkoutCard } from '@/components/WorkoutCard'
import { FeedbackForm } from '@/components/FeedbackForm'
import { cn } from '@/lib/utils'

const PROMPT_CHIPS = [
  "What exercises suit my injuries?",
  "30 min dumbbell workout",
  "Log 3x10 bench at 185",
  "Bench press form tips",
] as const

export default function ChatPage() {
  const { messages, sendMessage, isLoading, error, clearMessages, sessionId } = useChat()
  const { data: workouts, isLoading: workoutsLoading } = useWorkouts()
  const { data: user } = useMe()

  const [draft, setDraft] = useState('')
  const streamRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight
    }
  }, [messages, isLoading])

  function handleSend() {
    const trimmed = draft.trim()
    if (!trimmed || isLoading) return
    void sendMessage(trimmed)
    setDraft('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleChipClick(text: string) {
    if (isLoading) return
    void sendMessage(text)
    setDraft('')
  }

  const recentWorkouts = workouts?.slice(0, 10) ?? []

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
      }}
    >
      {/* Page header */}
      <div
        style={{
          padding: 'var(--space-4) var(--space-6) var(--space-3)',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <h1
          style={{
            fontSize: 'var(--text-2xl)',
            fontWeight: 'var(--weight-bold)',
            letterSpacing: '-0.025em',
            margin: 0,
            color: 'var(--foreground)',
          }}
        >
          AI Coach
        </h1>
        <p
          style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--muted-foreground)',
            marginTop: 'var(--space-1)',
            marginBottom: 0,
          }}
        >
          Ask questions, generate personalized workouts, log activity, or get injury-aware exercise recommendations.
        </p>
      </div>

      {/* Prompt chips — pinned below header, always visible */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
          padding: 'var(--space-2) var(--space-6)',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
          background: 'var(--background)',
        }}
      >
        {PROMPT_CHIPS.map((text) => (
          <button
            key={text}
            type="button"
            className="ww-btn ww-btn--outline ww-btn--sm"
            disabled={isLoading}
            onClick={() => { handleChipClick(text) }}
          >
            {text}
          </button>
        ))}
      </div>

      {/* Previous workouts — mobile: horizontal scrollable row */}
      <div
        className="chat-workouts-mobile"
        style={{
          display: 'none',
          overflowX: 'auto',
          gap: 'var(--space-3)',
          padding: 'var(--space-3) var(--space-4)',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        {workoutsLoading && (
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)', alignSelf: 'center' }}>
            Loading…
          </span>
        )}
        {recentWorkouts.map((w) => (
          <div key={w.id} style={{ minWidth: '200px', flexShrink: 0 }}>
            <WorkoutCard workout={w} to={`/workouts/${w.id}`} />
          </div>
        ))}
        {!workoutsLoading && recentWorkouts.length > 0 && (
          <Link
            to="/workouts"
            style={{
              alignSelf: 'center',
              flexShrink: 0,
              fontSize: 'var(--text-xs)',
              color: 'var(--muted-foreground)',
              textDecoration: 'none',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              All Workouts <ArrowRight size={14} aria-hidden />
            </span>
          </Link>
        )}
      </div>

      {/* Body: chat panel (left) + sidebar (right) */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        {/* Left: chat panel ~65% */}
        <div
          style={{
            flex: '1 1 65%',
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            minWidth: 0,
          }}
        >
          {/* Message stream */}
          <div
            ref={streamRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 'var(--space-4) var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)',
            }}
          >
            {messages.length === 0 && !error && (
              <ChatBubble
                role="assistant"
                content="What are we training today? Ask for a workout, log what you did, or get coaching — I'll route each message to the right agent."
              />
            )}

            {messages.map((msg) => (
              <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <ChatBubble
                  role={msg.role}
                  content={msg.content}
                  route={msg.role === 'assistant' ? msg.route : undefined}
                  confidence={msg.role === 'assistant' ? msg.confidence : undefined}
                  steps={msg.role === 'assistant' ? msg.steps : undefined}
                />
                {msg.role === 'assistant' && msg.route === 'KNOWLEDGE_GRAPH' && msg.kg_result != null && (
                  <div
                    className="ww-card"
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-4)',
                      padding: 'var(--space-4)',
                    }}
                  >
                    {msg.kg_result.fallback_used && (
                      <div
                        style={{
                          border: '1px solid var(--border)',
                          borderRadius: 'var(--radius-md)',
                          padding: 'var(--space-2) var(--space-3)',
                          fontSize: 'var(--text-xs)',
                          color: 'var(--muted-foreground)',
                          background: 'var(--muted)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--space-2)',
                        }}
                      >
                        <AlertTriangle size={14} aria-hidden style={{ flexShrink: 0 }} />
                        <span>Limited options due to injury constraints — fallback exercises shown.</span>
                      </div>
                    )}
                    {msg.kg_result.overall_reasoning && (
                      <p
                        style={{
                          fontSize: 'var(--text-sm)',
                          color: 'var(--muted-foreground)',
                          margin: 0,
                          lineHeight: 1.6,
                        }}
                      >
                        {msg.kg_result.overall_reasoning}
                      </p>
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                      <h2
                        style={{
                          fontSize: 'var(--text-base)',
                          fontWeight: 'var(--weight-semibold)',
                          color: 'var(--foreground)',
                          margin: 0,
                        }}
                      >
                        Recommended Exercises ({msg.kg_result.exercises.length})
                      </h2>
                      {msg.kg_result.exercises.map((ex) => (
                        <div
                          key={ex.exercise_id}
                          style={{
                            border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-md)',
                            padding: 'var(--space-4)',
                            background: 'var(--surface-card)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 'var(--space-2)',
                          }}
                        >
                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: 'var(--space-3)',
                              flexWrap: 'wrap',
                            }}
                          >
                            <span
                              style={{
                                fontSize: 'var(--text-base)',
                                fontWeight: 'var(--weight-semibold)',
                                color: 'var(--foreground)',
                              }}
                            >
                              {ex.name}
                            </span>
                            <span
                              style={{
                                fontSize: 'var(--text-sm)',
                                color: 'var(--muted-foreground)',
                                background: 'var(--muted)',
                                borderRadius: 'var(--radius-sm)',
                                padding: '2px var(--space-2)',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {ex.sets != null && ex.reps != null
                                ? `${ex.sets} × ${ex.reps} reps`
                                : ex.sets != null && ex.duration_seconds != null
                                  ? `${ex.sets} × ${ex.duration_seconds}s`
                                  : ex.sets != null
                                    ? `${ex.sets} sets`
                                    : ex.duration_seconds != null
                                      ? `${ex.duration_seconds}s`
                                      : ''}
                            </span>
                          </div>
                          {ex.reasoning && (
                            <p
                              style={{
                                fontSize: 'var(--text-sm)',
                                color: 'var(--muted-foreground)',
                                margin: 0,
                                lineHeight: 1.5,
                              }}
                            >
                              {ex.reasoning}
                            </p>
                          )}
                          {user?.id != null && (
                            <FeedbackForm
                              compact
                              exerciseId={ex.exercise_id}
                              memberId={user.id}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {error && (
              <div
                style={{
                  border: '1px solid var(--destructive)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3) var(--space-4)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--destructive)',
                  background: 'color-mix(in srgb, var(--destructive) 8%, transparent)',
                }}
              >
                <strong>Error:</strong> {error}
              </div>
            )}

            {isLoading && <TypingBubble label="Routing" />}
          </div>

          {/* Composer */}
          <div
            className="chat-composer-sticky"
            style={{
              borderTop: '1px solid var(--border)',
              padding: 'var(--space-3) var(--space-4)',
              flexShrink: 0,
              background: 'var(--background)',
            }}
          >
            <div
              style={{
                display: 'flex',
                gap: 'var(--space-2)',
                alignItems: 'flex-end',
              }}
            >
              <textarea
                placeholder="Ask a question, request a workout, or log a session…"
                value={draft}
                onChange={(e) => {
                  setDraft(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
                }}
                onKeyDown={handleKeyDown}
                style={{
                  flex: 1,
                  resize: 'none',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-strong)',
                  padding: 'var(--space-2) var(--space-3)',
                  fontSize: 'var(--text-sm)',
                  background: 'var(--surface-card)',
                  color: 'var(--foreground)',
                  fontFamily: 'inherit',
                  lineHeight: 1.5,
                  outline: 'none',
                  minHeight: '2.5rem',
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}
              />
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 'var(--space-1)',
                }}
              >
                <button
                  type="button"
                  className={cn('ww-btn ww-btn--gradient ww-btn--sm')}
                  disabled={!draft.trim() || isLoading}
                  onClick={handleSend}
                  aria-label="Send message"
                >
                  {isLoading ? '…' : 'Send'}
                </button>
                {messages.length > 0 && (
                  <button
                    type="button"
                    className="ww-btn ww-btn--ghost ww-btn--sm"
                    onClick={clearMessages}
                    aria-label="Clear conversation"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            <p
              style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--muted-foreground)',
                margin: 'var(--space-2) 0 0',
              }}
            >
              Session: <span className="ww-num">{sessionId.slice(0, 8)}…</span>
            </p>
          </div>
        </div>

        {/* Right: previous workouts sidebar ~35% — desktop only */}
        <div
          className="chat-sidebar-desktop"
          style={{
            flex: '0 0 35%',
            maxWidth: '320px',
            borderLeft: '1px solid var(--border)',
            overflow: 'hidden',
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
          }}
        >
          {/* Pinned header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}
          >
            <span
              style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--weight-semibold)',
                color: 'var(--foreground)',
              }}
            >
              Recent Workouts
            </span>
            <Link
              to="/workouts"
              style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--muted-foreground)',
                textDecoration: 'none',
              }}
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                All Workouts <ArrowRight size={14} aria-hidden />
              </span>
            </Link>
          </div>

          {/* Scrollable cards container */}
          <div
            style={{
              overflowY: 'auto',
            }}
          >
            {workoutsLoading && (
              <>
                {[0, 1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    style={{
                      height: '72px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--muted)',
                      opacity: 0.6,
                    }}
                  />
                ))}
              </>
            )}

            {!workoutsLoading && recentWorkouts.length === 0 && (
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
                No workouts yet.{' '}
                <Link to="/workouts/new" style={{ color: 'var(--foreground)', textDecoration: 'underline' }}>
                  Start one!
                </Link>
              </p>
            )}

            {recentWorkouts.map((w) => (
              <WorkoutCard key={w.id} workout={w} to={`/workouts/${w.id}`} />
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .chat-workouts-mobile { display: flex !important; }
          .chat-sidebar-desktop { display: none !important; }
          .chat-composer-sticky {
            position: sticky;
            bottom: 0;
          }
        }
      `}</style>
    </div>
  )
}
