import { useState, useRef, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCreateWorkout } from '@/hooks/useWorkouts'
import { useExercises } from '@/hooks/useExercises'
import { useChat } from '@/hooks/useChat'
import { useDraftWorkout } from '@/hooks/useDraftWorkout'
import { ChatBubble } from '@/components/ChatBubble'
import { PhaseTable } from '@/components/PhaseTable'
import { ArrowLeft, Check, Plus, ChevronDown, Search, X } from 'lucide-react'
import type { KGResult, WorkoutSequence, WorkoutSequenceCreate, WorkoutSet, WorkoutSetCreate, WorkoutPhase } from '@/types'

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

/** Convert a KG recommendation (flat exercise list) into a single "main" sequence.
 *
 * The KG pipeline returns slug-style exercise ids that don't match the Postgres
 * exercise UUIDs, so we resolve each recommendation to a real exercise — by id
 * when it already matches, otherwise by name — and skip any that can't be matched
 * (an unmatched id would fail the save FK). */
function kgResultToSets(
  kg: KGResult,
  positionBase: number,
  exercises: { id: string; name: string }[],
): WorkoutSet[] {
  const byId = new Set(exercises.map((e) => e.id))
  const byName = new Map(exercises.map((e) => [e.name.trim().toLowerCase(), e.id]))

  const resolved = kg.exercises
    .map((ex) => {
      const realId = byId.has(ex.exercise_id)
        ? ex.exercise_id
        : byName.get(ex.name.trim().toLowerCase())
      return realId ? { ex, realId } : null
    })
    .filter((x): x is { ex: KGResult['exercises'][number]; realId: string } => x !== null)

  return resolved.flatMap(({ ex, realId }, exIdx) =>
    Array.from({ length: ex.sets ?? 1 }, (_, setIdx): WorkoutSet => ({
      id: `kg-${exIdx}-${setIdx}-${positionBase}`,
      sequence_id: 'kg-main',
      exercise_id: realId,
      set_type: ex.duration_seconds != null && ex.reps == null ? 'CARDIO' : 'STRENGTH',
      position: positionBase + exIdx * 100 + setIdx,
      reps: ex.reps ?? undefined,
      weight_kg: ex.weight_kg ?? undefined,
      duration_s: ex.duration_seconds ?? undefined,
    }))
  )
}

export default function WorkoutNewPage() {
  const navigate = useNavigate()
  const createWorkout = useCreateWorkout()
  const { data: exercises } = useExercises()
  const { messages, sendMessage, isLoading: chatLoading, error: chatError, clearMessages } = useChat()
  const { sequences: draftSequences, setSequences: setDraftSequences, clear: clearDraft } = useDraftWorkout()
  const [inputText, setInputText] = useState('Build me a 30-minute workout.')
  const [duration, setDuration] = useState(30)
  const [excludedIds, setExcludedIds] = useState<string[]>([])
  const [allowedEquipment, setAllowedEquipment] = useState<string[]>([])
  const [intensity, setIntensity] = useState<'challenging' | 'easy' | null>(null)
  const [focus, setFocus] = useState<{ upper: boolean; lower: boolean }>({ upper: false, lower: false })
  const [excludeOpen, setExcludeOpen] = useState(false)
  const [excludeSearch, setExcludeSearch] = useState('')
  const [equipmentOpen, setEquipmentOpen] = useState(false)
  const [equipmentSearch, setEquipmentSearch] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const equipmentRef = useRef<HTMLDivElement>(null)
  const excludeRef = useRef<HTMLDivElement>(null)

  const DURATION_OPTIONS = [15, 30, 45, 60] as const

  const equipmentOptions: string[] = Array.from(
    new Set((exercises ?? []).flatMap((e) => e.equipment_required))
  ).sort()

  // Compose a human-readable workout request from the current setup selections.
  // Called from each selection handler so the chat input always mirrors the
  // setup card — the user can then edit and send when ready.
  const composeRequest = (next: {
    duration: number
    intensity: 'challenging' | 'easy' | null
    focus: { upper: boolean; lower: boolean }
    equipment: string[]
    excluded: string[]
  }): string => {
    const focusPhrase =
      next.focus.upper && next.focus.lower ? 'full body'
        : next.focus.upper ? 'upper body'
          : next.focus.lower ? 'lower body' : ''
    const descriptor = [next.intensity ?? '', focusPhrase].filter(Boolean).join(' ')
    const parts = [
      descriptor
        ? `Build me a ${descriptor} ${next.duration}-minute workout.`
        : `Build me a ${next.duration}-minute workout.`,
    ]
    if (next.equipment.length > 0) {
      parts.push(`Only use this equipment: ${next.equipment.join(', ')}.`)
    }
    if (next.excluded.length > 0) {
      const names = next.excluded
        .map((id) => (exercises ?? []).find((e) => e.id === id)?.name ?? id)
        .join(', ')
      parts.push(`Avoid these exercises: ${names}.`)
    }
    return parts.join(' ')
  }

  const selectDuration = (mins: number) => {
    setDuration(mins)
    setInputText(composeRequest({ duration: mins, intensity, focus, equipment: allowedEquipment, excluded: excludedIds }))
  }

  const toggleIntensity = (value: 'challenging' | 'easy') => {
    const nextIntensity = intensity === value ? null : value
    setIntensity(nextIntensity)
    setInputText(composeRequest({ duration, intensity: nextIntensity, focus, equipment: allowedEquipment, excluded: excludedIds }))
  }

  const toggleFocus = (part: 'upper' | 'lower') => {
    const nextFocus = { ...focus, [part]: !focus[part] }
    setFocus(nextFocus)
    setInputText(composeRequest({ duration, intensity, focus: nextFocus, equipment: allowedEquipment, excluded: excludedIds }))
  }

  const toggleExcluded = (id: string) => {
    const nextExcluded = excludedIds.includes(id) ? excludedIds.filter((x) => x !== id) : [...excludedIds, id]
    setExcludedIds(nextExcluded)
    setInputText(composeRequest({ duration, intensity, focus, equipment: allowedEquipment, excluded: nextExcluded }))
  }

  const clearExcluded = () => {
    setExcludedIds([])
    setInputText(composeRequest({ duration, intensity, focus, equipment: allowedEquipment, excluded: [] }))
  }

  const toggleEquipment = (eq: string) => {
    const nextEquipment = allowedEquipment.includes(eq) ? allowedEquipment.filter((x) => x !== eq) : [...allowedEquipment, eq]
    setAllowedEquipment(nextEquipment)
    setInputText(composeRequest({ duration, intensity, focus, equipment: nextEquipment, excluded: excludedIds }))
  }

  const clearEquipment = () => {
    setAllowedEquipment([])
    setInputText(composeRequest({ duration, intensity, focus, equipment: [], excluded: excludedIds }))
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [messages, chatLoading])

  // Keep the textarea sized to its (often programmatically set) content.
  useEffect(() => {
    const el = inputRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = `${Math.min(el.scrollHeight, 140)}px`
    }
  }, [inputText])

  // Collapse the equipment/exclude pickers when clicking outside their container.
  useEffect(() => {
    if (!equipmentOpen && !excludeOpen) return
    const onPointerDown = (e: MouseEvent) => {
      const target = e.target as Node
      if (equipmentOpen && equipmentRef.current && !equipmentRef.current.contains(target)) {
        setEquipmentOpen(false)
      }
      if (excludeOpen && excludeRef.current && !excludeRef.current.contains(target)) {
        setExcludeOpen(false)
      }
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => { document.removeEventListener('mousedown', onPointerDown) }
  }, [equipmentOpen, excludeOpen])

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

  const handleAddKgToSequence = (kg: KGResult) => {
    const exerciseList = exercises ?? []
    const existing = [...draftSequences]
    const mainIdx = existing.findIndex((s) => s.phase === 'main')
    if (mainIdx >= 0) {
      const base = existing[mainIdx].sets.length * 100
      const newSets = kgResultToSets(kg, base, exerciseList)
      if (newSets.length === 0) return
      existing[mainIdx] = { ...existing[mainIdx], sets: [...existing[mainIdx].sets, ...newSets] }
      setDraftSequences(existing)
    } else {
      const newSets = kgResultToSets(kg, 0, exerciseList)
      if (newSets.length === 0) return
      setDraftSequences([
        ...existing,
        { id: 'kg-main', workout_id: 'generated', phase: 'main', position: existing.length, sets: newSets },
      ])
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

  const excludedExercises = excludedIds
    .map((id) => (exercises ?? []).find((e) => e.id === id))
    .filter((e): e is NonNullable<typeof e> => Boolean(e))

  const excludeMatches = (exercises ?? [])
    .filter((e) => !excludedIds.includes(e.id))
    .filter((e) => e.name.toLowerCase().includes(excludeSearch.trim().toLowerCase()))

  const equipmentMatches = equipmentOptions
    .filter((eq) => !allowedEquipment.includes(eq))
    .filter((eq) => eq.toLowerCase().includes(equipmentSearch.trim().toLowerCase()))

  // ---- Inline style tokens (app.css prototype classes are not bundled) ----
  const labelStyle: React.CSSProperties = {
    fontSize: 'var(--text-xs)',
    fontWeight: 'var(--weight-semibold)',
    color: 'var(--muted-foreground)',
  }
  const eyebrowStyle: React.CSSProperties = {
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: 'var(--ember-600)',
  }
  const chipsRow: React.CSSProperties = { display: 'flex', flexWrap: 'wrap', gap: 6, flex: 1 }
  const chip: React.CSSProperties = {
    fontSize: 12,
    fontWeight: 500,
    padding: '4px 10px',
    borderRadius: 'var(--radius-full)',
    background: 'var(--surface-card, var(--card))',
    border: '1px solid var(--border)',
    color: 'var(--stone-700, var(--foreground))',
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    transition: 'all var(--dur-fast) var(--ease-out)',
  }
  const chipActive: React.CSSProperties = {
    borderColor: 'var(--ember-500)',
    background: 'var(--ember-50)',
    color: 'var(--ember-700)',
    fontWeight: 600,
  }
  // Compact setup row: fixed-width label + wrapping controls
  const setupRow: React.CSSProperties = { display: 'flex', alignItems: 'flex-start', gap: 12 }
  const rowLabel: React.CSSProperties = { ...eyebrowStyle, minWidth: 78, flexShrink: 0, paddingTop: 5 }

  return (
    <div
      style={{
        maxWidth: 1120,
        width: '100%',
        margin: '0 auto',
        padding: '16px 24px 20px',
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
      }}
    >
      {/* Header row: backlink + title together */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <Link
          to="/workouts"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 5,
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--muted-foreground)',
            textDecoration: 'none',
          }}
        >
          <ArrowLeft size={14} aria-hidden /> Workouts
        </Link>
        <span style={{ color: 'var(--border-strong, var(--border))' }}>/</span>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: '-0.02em' }}>New workout</h1>
      </div>

      {createWorkout.isError && (
        <div
          style={{
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-md)',
            background: 'oklch(0.97 0.02 25)',
            color: 'var(--destructive)',
            fontSize: 'var(--text-sm)',
            marginBottom: 'var(--space-3)',
          }}
        >
          {createWorkout.error instanceof Error
            ? createWorkout.error.message
            : 'Failed to create workout'}
        </div>
      )}

      {/* Session setup (compact) */}
      <div
        className="ww-card"
        style={{
          padding: 'var(--space-3)',
          marginBottom: 14,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          flexShrink: 0,
        }}
      >
        {/* Length / Intensity / Focus — one wrapping row of inline groups */}
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '10px 20px' }}>
          {/* Length */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={eyebrowStyle}>Length</span>
            <div style={{ display: 'flex', gap: 6 }}>
              {DURATION_OPTIONS.map((mins) => (
                <button
                  key={mins}
                  type="button"
                  style={duration === mins ? { ...chip, ...chipActive } : chip}
                  onClick={() => { selectDuration(mins) }}
                >
                  {mins} min
                </button>
              ))}
            </div>
          </div>

          {/* Intensity — single-select (either / or / none) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={eyebrowStyle}>Intensity</span>
            <div style={{ display: 'flex', gap: 6 }}>
              {([['challenging', 'Challenging'], ['easy', 'Easy']] as const).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  style={intensity === value ? { ...chip, ...chipActive } : chip}
                  aria-pressed={intensity === value}
                  onClick={() => { toggleIntensity(value) }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Focus — multi-select (0, 1, or 2) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={eyebrowStyle}>Focus</span>
            <div style={{ display: 'flex', gap: 6 }}>
              {([['upper', 'Upper body'], ['lower', 'Lower body']] as const).map(([part, label]) => (
                <button
                  key={part}
                  type="button"
                  style={focus[part] ? { ...chip, ...chipActive } : chip}
                  aria-pressed={focus[part]}
                  onClick={() => { toggleFocus(part) }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Equipment */}
        <div ref={equipmentRef} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={setupRow}>
            <span style={rowLabel}>Equipment</span>
            <div style={chipsRow}>
              <button
                type="button"
                style={chip}
                aria-expanded={equipmentOpen}
                onClick={() => { setEquipmentOpen((v) => !v) }}
              >
                <Plus size={13} aria-hidden />
                Add
                <ChevronDown
                  size={13}
                  aria-hidden
                  style={{ transform: equipmentOpen ? 'rotate(180deg)' : undefined, transition: 'transform var(--dur-base) var(--ease-out)' }}
                />
              </button>
              {allowedEquipment.length === 0 && (
                <span style={{ ...labelStyle, paddingTop: 5 }}>All</span>
              )}
              {allowedEquipment.map((eq) => (
                <button
                  key={eq}
                  type="button"
                  style={{ ...chip, ...chipActive }}
                  onClick={() => { toggleEquipment(eq) }}
                  title={`Remove ${eq}`}
                >
                  {eq}
                  <X size={12} aria-hidden />
                </button>
              ))}
              {allowedEquipment.length > 0 && (
                <button
                  type="button"
                  className="ww-btn ww-btn--ghost ww-btn--xs"
                  style={{ fontSize: 11 }}
                  onClick={clearEquipment}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
          {equipmentOpen && (
            <div style={setupRow}>
              <span style={{ ...rowLabel, paddingTop: 0 }} />
              <div
                style={{
                  flex: 1,
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--space-2)',
                  background: 'var(--surface-sunken, var(--muted))',
                }}
              >
                <div className="ww-input-wrap">
                  <span className="ww-input-wrap__icon"><Search size={15} aria-hidden /></span>
                  <input
                    className="ww-input ww-input--with-icon"
                    placeholder="Search equipment…"
                    value={equipmentSearch}
                    onChange={(e) => { setEquipmentSearch(e.target.value) }}
                  />
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 132, overflowY: 'auto', marginTop: 'var(--space-2)' }}>
                  {equipmentMatches.length === 0 ? (
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>No matches.</span>
                  ) : (
                    equipmentMatches.map((eq) => (
                      <button key={eq} type="button" style={chip} onClick={() => { toggleEquipment(eq) }} title={eq}>
                        {eq}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Exclude */}
        <div ref={excludeRef} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={setupRow}>
            <span style={rowLabel}>Exclude</span>
            <div style={chipsRow}>
              <button
                type="button"
                style={chip}
                aria-expanded={excludeOpen}
                onClick={() => { setExcludeOpen((v) => !v) }}
              >
                <Plus size={13} aria-hidden />
                Add
                <ChevronDown
                  size={13}
                  aria-hidden
                  style={{ transform: excludeOpen ? 'rotate(180deg)' : undefined, transition: 'transform var(--dur-base) var(--ease-out)' }}
                />
              </button>
              {excludedExercises.map((ex) => (
                <button
                  key={ex.id}
                  type="button"
                  style={{ ...chip, borderColor: 'var(--destructive)', color: 'var(--destructive)', fontWeight: 600 }}
                  onClick={() => { toggleExcluded(ex.id) }}
                  title={`Remove ${ex.name}`}
                >
                  {ex.name}
                  <X size={12} aria-hidden />
                </button>
              ))}
              {excludedIds.length > 0 && (
                <button
                  type="button"
                  className="ww-btn ww-btn--ghost ww-btn--xs"
                  style={{ fontSize: 11 }}
                  onClick={clearExcluded}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
          {excludeOpen && (
            <div style={setupRow}>
              <span style={{ ...rowLabel, paddingTop: 0 }} />
              <div
                style={{
                  flex: 1,
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: 'var(--space-2)',
                  background: 'var(--surface-sunken, var(--muted))',
                }}
              >
                <div className="ww-input-wrap">
                  <span className="ww-input-wrap__icon"><Search size={15} aria-hidden /></span>
                  <input
                    className="ww-input ww-input--with-icon"
                    placeholder="Search exercises to exclude…"
                    value={excludeSearch}
                    onChange={(e) => { setExcludeSearch(e.target.value) }}
                  />
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 132, overflowY: 'auto', marginTop: 'var(--space-2)' }}>
                  {excludeMatches.length === 0 ? (
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>No matches.</span>
                  ) : (
                    excludeMatches.map((ex) => (
                      <button key={ex.id} type="button" style={chip} onClick={() => { toggleExcluded(ex.id) }} title={ex.name}>
                        {ex.name}
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Builder: chat left, sequence right — fills remaining height */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.6fr) minmax(0, 1fr)',
          gap: 20,
          flex: 1,
          minHeight: 0,
        }}
      >
        {/* Chat column */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, flexShrink: 0 }}>Coach</div>

          {/* Messages stream — scrolls internally */}
          <div
            style={{
              flex: 1,
              minHeight: 0,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              padding: '6px 2px 12px',
            }}
          >
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
                      <Check size={14} aria-hidden /> Use this workout
                    </span>
                  </button>
                )}
                {msg.role === 'assistant' && msg.kg_result && msg.kg_result.exercises.some((e) => e.exercise_id) && (
                  <button
                    type="button"
                    className="ww-btn ww-btn--gradient ww-btn--sm"
                    style={{ alignSelf: 'flex-start' }}
                    onClick={() => { const k = msg.kg_result; if (k) { handleAddKgToSequence(k) } }}
                  >
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Plus size={14} aria-hidden /> Add to current workout
                    </span>
                  </button>
                )}
              </div>
            ))}
            {chatLoading && <ChatBubble role="assistant" content="Working…" />}
            <div ref={bottomRef} />
          </div>

          {/* Composer (pinned at bottom of the chat column) */}
          <div
            style={{
              flexShrink: 0,
              paddingTop: 10,
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              borderTop: '1px solid var(--border)',
            }}
          >
            {chatError && (
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--destructive)', margin: 0 }}>
                {chatError}
              </p>
            )}
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                gap: 10,
                padding: '8px 8px 8px 16px',
                background: 'var(--surface-card, var(--card))',
                border: '1px solid var(--border-strong, var(--border))',
                borderRadius: 'var(--radius-xl)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <textarea
                ref={inputRef}
                placeholder="Tell the coach what to build or change…"
                value={inputText}
                onChange={(e) => { setInputText(e.target.value) }}
                onKeyDown={handleKeyDown}
                rows={1}
                style={{
                  flex: 1,
                  border: 'none',
                  outline: 'none',
                  resize: 'none',
                  background: 'none',
                  fontFamily: 'var(--font-sans)',
                  fontSize: 15,
                  lineHeight: 1.5,
                  color: 'var(--foreground)',
                  maxHeight: 140,
                  padding: '6px 0',
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
            <p style={{ fontSize: 11, color: 'var(--muted-foreground)', textAlign: 'center', margin: 0 }}>
              Enter to send · Shift + Enter for a new line
            </p>
          </div>
        </div>

        {/* Sequence panel — fills height, body scrolls internally */}
        <aside style={{ minHeight: 0, display: 'flex' }}>
          <div className="ww-card" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                borderBottom: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexShrink: 0,
              }}
            >
              <span style={{ fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)' }}>
                Current sequence
              </span>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
                {draftSequences.reduce((acc, s) => acc + s.sets.length, 0)} sets
              </span>
            </div>

            <div style={{ padding: 'var(--space-4)', flex: 1, minHeight: 0, overflowY: 'auto' }}>
              {draftSequences.length === 0 ? (
                <p
                  style={{
                    fontSize: 13,
                    color: 'var(--muted-foreground)',
                    padding: '24px 14px',
                    textAlign: 'center',
                    border: '1.5px dashed var(--border-strong, var(--border))',
                    borderRadius: 'var(--radius-lg)',
                    margin: 0,
                  }}
                >
                  Nothing yet — ask the coach to build a session.
                </p>
              ) : (
                <PhaseTable
                  sequences={draftSequences}
                  exercises={exercises ?? []}
                  onRemoveSet={(setId) => {
                    const next = draftSequences
                      .map((seq) => ({ ...seq, sets: seq.sets.filter((s) => s.id !== setId) }))
                      .filter((seq) => seq.sets.length > 0)
                    setDraftSequences(next)
                  }}
                />
              )}
            </div>

            <div
              style={{
                padding: 'var(--space-3) var(--space-4)',
                paddingTop: 'var(--space-6)',
                borderTop: '1px solid var(--border)',
                marginBottom: 'var(--space-4)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
                flexShrink: 0,
              }}
            >
              <button
                type="button"
                className="ww-btn ww-btn--gradient"
                style={{ width: '100%', justifyContent: 'center' }}
                disabled={createWorkout.isPending || draftSequences.length === 0}
                onClick={handleSaveWorkout}
              >
                {createWorkout.isPending ? 'Saving…' : 'Save workout'}
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
                    setIntensity(null)
                    setFocus({ upper: false, lower: false })
                    setInputText(composeRequest({ duration, intensity: null, focus: { upper: false, lower: false }, equipment: [], excluded: [] }))
                  }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}