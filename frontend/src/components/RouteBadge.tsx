import { cn } from '@/lib/utils'

interface RouteBadgeProps {
  route: string
  confidence?: number
}

type Variant = 'amber' | 'soft' | 'success' | 'secondary'

const ROUTE_VARIANT: Record<string, Variant> = {
  COACH: 'amber',
  WORKOUT_GENERATE: 'soft',
  WORKOUT_LOG: 'success',
  FALLBACK: 'secondary',
}

const ROUTE_LABEL: Record<string, string> = {
  COACH: 'Coach',
  WORKOUT_GENERATE: 'Generate',
  WORKOUT_LOG: 'Log',
  FALLBACK: 'Fallback',
}

export function RouteBadge({ route, confidence }: RouteBadgeProps) {
  const variant = ROUTE_VARIANT[route] ?? 'secondary'
  const label = ROUTE_LABEL[route] ?? route

  return (
    <span className={cn('ww-badge', `ww-badge--${variant}`)}>
      {label}
      {confidence != null && (
        <span style={{ opacity: 0.75 }}>{Math.round(confidence * 100)}%</span>
      )}
    </span>
  )
}
