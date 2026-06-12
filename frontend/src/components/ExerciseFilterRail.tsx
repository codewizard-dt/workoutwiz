import { Search, X, Repeat, Clock, Dumbbell } from 'lucide-react'
import type { CSSProperties, ReactNode } from 'react'
import type { ExerciseFacets } from '@/types'
import type { ExerciseFilterState, ModalityKey } from './exerciseFilters'
import { EMPTY_FILTERS } from './exerciseFilters'

const numStyle: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontVariantNumeric: 'tabular-nums slashed-zero',
}

function toggle<T>(list: T[], item: T): T[] {
  return list.includes(item) ? list.filter((x) => x !== item) : [...list, item]
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      className="ww-tag"
      data-active={active}
      onClick={onClick}
      style={{
        cursor: 'pointer',
        background: active ? 'var(--ember-500)' : undefined,
        color: active ? 'var(--primary-foreground)' : undefined,
        borderColor: active ? 'var(--ember-500)' : undefined,
      }}
    >
      {children}
    </button>
  )
}

function FilterSection({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <span
        style={{
          fontSize: 'var(--text-2xs)',
          fontWeight: 'var(--weight-semibold)',
          letterSpacing: 'var(--tracking-caps)',
          textTransform: 'uppercase',
          color: 'var(--muted-foreground)',
        }}
      >
        {label}
      </span>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1-5)' }}>{children}</div>
    </div>
  )
}

interface Props {
  facets?: ExerciseFacets
  value: ExerciseFilterState
  onChange: (next: ExerciseFilterState) => void
  resultCount: number
  totalCount: number
}

const MODALITIES: { key: ModalityKey; label: string; icon: ReactNode }[] = [
  { key: 'reps', label: 'Reps', icon: <Repeat size={13} /> },
  { key: 'duration', label: 'Time', icon: <Clock size={13} /> },
  { key: 'weight', label: 'Weighted', icon: <Dumbbell size={13} /> },
]

export function ExerciseFilterRail({ facets, value, onChange, resultCount, totalCount }: Props) {
  const hasActive =
    value.name !== '' ||
    value.muscles.length > 0 ||
    value.equipment.length > 0 ||
    value.patterns.length > 0 ||
    value.modality.length > 0 ||
    value.tier !== null

  const colLabelStyle: React.CSSProperties = {
    fontSize: 'var(--text-2xs)',
    fontWeight: 'var(--weight-semibold)',
    letterSpacing: 'var(--tracking-caps)',
    textTransform: 'uppercase',
    color: 'var(--muted-foreground)',
    backgroundColor: 'var(--surface-sunken)',
    padding: 'var(--space-3)',
    borderBottom: '1px solid var(--border)',
  }
  const colContentStyle: React.CSSProperties = {
    height: '7rem',
    overflowY: 'auto',
    padding: 'var(--space-2)',
  }

  return (
    <div className="ww-card" style={{ padding: 'var(--space-4)', gap: 'var(--space-4)' }}>
      {/* Search + count */}
      <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="ww-input-wrap" style={{ position: 'relative', flex: '1 1 240px' }}>
          <Search
            size={15}
            className="ww-input-wrap__icon"
            style={{ position: 'absolute', left: 'var(--space-3)', top: '50%', transform: 'translateY(-50%)', color: 'var(--muted-foreground)', pointerEvents: 'none' }}
          />
          <input
            id="name-filter"
            className="ww-input ww-input--with-icon"
            placeholder="Search exercises…"
            value={value.name}
            onChange={(e) => { onChange({ ...value, name: e.target.value }) }}
            style={{ width: '100%' }}
          />
        </div>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
          <span style={{ ...numStyle, color: 'var(--foreground)', fontWeight: 'var(--weight-semibold)' }}>{resultCount}</span>
          {' '}of <span style={numStyle}>{totalCount}</span>
        </span>
        {hasActive && (
          <button
            type="button"
            className="ww-btn ww-btn--ghost ww-btn--sm"
            onClick={() => { onChange(EMPTY_FILTERS) }}
          >
            <X size={14} />
            Clear all
          </button>
        )}
      </div>

      {/* Row 1: Tracked by + Priority tier */}
      <div style={{ display: 'flex', gap: 'var(--space-6)', flexWrap: 'wrap' }}>
        <FilterSection label="Tracked by">
          {MODALITIES.map((m) => (
            <Chip
              key={m.key}
              active={value.modality.includes(m.key)}
              onClick={() => { onChange({ ...value, modality: toggle(value.modality, m.key) }) }}
            >
              {m.icon}
              {m.label}
            </Chip>
          ))}
        </FilterSection>

        <FilterSection label="Priority tier">
          {[1, 2, 3].map((t) => (
            <Chip
              key={t}
              active={value.tier === t}
              onClick={() => { onChange({ ...value, tier: value.tier === t ? null : t }) }}
            >
              Tier <span style={numStyle}>{t}</span>
            </Chip>
          ))}
        </FilterSection>
      </div>

      {/* Row 2: Muscle groups | Equipment | Movement pattern */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', border: '1px solid var(--border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border)' }}>
          <div style={colLabelStyle}>Muscle groups</div>
          <div style={colContentStyle}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1-5)' }}>
              {facets?.muscle_groups.map((f) => (
                <Chip
                  key={f.value}
                  active={value.muscles.includes(f.value)}
                  onClick={() => { onChange({ ...value, muscles: toggle(value.muscles, f.value) }) }}
                >
                  {f.value}
                </Chip>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border)' }}>
          <div style={colLabelStyle}>Equipment</div>
          <div style={colContentStyle}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1-5)' }}>
              {facets?.equipment.map((f) => (
                <Chip
                  key={f.value}
                  active={value.equipment.includes(f.value)}
                  onClick={() => { onChange({ ...value, equipment: toggle(value.equipment, f.value) }) }}
                >
                  {f.value}
                </Chip>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={colLabelStyle}>Movement pattern</span>
          <div style={colContentStyle}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1-5)' }}>
              {facets?.movement_patterns.map((f) => (
                <Chip
                  key={f.value}
                  active={value.patterns.includes(f.value)}
                  onClick={() => { onChange({ ...value, patterns: toggle(value.patterns, f.value) }) }}
                >
                  {f.value}
                </Chip>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
