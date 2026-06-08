import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Frown, Annoyed, Meh, Smile, Laugh, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

const FACE: Record<number, LucideIcon> = {
  1: Frown,
  2: Annoyed,
  3: Meh,
  4: Smile,
  5: Laugh,
}

// Sentiment scale: red (poor) → grey (neutral) → green (great)
const FACE_COLOR: Record<number, string> = {
  1: '#b91c1c',
  2: '#82383f',
  3: '#4b5563',
  4: '#306a50',
  5: '#15803d',
}

const LABEL: Record<number, string> = {
  1: 'Poor',
  2: 'Fair',
  3: 'OK',
  4: 'Good',
  5: 'Great',
}

function FaceIcon({ n }: { n: number }) {
  const Icon = FACE[n]
  return <Icon size={20} color={FACE_COLOR[n]} aria-hidden />
}

interface RatingWidgetProps {
  value: 1 | 2 | 3 | 4 | 5 | null
  onChange: (v: 1 | 2 | 3 | 4 | 5) => void
  disabled?: boolean
  /** Compact mode: shows a single face button; click to open the full picker popover. */
  compact?: boolean
  label?: string
  /** Alignment of the compact popover relative to the trigger button. Defaults to 'left'. */
  popoverAlign?: 'left' | 'center' | 'right'
}

export function RatingWidget({
  value,
  onChange,
  disabled = false,
  compact = false,
  label,
  popoverAlign = 'left',
}: RatingWidgetProps) {
  const [hovered, setHovered] = useState<number | null>(null)
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  // The popover is portaled to document.body, so it lives outside wrapperRef.
  // Track it separately so the click-outside handler doesn't treat clicks on
  // the rating faces as "outside" and close before their onClick can fire.
  const popoverRef = useRef<HTMLDivElement>(null)
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number } | null>(null)

  // Close popover on click-outside or Escape
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    function onOutside(e: MouseEvent) {
      const target = e.target as Node
      const insideTrigger = wrapperRef.current?.contains(target)
      const insidePopover = popoverRef.current?.contains(target)
      if (!insideTrigger && !insidePopover) {
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
    const Face = value != null ? FACE[value] : Meh
    const faceLabel = value != null ? LABEL[value] : 'Rate'

    // Measure button position when opening so the portal popup can be placed correctly
    function handleToggle() {
      if (!open && wrapperRef.current) {
        const rect = wrapperRef.current.getBoundingClientRect()
        setPopoverPos({ top: rect.top + window.scrollY, left: rect.left + window.scrollX })
      }
      setOpen((o) => !o)
    }

    // Derive portal popup left from alignment prop + measured position
    function portalLeft(pos: { top: number; left: number; }) {
      if (popoverAlign === 'right') return pos.left  // right edge: needs popup width, handled via transform
      if (popoverAlign === 'center') return pos.left  // center: also handled via transform
      return pos.left  // left: align popup left with button left
    }

    return (
      <div ref={wrapperRef} style={{ display: 'inline-block', width: 'fit-content' }}>
        <button
          type="button"
          aria-label={value != null ? `Rated ${faceLabel} — click to change` : 'Rate this exercise'}
          aria-expanded={open}
          aria-haspopup="true"
          disabled={disabled}
          onClick={handleToggle}
          className="ww-btn ww-btn--ghost ww-iconbtn"
          style={{
            fontSize: '1.25rem',
            opacity: disabled ? 0.4 : value != null ? 1 : 0.4,
            transition: 'opacity var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out)',
          }}
          onMouseEnter={(e) => {
            if (!disabled) {
              e.currentTarget.style.boxShadow = '0 0 0 2px var(--accent)'
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = ''
          }}
        >
          <Face size={20} color={value != null ? FACE_COLOR[value] : '#9ca3af'} aria-hidden />
        </button>

        {open && popoverPos !== null && createPortal(
          <div
            ref={popoverRef}
            role="dialog"
            aria-label="Select rating"
            style={{
              position: 'absolute',
              top: popoverPos.top - 8,  // 8px gap above button
              left: portalLeft(popoverPos),
              transform: popoverAlign === 'center'
                ? 'translate(-50%, -100%)'
                : popoverAlign === 'right'
                  ? 'translate(-100%, -100%)'
                  : 'translateY(-100%)',
              zIndex: 9999,
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
                <FaceIcon n={n} />
              </button>
            ))}
          </div>,
          document.body,
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
            <FaceIcon n={n} />
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
