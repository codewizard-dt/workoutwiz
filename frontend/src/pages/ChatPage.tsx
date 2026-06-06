import { useRef, useEffect, useState, type KeyboardEvent } from 'react'
import { Link } from 'react-router-dom'
import { useChat } from '../hooks/useChat'
import { useWorkouts } from '../hooks/useWorkouts'
import { ChatBubble } from '@/components/ChatBubble'
import { WorkoutCard } from '@/components/WorkoutCard'
import { cn } from '@/lib/utils'

const PROMPT_CHIPS = [
  "What muscles does a deadlift work?",
  "30 min dumbbell workout",
  "Log 3x10 bench at 185",
  "Bench press form tips",
] as const

export default function ChatPage() {
  const { messages, sendMessage, isLoading, error, clearMessages, sessionId } = useChat()
  const { data: workouts, isLoading: workoutsLoading } = useWorkouts()

  const [draft, setDraft] = useState('')
  const streamRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages or loading state change
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

  const recentWorkouts = workouts?.slice(0, 3) ?? []

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
          Chat
        </h1>
        <p
          style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--muted-foreground)',
            marginTop: 'var(--space-1)',
            marginBottom: 0,
          }}
        >
          Ask questions, generate workouts, or log completed activity.
        </p>
      </div>

      {/* Previous workouts — mobile: horizontal scrollable row above chat */}
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
            All Workouts →
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
            {/* Welcome empty state */}
            {messages.length === 0 && !error && (
              <ChatBubble
                role="assistant"
                content="What are we training today? Ask for a workout, log what you did, or get coaching — I'll route each message to the right agent."
              />
            )}

            {messages.map((msg) => (
              <ChatBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                route={msg.role === 'assistant' ? msg.route : undefined}
                confidence={msg.role === 'assistant' ? msg.confidence : undefined}
                steps={msg.role === 'assistant' ? msg.steps : undefined}
              />
            ))}

            {/* API error rendered as system message in the chat list */}
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

            {/* Loading indicator bubble */}
            {isLoading && (
              <ChatBubble
                role="assistant"
                content="Routing…"
              />
            )}
          </div>

          {/* Composer — sticky to bottom on mobile */}
          <div
            className="chat-composer-sticky"
            style={{
              borderTop: '1px solid var(--border)',
              padding: 'var(--space-3) var(--space-4)',
              flexShrink: 0,
              background: 'var(--background)',
            }}
          >
            {/* Prompt chips — visible only when conversation is empty */}
            {messages.length === 0 && (
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 'var(--space-2)',
                  marginBottom: 'var(--space-3)',
                }}
              >
                {PROMPT_CHIPS.map((text) => (
                  <button
                    key={text}
                    type="button"
                    className="ww-btn ww-btn--outline ww-btn--sm"
                    onClick={() => { handleChipClick(text) }}
                  >
                    {text}
                  </button>
                ))}
              </div>
            )}

            <div
              style={{
                display: 'flex',
                gap: 'var(--space-2)',
                alignItems: 'flex-end',
              }}
            >
              <textarea
                rows={2}
                placeholder="Ask a question, request a workout, or log a session…"
                value={draft}
                onChange={(e) => { setDraft(e.target.value) }}
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
                  className={cn(
                    'ww-btn ww-btn--gradient ww-btn--sm',
                  )}
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

            {/* Session ID footer */}
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
            overflowY: 'auto',
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span
              style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--weight-semibold)',
                color: 'var(--foreground)',
              }}
            >
              Previous Workouts
            </span>
            <Link
              to="/workouts"
              style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--muted-foreground)',
                textDecoration: 'none',
              }}
            >
              All Workouts →
            </Link>
          </div>

          {/* Skeleton loading state */}
          {workoutsLoading && (
            <>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    height: '64px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--muted)',
                    opacity: 0.6,
                  }}
                />
              ))}
            </>
          )}

          {!workoutsLoading && recentWorkouts.length === 0 && (
            <p
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--muted-foreground)',
              }}
            >
              No workouts yet.{' '}
              <Link
                to="/workouts/new"
                style={{ color: 'var(--foreground)', textDecoration: 'underline' }}
              >
                Start one!
              </Link>
            </p>
          )}

          {recentWorkouts.map((w) => (
            <WorkoutCard key={w.id} workout={w} to={`/workouts/${w.id}`} />
          ))}
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
