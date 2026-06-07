import { useState, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

const EMOJI: Record<number, string> = {
  1: '😞',
  2: '🙁',
  3: '😐',
  4: '🙂',
  5: '😄',
}

const LABEL: Record<number, string> = {
  1: 'Poor',
  2: 'Fair',
  3: 'OK',
  4: 'Good',
  5: 'Great',
}

interface RatingWidgetProps {
  value: 1 | 2 | 3 | 4 | 5 | null
  onChange: (v: 1 | 2 | 3 | 4 | 5) => void
  disabled?: boolean
  /** Compact mode: shows a single face button; click to open the full picker popover. */
  compact?: boolean
  label?: string
}

export function RatingWidget({
  value,
  onChange,
  disabled = false,
  compact = false,
  label,
}: RatingWidgetProps) {
  const [hovered, setHovered] = useState<number | null>(null)
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Close popover on click-outside or Escape
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    function onOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onOutside)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onOutside)
    }
  }, [open])

  const displayRating = hovered ?? value

  if (compact) {
    const face = value != null ? EMOJI[value] : '😐'
    const faceLabel = value != null ? LABEL[value] : 'Rate'

    return (
      <div ref={wrapperRef} style={{ position: 'relative', display: 'inline-block' }}>
        <button
          type="button"
          aria-label={value != null ? `Rated ${faceLabel} — click to change` : 'Rate this exercise'}
          aria-expanded={open}
          aria-haspopup="true"
          disabled={disabled}
          onClick={() => { setOpen((o) => !o) }}
          className="ww-btn ww-btn--ghost ww-iconbtn"
          style={{
            fontSize: '1.25rem',
            opacity: disabled ? 0.4 : value != null ? 1 : 0.4,
            transition: 'opacity var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out)',
          }}
          onMouseEnter={(e) => {
            if (!disabled) {
              ;(e.currentTarget as HTMLButtonElement).style.boxShadow = '0 0 0 2px var(--accent)'
            }
          }}
          onMouseLeave={(e) => {
            ;(e.currentTarget as HTMLButtonElement).style.boxShadow = ''
          }}
        >
          {face}
        </button>

        {open && (
          <div
            role="dialog"
            aria-label="Select rating"
            style={{
              position: 'absolute',
              bottom: 'calc(100% + var(--space-1))',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 50,
              background: 'var(--popover, var(--card))',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-2)',
              display: 'flex',
              gap: 'var(--space-1)',
              boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            }}
          >
            {([1, 2, 3, 4, 5] as const).map((n) => (
              <button
                key={n}
                type="button"
                aria-label={`${LABEL[n]} — ${n} out of 5`}
                aria-pressed={value === n}
                onClick={() => {
                  onChange(n)
                  setOpen(false)
                }}
                onMouseEnter={() => { setHovered(n) }}
                onMouseLeave={() => { setHovered(null) }}
                className={cn('ww-btn ww-btn--ghost ww-iconbtn', value === n && 'ww-btn--accent')}
                style={{
                  fontSize: '1.25rem',
                  opacity: displayRating === n ? 1 : 0.45,
                  transition: 'opacity var(--dur-fast) var(--ease-out)',
                }}
              >
                {EMOJI[n]}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Expanded mode — full row of 5 faces with hover preview
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
      {label && (
        <span
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--weight-semibold)',
            textTransform: 'uppercase',
            letterSpacing: 'var(--tracking-caps)',
            color: 'var(--muted-foreground)',
          }}
        >
          {label}
        </span>
      )}
      <div
        role="group"
        aria-label="Rating scale"
        style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}
      >
        {([1, 2, 3, 4, 5] as const).map((n) => (
          <button
            key={n}
            type="button"
            aria-label={`${LABEL[n]} — ${n} out of 5`}
            aria-pressed={value === n}
            disabled={disabled}
            onClick={() => { onChange(n) }}
            onMouseEnter={() => { setHovered(n) }}
            onMouseLeave={() => { setHovered(null) }}
            className={cn('ww-btn ww-btn--ghost ww-iconbtn', value === n && 'ww-btn--accent')}
            style={{
              fontSize: '1.25rem',
              opacity: disabled ? 0.4 : displayRating === n ? 1 : 0.45,
              transition: 'opacity var(--dur-fast) var(--ease-out)',
            }}
          >
            {EMOJI[n]}
          </button>
        ))}
        {displayRating != null && (
          <span
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--muted-foreground)',
              marginLeft: 'var(--space-1)',
            }}
          >
            {LABEL[displayRating]}
          </span>
        )}
      </div>
    </div>
  )
}
