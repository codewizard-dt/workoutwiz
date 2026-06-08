import { useState, useRef, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCreateWorkout } from '@/hooks/useWorkouts'
import { useExercises } from '@/hooks/useExercises'
import { useChat } from '@/hooks/useChat'
import { useDraftWorkout } from '@/hooks/useDraftWorkout'
import { ChatBubble } from '@/components/ChatBubble'
import { PhaseTable } from '@/components/PhaseTable'
import { ArrowLeft, Check } from 'lucide-react'
import type { WorkoutSequence, WorkoutSequenceCreate, WorkoutSet, WorkoutSetCreate, WorkoutPhase } from '@/types'

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
    const sets: WorkoutSet[] = exercises.flatMap((ex, exIdx) =>
      Array.from({ length: ex.sets }, (_, setIdx): WorkoutSet => ({
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
  const [duration, setDuration] = useState(30)
  const [excludedIds, setExcludedIds] = useState<string[]>([])
  const [allowedEquipment, setAllowedEquipment] = useState<string[]>([])
  const streamRef = useRef<HTMLDivElement>(null)

  const DURATION_OPTIONS = [15, 30, 45, 60] as const

  const equipmentOptions: string[] = Array.from(
    new Set((exercises ?? []).flatMap((e) => e.equipment_required))
  ).sort()

  const buildConstraintPreamble = (): string => {
    const parts: string[] = []
    if (excludedIds.length > 0) {
      const names = excludedIds
        .map((id) => (exercises ?? []).find((e) => e.id === id)?.name ?? id)
        .join(', ')
      parts.push(`Exclude these exercises: ${names}.`)
    }
    if (allowedEquipment.length > 0) {
      parts.push(`Only use equipment: ${allowedEquipment.join(', ')}.`)
    }
    return parts.join(' ')
  }

  const toggleExcluded = (id: string) => {
    setExcludedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  const toggleEquipment = (eq: string) => {
    setAllowedEquipment((prev) =>
      prev.includes(eq) ? prev.filter((x) => x !== eq) : [...prev, eq]
    )
  }

  const dispatchMessage = (text: string) => {
    const preamble = buildConstraintPreamble()
    const withDuration = `Time window: ${duration} minutes. ${text}`
    const full = [preamble, withDuration].filter(Boolean).join(' ')
    void sendMessage(full)
  }

  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight
    }
  }, [messages, chatLoading])

  const handleSend = () => {
    const text = inputText.trim()
    if (!text) return
    setInputText('')
    dispatchMessage(text)
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
      {
        onSuccess: (result) => {
          clearDraft()
          navigate(`/workouts/${result.id}`)
        }
      }
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
          <ArrowLeft size={14} aria-hidden /> Workouts
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
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Check size={14} aria-hidden /> Use This Workout
                    </span>
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

          {/* Constraints panel */}
          <div
            style={{
              padding: 'var(--space-3) var(--space-4)',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            {/* Exclude exercises */}
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 'var(--space-1)',
                }}
              >
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Exclude exercises
                </span>
                {excludedIds.length > 0 && (
                  <button
                    type="button"
                    className="ww-btn ww-btn--ghost ww-btn--sm"
                    style={{ fontSize: 'var(--text-xs)', padding: '0 var(--space-1)' }}
                    onClick={() => { setExcludedIds([]) }}
                  >
                    Clear ({excludedIds.length})
                  </button>
                )}
              </div>
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 'var(--space-1)',
                  maxHeight: '80px',
                  overflowY: 'auto',
                }}
              >
                {(exercises ?? []).map((ex) => {
                  const active = excludedIds.includes(ex.id)
                  return (
                    <button
                      key={ex.id}
                      type="button"
                      className={`ww-btn ww-btn--outline ww-btn--sm${active ? ' ww-btn--active' : ''}`}
                      style={{
                        fontSize: 'var(--text-xs)',
                        opacity: active ? 1 : 0.7,
                        fontWeight: active ? 'var(--weight-semibold)' : undefined,
                        textDecoration: active ? 'line-through' : undefined,
                        borderColor: active ? 'var(--destructive)' : undefined,
                        color: active ? 'var(--destructive)' : undefined,
                      }}
                      onClick={() => { toggleExcluded(ex.id) }}
                      title={ex.name}
                    >
                      {ex.name}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Available equipment */}
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 'var(--space-1)',
                }}
              >
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Available equipment {allowedEquipment.length === 0 ? '(all)' : `(${allowedEquipment.length} selected)`}
                </span>
                {allowedEquipment.length > 0 && (
                  <button
                    type="button"
                    className="ww-btn ww-btn--ghost ww-btn--sm"
                    style={{ fontSize: 'var(--text-xs)', padding: '0 var(--space-1)' }}
                    onClick={() => { setAllowedEquipment([]) }}
                  >
                    Clear
                  </button>
                )}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                {equipmentOptions.map((eq) => {
                  const active = allowedEquipment.includes(eq)
                  return (
                    <button
                      key={eq}
                      type="button"
                      className={`ww-btn ww-btn--outline ww-btn--sm${active ? ' ww-btn--active' : ''}`}
                      style={{
                        fontSize: 'var(--text-xs)',
                        fontWeight: active ? 'var(--weight-semibold)' : undefined,
                        background: active ? 'var(--primary)' : undefined,
                        color: active ? 'var(--primary-foreground)' : undefined,
                        borderColor: active ? 'var(--primary)' : undefined,
                      }}
                      onClick={() => { toggleEquipment(eq) }}
                    >
                      {eq}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

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
            {/* Session length selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <span
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: 'var(--weight-semibold)',
                  color: 'var(--muted-foreground)',
                  whiteSpace: 'nowrap',
                }}
              >
                Session length
              </span>
              <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                {DURATION_OPTIONS.map((mins) => (
                  <button
                    key={mins}
                    type="button"
                    className={`ww-btn ww-btn--outline ww-btn--sm${duration === mins ? ' ww-btn--gradient' : ''}`}
                    style={{
                      fontSize: 'var(--text-xs)',
                      fontWeight: duration === mins ? 'var(--weight-semibold)' : undefined,
                    }}
                    onClick={() => { setDuration(mins) }}
                  >
                    {mins} min
                  </button>
                ))}
              </div>
            </div>

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
                    dispatchMessage(text)
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
                  setExcludedIds([])
                  setAllowedEquipment([])
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
