import { useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import { Dumbbell, Layers, Wrench, ShieldCheck, ShieldAlert } from 'lucide-react'
import { useExercises } from '@/hooks/useExercises'
import { useExerciseFacets } from '@/hooks/useExerciseFacets'
import { useFeedbackSummary } from '@/hooks/useFeedbackSummary'
import { useContraindications } from '@/hooks/useContraindications'
import { useCoachBrief } from '@/hooks/useCoachBrief'
import { StatTile } from '@/components/StatTile'
import { ExerciseCard } from '@/components/ExerciseCard'
import { ExerciseFilterRail } from '@/components/ExerciseFilterRail'
import { EMPTY_FILTERS } from '@/components/exerciseFilters'
import type { ExerciseFilterState } from '@/components/exerciseFilters'
import { ExerciseDetailDrawer } from '@/components/ExerciseDetailDrawer'
import { AddExerciseModal } from '@/components/AddExerciseModal'
import type { AddDraftSet } from '@/components/AddExerciseModal'
import type { Contraindication, Exercise, FeedbackSummaryItem } from '@/types'

const numStyle: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontVariantNumeric: 'tabular-nums slashed-zero',
}


function applyFilters(list: Exercise[], f: ExerciseFilterState): Exercise[] {
  const name = f.name.trim().toLowerCase()
  return list.filter((ex) => {
    if (name && !ex.name.toLowerCase().includes(name)) return false
    if (f.muscles.length > 0 && !ex.muscle_groups.some((m) => f.muscles.includes(m))) return false
    if (f.equipment.length > 0 && !ex.equipment_required.some((e) => f.equipment.includes(e))) return false
    if (f.patterns.length > 0 && !ex.movement_patterns.some((p) => f.patterns.includes(p))) return false
    if (f.tier !== null && ex.priority_tier !== f.tier) return false
    for (const mod of f.modality) {
      if (mod === 'reps' && !ex.is_reps) return false
      if (mod === 'duration' && !ex.is_duration) return false
      if (mod === 'weight' && !ex.supports_weight) return false
    }
    return true
  })
}


export default function ExercisesPage() {
  const [filters, setFilters] = useState<ExerciseFilterState>(EMPTY_FILTERS)
  const [safetyLensOn, setSafetyLensOn] = useState(false)
  const [addTarget, setAddTarget] = useState<Exercise | null>(null)
  const [detail, setDetail] = useState<Exercise | null>(null)

  // Whole catalog (50 rows) — filtered client-side so counts stay consistent and
  // the drawer can resolve bilateral pairs without extra round-trips.
  const { data: allExercises, isLoading, isError } = useExercises()
  const { data: facets } = useExerciseFacets()
  const { data: feedbackData } = useFeedbackSummary()
  const { data: contra } = useContraindications(safetyLensOn)
  const { data: brief } = useCoachBrief()

  const exercises = useMemo(() => allExercises ?? [], [allExercises])
  const filtered = useMemo(() => applyFilters(exercises, filters), [exercises, filters])

  const feedbackMap = useMemo(() => {
    const m = new Map<string, FeedbackSummaryItem>()
    feedbackData?.items.forEach((i) => m.set(i.exercise_id, i))
    return m
  }, [feedbackData])

  const contraMap = useMemo(() => {
    const m = new Map<string, Contraindication>()
    contra?.items.forEach((i) => m.set(i.exercise_id, i))
    return m
  }, [contra])

  const muscleCount = facets?.muscle_groups.length ?? new Set(exercises.flatMap((e) => e.muscle_groups)).size
  const equipmentCount = facets?.equipment.length ?? new Set(exercises.flatMap((e) => e.equipment_required)).size
  const flaggedCount = contraMap.size
  const injuries = brief?.injuries ?? []

  return (
    <div
      style={{
        padding: 'var(--space-6) var(--space-4)',
        maxWidth: 1100,
        margin: '0 auto',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-5)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
        <div>
          <span
            style={{
              fontSize: 'var(--text-2xs)',
              fontWeight: 'var(--weight-semibold)',
              letterSpacing: 'var(--tracking-caps)',
              textTransform: 'uppercase',
              color: 'var(--ember-600)',
            }}
          >
            Movement library
          </span>
          <h1 style={{ margin: 'var(--space-1) 0 var(--space-1)', fontSize: 'var(--text-2xl)', fontWeight: 'var(--weight-semibold)', letterSpacing: 'var(--tracking-tight)' }}>
            Exercises
          </h1>
          <p style={{ margin: 0, fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
            The movement dataset used to ground every plan and log.
          </p>
        </div>

        <button
          type="button"
          data-testid="safety-lens-toggle"
          className={`ww-btn ${safetyLensOn ? 'ww-btn--gradient' : 'ww-btn--outline'}`}
          aria-pressed={safetyLensOn}
          onClick={() => { setSafetyLensOn((v) => !v) }}
        >
          <ShieldCheck size={16} />
          {safetyLensOn ? 'Safe-for-me on' : 'Safe for me'}
        </button>
      </div>

      {/* Injury banner */}
      {safetyLensOn && (
        <div
          className="ww-card ww-card--flush"
          style={{
            padding: 'var(--space-3) var(--space-4)',
            flexDirection: 'row',
            alignItems: 'center',
            gap: 'var(--space-2)',
            fontSize: 'var(--text-sm)',
            color: injuries.length > 0 ? 'var(--destructive)' : 'var(--muted-foreground)',
          }}
        >
          <ShieldAlert size={16} />
          {injuries.length > 0 ? (
            <span>
              Personalized for your <span style={{ ...numStyle, fontWeight: 'var(--weight-semibold)' }}>{injuries.length}</span>{' '}
              active injur{injuries.length === 1 ? 'y' : 'ies'}: {injuries.map((i) => i.name).join(', ')}.
              {' '}<span style={{ ...numStyle, fontWeight: 'var(--weight-semibold)' }}>{flaggedCount}</span> exercise{flaggedCount === 1 ? '' : 's'} flagged.
            </span>
          ) : (
            <span>No injuries on file for your profile — nothing to flag.</span>
          )}
        </div>
      )}

      {/* Stats */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        <StatTile label="Exercises" value={exercises.length} icon={<Dumbbell />} />
        <StatTile label="Muscle groups" value={muscleCount} icon={<Layers />} />
        <StatTile label="Equipment types" value={equipmentCount} icon={<Wrench />} />
        {safetyLensOn && (
          <StatTile label="Flagged for you" value={flaggedCount} icon={<ShieldAlert />} />
        )}
      </div>

      {/* Filters */}
      <ExerciseFilterRail
        facets={facets}
        value={filters}
        onChange={setFilters}
        resultCount={filtered.length}
        totalCount={exercises.length}
      />

      {isLoading && (
        <p style={{ color: 'var(--muted-foreground)', fontSize: 'var(--text-sm)' }}>Loading exercises…</p>
      )}
      {isError && (
        <p style={{ color: 'var(--destructive)', fontSize: 'var(--text-sm)' }}>Failed to load exercises.</p>
      )}

      {!isLoading && !isError && (
        filtered.length === 0 ? (
          <div
            className="ww-card ww-card--flush"
            style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--muted-foreground)', fontSize: 'var(--text-sm)' }}
          >
            No exercises match your filters.
          </div>
        ) : (
          <div
            data-testid="exercise-grid"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: 'var(--space-4)',
              alignItems: 'stretch',
            }}
          >
            {filtered.map((ex) => (
              <ExerciseCard
                key={ex.id}
                exercise={ex}
                feedback={feedbackMap.get(ex.id)}
                contraindication={contraMap.get(ex.id)}
                safetyLensOn={safetyLensOn}
                onOpen={setDetail}
                onAdd={setAddTarget}
              />
            ))}
          </div>
        )
      )}

      {detail && (
        <ExerciseDetailDrawer
          key={detail.id}
          exercise={detail}
          allExercises={exercises}
          feedback={feedbackMap.get(detail.id)}
          contraindication={contraMap.get(detail.id)}
          safetyLensOn={safetyLensOn}
          memberId={contra?.member_id ?? null}
          onClose={() => { setDetail(null) }}
          onAdd={(ex) => { setAddTarget(ex) }}
          onSelectExercise={(ex) => { setDetail(ex) }}
        />
      )}

      {addTarget && (
        <AddExerciseModal
          exercise={addTarget}
          onClose={() => { setAddTarget(null) }}
          onAdd={() => { /* draft is stored in localStorage inside modal */ }}
        />
      )}
    </div>
  )
}
