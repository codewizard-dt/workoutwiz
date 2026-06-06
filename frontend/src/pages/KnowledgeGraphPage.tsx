import { useState } from 'react'
import { useMe } from '@/hooks'
import { useKGRecommend } from '@/hooks/useKGRecommend'
import { FeedbackForm } from '@/components/FeedbackForm'

interface RecommendedExercise {
  exercise_id: string
  name: string
  sets?: number
  reps?: number
  duration_seconds?: number
  weight_kg?: number
  reasoning: string
}

interface KGRecommendResponse {
  member_id: string
  exercises: RecommendedExercise[]
  overall_reasoning: string
  skipped_exercise_ids: string[]
  fallback_used: boolean
}

export default function KnowledgeGraphPage() {
  const { data: user } = useMe()
  const [query, setQuery] = useState('')

  const { mutate, data, isPending, isError, error, reset } = useKGRecommend()

  function handleSubmit(e: React.SyntheticEvent) {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || !user?.id) return
    reset()
    mutate({ memberId: user.id, query: trimmed })
  }

  const result = data as KGRecommendResponse | undefined

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
          Get a personalized workout recommendation powered by your training history and the knowledge graph.
        </p>
      </div>

      {/* Content */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'var(--space-6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-6)',
          maxWidth: '720px',
        }}
      >
        {/* Query form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <label
            htmlFor="kg-query"
            style={{
              fontSize: 'var(--text-sm)',
              fontWeight: 'var(--weight-semibold)',
              color: 'var(--foreground)',
            }}
          >
            What are your goals or constraints today?
          </label>
          <textarea
            id="kg-query"
            rows={3}
            placeholder="e.g. Upper body strength, no shoulder injuries, 45 minutes available"
            value={query}
            onChange={(e) => { setQuery(e.target.value) }}
            style={{
              resize: 'vertical',
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
          <button
            type="submit"
            className="ww-btn ww-btn--gradient ww-btn--sm"
            disabled={!query.trim() || isPending || !user?.id}
            style={{ alignSelf: 'flex-start' }}
          >
            {isPending ? 'Generating…' : 'Get Recommendation'}
          </button>
        </form>

        {/* Loading state */}
        {isPending && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-3)',
            }}
          >
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                style={{
                  height: '80px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--muted)',
                  opacity: 0.6,
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
            ))}
          </div>
        )}

        {/* Error state */}
        {isError && (
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
            <strong>Error:</strong>{' '}
            {error instanceof Error ? error.message : 'Failed to get recommendation. Please try again.'}
          </div>
        )}

        {/* Results */}
        {result && !isPending && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {/* Fallback notice */}
            {result.fallback_used && (
              <div
                style={{
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-3) var(--space-4)',
                  fontSize: 'var(--text-sm)',
                  color: 'var(--muted-foreground)',
                  background: 'var(--muted)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)',
                }}
              >
                <span>⚠️</span>
                <span>Limited options due to injury constraints.</span>
              </div>
            )}

            {/* Overall explanation */}
            {result.overall_reasoning && (
              <p
                style={{
                  fontSize: 'var(--text-sm)',
                  color: 'var(--muted-foreground)',
                  margin: 0,
                  lineHeight: 1.6,
                }}
              >
                {result.overall_reasoning}
              </p>
            )}

            {/* Exercise cards */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-3)',
              }}
            >
              <h2
                style={{
                  fontSize: 'var(--text-base)',
                  fontWeight: 'var(--weight-semibold)',
                  color: 'var(--foreground)',
                  margin: 0,
                }}
              >
                Recommended Exercises ({result.exercises.length})
              </h2>
              {result.exercises.map((ex) => (
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
                  <FeedbackForm
                    exerciseId={ex.exercise_id}
                    memberId={result.member_id}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty state after submit with no results */}
        {result && !isPending && result.exercises.length === 0 && (
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
            No recommendations found. Try a different query.
          </p>
        )}
      </div>
    </div>
  )
}
