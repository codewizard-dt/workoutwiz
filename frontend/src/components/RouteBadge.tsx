import { cn } from '@/lib/utils'
import { ShieldCheck, CheckCircle2, HelpCircle, Zap } from 'lucide-react'

interface RouteBadgeProps {
  route: string
  confidence?: number
}

type Variant = 'amber' | 'soft' | 'success' | 'secondary'

const ROUTE_VARIANT: Record<string, Variant> = {
  MEMBER_CONTEXT_KG: 'amber',
  WORKOUT_GENERATE_KG: 'amber',
  WORKOUT_LOG: 'success',
  FALLBACK: 'secondary',
}

const ROUTE_LABEL: Record<string, string> = {
  MEMBER_CONTEXT_KG: 'Personalized',
  WORKOUT_GENERATE_KG: 'Injury-Screened',
  WORKOUT_LOG: 'Logged',
  FALLBACK: 'Clarifying',
}

const ROUTE_DESC: Record<string, string> = {
  MEMBER_CONTEXT_KG: 'Grounded in your training history',
  WORKOUT_GENERATE_KG: 'Knowledge graph · SNOMED CT contraindication gate',
  WORKOUT_LOG: 'Fuzzy-matched to exercise database',
  FALLBACK: 'Routing needs clarification',
}

function RouteIcon({ route }: { route: string }) {
  if (route === 'WORKOUT_GENERATE_KG' || route === 'MEMBER_CONTEXT_KG')
    return <ShieldCheck size={11} aria-hidden />
  if (route === 'WORKOUT_LOG')
    return <CheckCircle2 size={11} aria-hidden />
  if (route === 'FALLBACK')
    return <HelpCircle size={11} aria-hidden />
  return <Zap size={11} aria-hidden />
}

export function RouteBadge({ route, confidence }: RouteBadgeProps) {
  const variant = ROUTE_VARIANT[route] ?? 'secondary'
  const label = ROUTE_LABEL[route] ?? route
  const desc = ROUTE_DESC[route]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
      <span
        className={cn('ww-badge', `ww-badge--${variant}`)}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-1)', alignSelf: 'flex-start' }}
      >
        <RouteIcon route={route} />
        {label}
        {confidence != null && (
          <span
            style={{
              background: 'rgba(0,0,0,0.10)',
              borderRadius: 'var(--radius-full)',
              padding: '0 0.3rem',
              fontSize: 'var(--text-2xs)',
              fontWeight: 'var(--weight-semibold)',
              lineHeight: '1.4',
            }}
          >
            {Math.round(confidence * 100)}%
          </span>
        )}
      </span>
      {desc && (
        <span style={{ fontSize: 'var(--text-2xs)', color: 'var(--muted-foreground)', paddingLeft: '0.05rem' }}>
          {desc}
        </span>
      )}
    </div>
  )
}
