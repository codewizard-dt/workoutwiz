import { cn } from '@/lib/utils'

interface EnjoymentScaleProps {
  value: number
  onChange: (v: number) => void
  disabled?: boolean
}

const EMOJI: Record<number, string> = {
  1: '😞',
  2: '🙁',
  3: '😐',
  4: '🙂',
  5: '😄',
}

export function EnjoymentScale({ value, onChange, disabled = false }: EnjoymentScaleProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-1)',
      }}
    >
      {([1, 2, 3, 4, 5] as const).map((n) => (
        <button
          key={n}
          type="button"
          aria-label={`Rate ${n} out of 5`}
          aria-pressed={value === n}
          disabled={disabled}
          onClick={() => { onChange(n) }}
          className={cn(
            'ww-btn ww-btn--ghost ww-iconbtn',
            value === n && 'ww-btn--accent',
          )}
          style={{
            fontSize: '1.25rem',
            opacity: disabled ? 0.5 : value === n ? 1 : 0.45,
            transition: 'opacity var(--dur-fast) var(--ease-out)',
          }}
        >
          {EMOJI[n]}
        </button>
      ))}
    </div>
  )
}
