import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import wordmarkUrl from '@/assets/logo/logo-wordmark.svg'
import heroUrl from '@/assets/hero/workout-wiz-hero-selected.png'

const FEATURES = [
  {
    num: '01',
    title: 'Injury-Aware by Design',
    desc: 'Every plan is screened by a medical knowledge graph with SNOMED CT grounding. Contraindicated movements are blocked before they reach you.',
  },
  {
    num: '02',
    title: 'Multi-Agent AI Coaching',
    desc: 'Specialized agents for coaching questions, workout generation, and session logging — with routing confidence surfaced on every response.',
  },
  {
    num: '03',
    title: 'Conversational Logging',
    desc: '"3×10 bench at 185" → structured sets, fuzzy-matched to the exercise database, persisted instantly.',
  },
]

const NAV: React.CSSProperties = {
  position: 'fixed',
  top: 20,
  left: 24,
  right: 24,
  zIndex: 50,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '10px 16px 10px 20px',
  borderRadius: 20,
  background: 'rgba(255,255,255,0.10)',
  backdropFilter: 'blur(10px)',
  WebkitBackdropFilter: 'blur(10px)',
  border: '1px solid rgba(255,255,255,0.18)',
  boxShadow: 'inset 1px 1px 0 rgba(255,255,255,0.25), inset -1px -1px 0 rgba(255,255,255,0.10)',
}

const GLASS_BTN: React.CSSProperties = {
  background: 'rgba(255,255,255,0.95)',
  color: '#272a2b',
  border: 'none',
  borderRadius: 14,
  padding: '8px 18px',
  fontSize: 14,
  fontWeight: 550,
  cursor: 'pointer',
  fontFamily: 'inherit',
  lineHeight: 1.1,
  boxShadow: '0 0 2px rgba(0,0,0,0.10), 0 1px 8px rgba(0,0,0,0.14)',
  backdropFilter: 'blur(4px)',
}

const GLASS_BTN_LG: React.CSSProperties = {
  ...GLASS_BTN,
  padding: '13px 28px',
  fontSize: 15,
  borderRadius: 16,
}

export default function LandingPage() {
  const { token } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (token) navigate('/chat', { replace: true })
  }, [token, navigate])

  return (
    <div style={{ minHeight: '100dvh', background: '#ffffff', fontFamily: "'DM Sans', system-ui, sans-serif" }}>

      {/* ── Floating glass nav ── */}
      <nav style={NAV}>
        <Link to="/" style={{ textDecoration: 'none', flexShrink: 0 }}>
          <img
            src={wordmarkUrl}
            alt="futurePro"
            style={{ height: '1rem', width: 'auto', filter: 'brightness(0) invert(1)', display: 'block' }}
          />
        </Link>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Link to="/login" style={{
            textDecoration: 'none',
            color: 'rgba(255,255,255,0.80)',
            fontSize: 14,
            fontWeight: 500,
            padding: '8px 12px',
            lineHeight: 1.1,
          }}>
            Sign in
          </Link>
          <Link to="/register" style={{ textDecoration: 'none' }}>
            <button type="button" style={GLASS_BTN}>Find Your Coach</button>
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section style={{
        position: 'relative',
        minHeight: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url(${heroUrl})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center top',
        }} />
        {/* Future-style gradient: subtle dark at top, heavier at bottom for text legibility */}
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(to bottom, rgba(1,7,3,0.30) 0%, rgba(1,7,3,0.10) 35%, rgba(1,7,3,0.72) 100%)',
        }} />

        {/* Hero copy — bottom-anchored, left-aligned, Future style */}
        <div style={{
          position: 'relative',
          zIndex: 1,
          padding: 'clamp(2.5rem, 5vw, 5rem) clamp(1.5rem, 4vw, 3.5rem)',
          maxWidth: 820,
        }}>
          <h1 style={{
            fontSize: 'clamp(2.75rem, 7vw, 5.5rem)',
            fontWeight: 400,
            color: '#ffffff',
            letterSpacing: '-0.01em',
            lineHeight: 1.0,
            margin: '0 0 1.25rem',
          }}>
            Personal training,{' '}
            <em style={{ fontStyle: 'italic', fontWeight: 400 }}>reimagined.</em>
          </h1>
          <p style={{
            fontSize: 'clamp(0.9375rem, 1.8vw, 1.0625rem)',
            color: 'rgba(255,255,255,0.70)',
            margin: '0 0 2rem',
            lineHeight: 1.6,
            maxWidth: 500,
            fontWeight: 400,
          }}>
            Injury-aware workout planning, multi-agent AI coaching, and conversational session logging — all from a single interface, built for serious athletes.
          </p>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <Link to="/register" style={{ textDecoration: 'none' }}>
              <button type="button" style={GLASS_BTN_LG}>Find Your Coach</button>
            </Link>
            <Link to="/login" style={{
              textDecoration: 'none',
              color: 'rgba(255,255,255,0.65)',
              fontSize: 15,
              fontWeight: 400,
            }}>
              Sign in →
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section style={{
        background: '#ffffff',
        padding: 'clamp(4rem, 8vw, 7rem) clamp(1.5rem, 5vw, 4rem)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          {/* Section header */}
          <div style={{ marginBottom: 'clamp(2.5rem, 5vw, 4.5rem)' }}>
            <p style={{
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: '0.10em',
              textTransform: 'uppercase',
              color: '#b6b7b8',
              margin: '0 0 0.875rem',
            }}>
              How it works
            </p>
            <h2 style={{
              fontSize: 'clamp(2rem, 5vw, 3.5rem)',
              fontWeight: 700,
              letterSpacing: '-0.01em',
              color: '#1c2127',
              margin: '0 0 1rem',
              lineHeight: 1.05,
              maxWidth: 560,
            }}>
              Together, we go further.
            </h2>
            <p style={{
              fontSize: 16,
              color: '#767778',
              lineHeight: 1.6,
              margin: 0,
              maxWidth: 440,
            }}>
              A complete AI fitness stack — from planning to logging — in one interface.
            </p>
          </div>

          {/* Feature cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))',
            gap: '1px',
            background: '#d6d7d7',
            borderRadius: 16,
            overflow: 'hidden',
            border: '1px solid #d6d7d7',
          }}>
            {FEATURES.map((f) => (
              <div key={f.title} style={{
                background: '#ffffff',
                padding: 'clamp(1.75rem, 3vw, 2.5rem)',
              }}>
                <p style={{
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: '#b6b7b8',
                  margin: '0 0 1.5rem',
                }}>
                  {f.num}
                </p>
                <h3 style={{
                  fontSize: 'clamp(1.0625rem, 2.2vw, 1.375rem)',
                  fontWeight: 700,
                  letterSpacing: '-0.01em',
                  color: '#1c2127',
                  margin: '0 0 0.625rem',
                  lineHeight: 1.15,
                }}>
                  {f.title}
                </h3>
                <p style={{
                  fontSize: 14,
                  color: '#767778',
                  margin: 0,
                  lineHeight: 1.65,
                }}>
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Dark motivation section ── */}
      <section style={{
        background: '#010703',
        padding: 'clamp(4rem, 8vw, 7rem) clamp(1.5rem, 5vw, 4rem)',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div style={{ maxWidth: 640 }}>
            <h2 style={{
              fontSize: 'clamp(2rem, 5.5vw, 4rem)',
              fontWeight: 700,
              letterSpacing: '-0.01em',
              color: '#ffffff',
              margin: '0 0 1.25rem',
              lineHeight: 1.0,
            }}>
              Say hello to your motivation buddy.
            </h2>
            <p style={{
              fontSize: 16,
              color: 'rgba(255,255,255,0.50)',
              lineHeight: 1.65,
              margin: '0 0 2rem',
              maxWidth: 480,
            }}>
              Never train alone again. Your AI coach is always in your corner —
              ready to build your program, answer your questions, and celebrate your wins.
            </p>
            <Link to="/register" style={{ textDecoration: 'none' }}>
              <button type="button" style={{
                background: '#ffffff',
                color: '#1c2127',
                border: 'none',
                borderRadius: 14,
                padding: '13px 28px',
                fontSize: 15,
                fontWeight: 600,
                cursor: 'pointer',
                fontFamily: 'inherit',
                lineHeight: 1.1,
              }}>
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{
        background: '#ffffff',
        borderTop: '1px solid #d6d7d7',
        padding: '1.75rem clamp(1.5rem, 5vw, 4rem)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        <img
          src={wordmarkUrl}
          alt="futurePro"
          style={{ height: '0.8125rem', width: 'auto', opacity: 0.35, display: 'block' }}
        />
        <p style={{ fontSize: 12, color: '#b6b7b8', margin: 0 }}>
          AI-powered personal training for serious athletes.
        </p>
      </footer>

    </div>
  )
}
