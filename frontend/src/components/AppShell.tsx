import { useState, useEffect, Fragment } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAuth } from '../context/AuthContext'
import { useMe } from '@/hooks'
import { Menu, X, UserCheck } from 'lucide-react'
import logoUrl from '@/assets/logo/logo-wordmark.svg'

interface AppShellProps {
  children: React.ReactNode
}

const NAV_LINKS = [
  { to: '/chat', label: 'AI Coach' },
  { to: '/workouts', label: 'Workouts' },
  { to: '/exercises', label: 'Exercises' },
  { to: '/coach', label: 'Coach View' },
] as const

function isNavActive(to: string, pathname: string): boolean {
  if (to === '/workouts') {
    return pathname === '/workouts' || pathname.startsWith('/workouts/') || pathname.startsWith('/workout/')
  }
  return pathname === to || pathname.startsWith(to + '/')
}

export function AppShell({ children }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const { logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { data: me } = useMe()
  const displayName = me?.email
    ? me.email.split('@')[0].split('.')[0].replace(/^./, (c) => c.toUpperCase())
    : null

  const countDraft = () => {
    try {
      // Primary draft (useDraftWorkout → WorkoutNewPage + PhaseTable)
      type Seq = { sets?: unknown[] }
      const seqs = JSON.parse(localStorage.getItem('ww_draft_sequences') ?? '[]') as Seq[]
      const seqCount = Array.isArray(seqs)
        ? seqs.reduce((n, s) => n + (Array.isArray(s.sets) ? s.sets.length : 0), 0)
        : 0
      if (seqCount > 0) return seqCount
      // Fallback: flat draft (ExercisesPage modal)
      const flat = JSON.parse(localStorage.getItem('ww_workout_draft') ?? '[]') as unknown[]
      return Array.isArray(flat) ? flat.length : 0
    } catch { return 0 }
  }

  const [draftCount, setDraftCount] = useState(countDraft)

  useEffect(() => {
    const refresh = () => { setDraftCount(countDraft()) }
    window.addEventListener('storage', refresh)
    window.addEventListener('ww:draft-updated', refresh)
    return () => {
      window.removeEventListener('storage', refresh)
      window.removeEventListener('ww:draft-updated', refresh)
    }
  }, [])

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function closeMenu() {
    setMenuOpen(false)
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100dvh',
        minHeight: 0,
        background: 'var(--background)',
      }}
    >
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 40,
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
          height: '3.25rem',
          padding: '0 var(--space-4)',
          background: 'var(--surface-card, var(--card))',
          borderBottom: '1px solid var(--border)',
        }}
      >
        <Link
          to="/chat"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            textDecoration: 'none',
            color: 'inherit',
            flexShrink: 0,
          }}
        >
          <img
            src={logoUrl}
            alt="futurePro"
            style={{ height: '1.25rem' }}
          />
        </Link>

        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
            marginLeft: 'var(--space-2)',
          }}
          className="topnav-desktop"
        >
          {NAV_LINKS.map((link) => (
            <Fragment key={link.to}>
              {link.to === '/coach' && (
                <span
                  style={{ width: '1px', height: '1.25rem', background: 'var(--border)', flexShrink: 0, margin: '0 var(--space-1)' }}
                  aria-hidden
                />
              )}
              <Link to={link.to} style={{ textDecoration: 'none' }}>
                <button
                  type="button"
                  className={cn(
                    link.to === '/coach'
                      ? 'ww-btn ww-btn--outline ww-btn--sm'
                      : 'ww-btn ww-btn--ghost ww-btn--sm',
                    isNavActive(link.to, location.pathname) && 'ww-btn--secondary',
                  )}
                  style={link.to === '/coach' ? { color: 'var(--amber-600)', borderColor: 'var(--amber-200)' } : undefined}
                >
                  {link.to === '/coach' ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      <UserCheck size={13} aria-hidden />
                      {link.label}
                    </span>
                  ) : link.label}
                </button>
              </Link>
            </Fragment>
          ))}
        </nav>

        <div style={{ flex: 1 }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {displayName && (
            <span
              className="topnav-desktop"
              style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)', whiteSpace: 'nowrap' }}
            >
              Hi, {displayName}!
            </span>
          )}
          <Link to="/workouts/new" style={{ textDecoration: 'none' }} className="topnav-desktop">
            <button type="button" className="ww-btn ww-btn--gradient ww-btn--sm ww-btn--shimmer">
              {draftCount > 0 ? `Current Workout (${draftCount})` : 'Start New Workout'}
            </button>
          </Link>

          <span
            style={{ width: '1px', height: '1.25rem', background: 'var(--border)', flexShrink: 0 }}
            aria-hidden
          />
          <button
            type="button"
            className="ww-btn ww-btn--ghost ww-btn--sm"
            style={{ opacity: 0.65, fontSize: 'var(--text-xs)' }}
            onClick={handleLogout}
            aria-label="Log out"
          >
            Log out
          </button>

          <button
            type="button"
            className="ww-btn ww-btn--ghost ww-iconbtn ww-btn--sm topnav-burger"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
            onClick={() => { setMenuOpen((v) => !v) }}
          >
            {menuOpen ? <X size={20} aria-hidden /> : <Menu size={20} aria-hidden />}
          </button>
        </div>
      </header>

      {menuOpen && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 30 }}
            onClick={closeMenu}
            aria-hidden="true"
          />
          <div
            style={{
              position: 'fixed',
              top: '3.25rem',
              left: 0,
              right: 0,
              zIndex: 35,
              background: 'var(--surface-card, var(--card))',
              borderBottom: '1px solid var(--border)',
              padding: 'var(--space-3) var(--space-4)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-1)',
            }}
          >
            {NAV_LINKS.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                style={{ textDecoration: 'none' }}
                onClick={closeMenu}
              >
                <button
                  type="button"
                  className={cn(
                    'ww-btn ww-btn--ghost',
                    'ww-btn--block',
                    isNavActive(link.to, location.pathname) && 'ww-btn--secondary',
                  )}
                  style={{ justifyContent: 'flex-start' }}
                >
                  {link.label}
                </button>
              </Link>
            ))}
            <Link to="/workouts/new" style={{ textDecoration: 'none' }} onClick={closeMenu}>
              <button
                type="button"
                className="ww-btn ww-btn--gradient ww-btn--block"
                style={{ justifyContent: 'flex-start' }}
              >
                {draftCount > 0 ? `Current Workout (${draftCount})` : 'Start New Workout'}
              </button>
            </Link>
          </div>
        </>
      )}

      <main
        className="ww-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{
            width: '1280px',
            maxWidth: '100%',
            margin: '0 auto',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
          }}
        >
          {children}
        </div>
      </main>
    </div>
  )
}
