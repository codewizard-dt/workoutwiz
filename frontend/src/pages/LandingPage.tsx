import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import logoUrl from '@/assets/logo/workout-wiz-logo-smile.png'
import heroUrl from '@/assets/hero/workout-wiz-hero-selected.png'

export default function LandingPage() {
  const { token } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (token) navigate('/chat', { replace: true })
  }, [token, navigate])

  return (
    <div style={{ minHeight: '100dvh', background: 'var(--background)' }}>
      {/* ── Hero ── */}
      <section
        style={{
          position: 'relative',
          minHeight: '100dvh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        {/* Hero image */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage: `url(${heroUrl})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center top',
            filter: 'brightness(0.5)',
          }}
        />
        {/* Gradient overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(to bottom, oklch(0 0 0 / 0.2) 0%, oklch(0.08 0.01 40) 100%)',
          }}
        />
        {/* Content */}
        <div
          style={{
            position: 'relative',
            zIndex: 1,
            textAlign: 'center',
            padding: '0 var(--space-6)',
            maxWidth: 720,
          }}
        >
          <img
            src={logoUrl}
            alt="Workout Wiz"
            style={{ width: 80, height: 'auto', marginBottom: 'var(--space-5)', filter: 'drop-shadow(0 4px 12px oklch(0 0 0 / 0.4))' }}
          />
          <h1
            style={{
              fontSize: 'clamp(2.4rem, 6vw, 4.5rem)',
              fontWeight: 800,
              color: '#fff',
              letterSpacing: '-0.03em',
              lineHeight: 1.1,
              margin: '0 0 var(--space-5)',
            }}
          >
            Your AI&nbsp;
            <span
              style={{
                background: 'var(--gradient-ember)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              Strength Coach
            </span>
          </h1>
          <p
            style={{
              fontSize: 'clamp(1rem, 2vw, 1.2rem)',
              color: 'oklch(0.85 0.02 60)',
              margin: '0 0 var(--space-8)',
              lineHeight: 1.65,
            }}
          >
            Generate personalized workouts, log your sessions with smart exercise matching,
            and get real-time coaching — all powered by a multi-agent AI built for serious athletes.
          </p>
          <div
            style={{
              display: 'flex',
              gap: 'var(--space-3)',
              justifyContent: 'center',
              flexWrap: 'wrap',
            }}
          >
            <Link to="/register" style={{ textDecoration: 'none' }}>
              <button
                type="button"
                className="ww-btn ww-btn--gradient"
                style={{ fontSize: '1rem', height: '3rem', padding: '0 2rem' }}
              >
                Get Started Free
              </button>
            </Link>
            <Link to="/login" style={{ textDecoration: 'none' }}>
              <button
                type="button"
                className="ww-btn ww-btn--outline"
                style={{
                  fontSize: '1rem',
                  height: '3rem',
                  padding: '0 2rem',
                  color: '#fff',
                  borderColor: 'oklch(1 0 0 / 0.3)',
                  background: 'oklch(1 0 0 / 0.08)',
                }}
              >
                Sign In
              </button>
            </Link>
          </div>
        </div>
        {/* Scroll cue */}
        <div
          style={{
            position: 'absolute',
            bottom: 'var(--space-8)',
            left: '50%',
            transform: 'translateX(-50%)',
            color: 'oklch(1 0 0 / 0.5)',
            fontSize: 'var(--text-xs)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          ↓ Learn more
        </div>
      </section>

      {/* ── Features ── */}
      <section
        style={{
          padding: 'var(--space-16) var(--space-6)',
          maxWidth: 1100,
          margin: '0 auto',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-12)' }}>
          <h2
            style={{
              fontSize: 'clamp(1.75rem, 4vw, 2.75rem)',
              fontWeight: 800,
              letterSpacing: '-0.025em',
              margin: '0 0 var(--space-3)',
            }}
          >
            Train smarter, not harder
          </h2>
          <p
            style={{
              fontSize: 'var(--text-md)',
              color: 'var(--muted-foreground)',
              maxWidth: 520,
              margin: '0 auto',
              lineHeight: 1.6,
            }}
          >
            A complete AI fitness stack — from planning to logging — in one interface.
          </p>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 'var(--space-6)',
          }}
        >
          {[
            {
              icon: '⚡',
              title: 'AI Workout Generation',
              desc: 'Describe your goals and available equipment. The AI builds a complete program in seconds, optimized for your schedule.',
            },
            {
              icon: '🎯',
              title: 'Expert Real-time Coaching',
              desc: 'Ask anything — form cues, progression strategies, programming questions. Your coach is always available.',
            },
            {
              icon: '📊',
              title: 'Effortless Progress Tracking',
              desc: 'Log every set with fuzzy exercise matching. Watch your strength trends build week over week.',
            },
          ].map((f) => (
            <div
              key={f.title}
              className="ww-card"
              style={{ padding: 'var(--space-6)' }}
            >
              <div style={{ fontSize: '2.25rem', marginBottom: 'var(--space-3)' }}>
                {f.icon}
              </div>
              <h3
                style={{
                  fontSize: 'var(--text-lg)',
                  fontWeight: 700,
                  margin: '0 0 var(--space-2)',
                }}
              >
                {f.title}
              </h3>
              <p
                style={{
                  color: 'var(--muted-foreground)',
                  margin: 0,
                  lineHeight: 1.6,
                  fontSize: 'var(--text-sm)',
                }}
              >
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer CTA ── */}
      <section
        style={{
          textAlign: 'center',
          padding: 'var(--space-16) var(--space-6)',
          background: 'var(--surface-sunken)',
          borderTop: '1px solid var(--border)',
        }}
      >
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 3.5vw, 2.25rem)',
            fontWeight: 700,
            margin: '0 0 var(--space-3)',
          }}
        >
          Ready to level up?
        </h2>
        <p
          style={{
            color: 'var(--muted-foreground)',
            margin: '0 0 var(--space-6)',
            fontSize: 'var(--text-md)',
          }}
        >
          Join athletes already training with AI-powered coaching.
        </p>
        <Link to="/register" style={{ textDecoration: 'none' }}>
          <button
            type="button"
            className="ww-btn ww-btn--gradient"
            style={{ fontSize: '1rem', height: '3rem', padding: '0 2.5rem' }}
          >
            Create Free Account
          </button>
        </Link>
      </section>
    </div>
  )
}
