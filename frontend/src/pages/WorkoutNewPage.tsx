import { useState, useRef, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCreateWorkout } from '@/hooks/useWorkouts'
import { useExercises } from '@/hooks/useExercises'
import { useChat } from '@/hooks/useChat'
import { useDraftWorkout } from '@/hooks/useDraftWorkout'
import { ChatBubble } from '@/components/ChatBubble'
import { PhaseTable } from '@/components/PhaseTable'
import type { WorkoutSequenceCreate, WorkoutSetCreate, WorkoutPhase } from '@/types'

const WORKOUT_CHIPS = [
  'Challenging workout',
  'Easy day',
  'Upper body',
  'Lower body',
] as const

function workoutDraftToSequences(draft: import('@/types').WorkoutDraft): WorkoutSequence[] {
  const result: WorkoutSequence[] = []
  const phaseEntries: [WorkoutPhase, import('@/types').WorkoutDraftExercise[]][] = [
    ['warmup', draft.phases.warmup],
    ['main', draft.phases.main],
    ['cooldown', draft.phases.cooldown],
  ]
  phaseEntries.forEach(([phase, exercises], phaseIdx) => {
    if (!exercises.length) return
    const sets = exercises.flatMap((ex, exIdx) =>
      Array.from({ length: ex.sets }, (_, setIdx) => ({
        id: `gen-${phase}-${exIdx}-${setIdx}`,
        sequence_id: `gen-${phase}`,
        exercise_id: ex.id,
        set_type: ex.duration_s != null ? 'CARDIO' : 'STRENGTH',
        position: exIdx * 100 + setIdx,
        reps: ex.reps ? parseInt(ex.reps.split('-')[0]) : undefined,
        weight_kg: undefined as number | undefined,
        duration_s: ex.duration_s ?? undefined,
      }))
    )
    result.push({ id: `gen-${phase}`, workout_id: 'generated', phase, position: phaseIdx, sets })
  })
  return result
}

export default function WorkoutNewPage() {
  const navigate = useNavigate()
  const createWorkout = useCreateWorkout()
  const { data: exercises } = useExercises()
  const { messages, sendMessage, isLoading: chatLoading, error: chatError, clearMessages } = useChat()
  const { sequences: draftSequences, setSequences: setDraftSequences, clear: clearDraft } = useDraftWorkout()
  const [inputText, setInputText] = useState('')
  const streamRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight
    }
  }, [messages, chatLoading])

  const handleSend = () => {
    const text = inputText.trim()
    if (!text) return
    setInputText('')
    void sendMessage(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSaveWorkout = () => {
    const payload: WorkoutSequenceCreate[] = draftSequences.map((seq, seqPos) => ({
      phase: seq.phase,
      position: seqPos,
      sets: seq.sets.map((s, setPos) => {
        const base: WorkoutSetCreate = {
          exercise_id: s.exercise_id,
          set_type: s.set_type,
          position: setPos,
        }
        if (s.set_type === 'STRENGTH') {
          if (s.reps) base.reps = s.reps
          if (s.weight_kg != null) base.weight_kg = s.weight_kg
        } else {
          if (s.duration_s != null) base.duration_s = s.duration_s
        }
        return base
      }),
    }))

    createWorkout.mutate(
      { started_at: new Date().toISOString(), sequences: payload },
      { onSuccess: (result) => {
        clearDraft()
        navigate(`/workouts/${result.id}`)
      } }
    )
  }

  return (
    <div
      style={{
        padding: 'var(--space-5) var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
        minHeight: 0,
        flex: 1,
      }}
    >
      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <Link
          to="/workouts"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
            fontSize: 'var(--text-sm)',
            color: 'var(--muted-foreground)',
            textDecoration: 'none',
          }}
        >
          ← Workouts
        </Link>
        <h1 style={{ margin: 0, fontSize: 'var(--text-xl)', fontWeight: 'var(--weight-semibold)' }}>
          New Workout
        </h1>
      </div>

      {createWorkout.isError && (
        <div
          style={{
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-md)',
            background: 'oklch(0.97 0.02 25)',
            color: 'var(--destructive)',
            fontSize: 'var(--text-sm)',
          }}
        >
          {createWorkout.error instanceof Error
            ? createWorkout.error.message
            : 'Failed to create workout'}
        </div>
      )}

      {/* Builder: chat left, sequence right */}
      <div
        className="builder"
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-4)',
          flex: 1,
          minHeight: 0,
          alignItems: 'start',
        }}
      >
        {/* Chat panel */}
        <div className="ww-card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderBottom: '1px solid var(--border)',
              fontWeight: 'var(--weight-semibold)',
              fontSize: 'var(--text-sm)',
            }}
          >
            Coach
          </div>

          {/* Messages stream */}
          <div
            ref={streamRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 'var(--space-3)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
              minHeight: 320,
              maxHeight: 480,
            }}
          >
            {/* Opening prompt if no messages yet */}
            {messages.length === 0 && (
              <ChatBubble
                role="assistant"
                content="What are we training today? Tell me the focus, duration, and available equipment."
              />
            )}
            {messages.map((msg) => (
              <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                <ChatBubble
                  role={msg.role}
                  content={msg.content}
                  route={msg.route}
                  confidence={msg.confidence}
                  steps={msg.steps}
                />
                {msg.role === 'assistant' && msg.workout_draft && (
                  <button
                    type="button"
                    className="ww-btn ww-btn--gradient ww-btn--sm"
                    style={{ alignSelf: 'flex-start' }}
                    onClick={() => { const d = msg.workout_draft; if (d) { setDraftSequences(workoutDraftToSequences(d)) } }}
                  >
                    ✓ Use This Workout
                  </button>
                )}
              </div>
            ))}
            {chatLoading && (
              <ChatBubble role="assistant" content="Working…" />
            )}
          </div>

          {chatError && (
            <div
              style={{
                padding: 'var(--space-2) var(--space-4)',
                fontSize: 'var(--text-xs)',
                color: 'var(--destructive)',
                borderTop: '1px solid var(--border)',
              }}
            >
              {chatError}
            </div>
          )}

          {/* Composer */}
          <div
            style={{
              padding: 'var(--space-3)',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            {/* Quick-action chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
              {WORKOUT_CHIPS.map((text) => (
                <button
                  key={text}
                  type="button"
                  className="ww-btn ww-btn--outline ww-btn--sm"
                  disabled={chatLoading}
                  onClick={() => {
                    setInputText('')
                    void sendMessage(text)
                  }}
                >
                  {text}
                </button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'flex-end' }}>
              <textarea
                className="ww-input"
                placeholder="Tell the coach what to build or change…"
                value={inputText}
                onChange={(e) => {
                  setInputText(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
                }}
                onKeyDown={handleKeyDown}
                style={{
                  flex: 1,
                  resize: 'none',
                  fontSize: 'var(--text-sm)',
                  minHeight: '2.5rem',
                  maxHeight: '200px',
                  overflowY: 'auto',
                }}
              />
              <button
                type="button"
                className="ww-btn ww-btn--gradient ww-btn--sm"
                onClick={handleSend}
                disabled={chatLoading || !inputText.trim()}
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Sequence panel */}
        <div className="ww-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span style={{ fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)' }}>
              Current Sequence
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
              {draftSequences.reduce((acc, s) => acc + s.sets.length, 0)} sets
            </span>
          </div>

          <div style={{ padding: 'var(--space-4)', flex: 1 }}>
            {draftSequences.length === 0 ? (
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)', textAlign: 'center', padding: 'var(--space-8) 0' }}>
                Nothing yet — ask the coach to build a session.
              </p>
            ) : (
              <PhaseTable
                sequences={draftSequences}
                exercises={exercises ?? []}
              />
            )}
          </div>

          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            <button
              type="button"
              className="ww-btn ww-btn--gradient"
              style={{ width: '100%', justifyContent: 'center' }}
              disabled={createWorkout.isPending || draftSequences.length === 0}
              onClick={handleSaveWorkout}
            >
              {createWorkout.isPending ? 'Saving…' : 'Save Workout'}
            </button>
            {draftSequences.length > 0 && (
              <button
                type="button"
                className="ww-btn ww-btn--ghost ww-btn--sm"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => {
                  clearDraft()
                  clearMessages()
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
