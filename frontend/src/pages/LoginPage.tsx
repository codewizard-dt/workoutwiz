import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useLogin } from '@/hooks/useAuthMutations'


export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const login = useLogin()

  const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    login.mutate(
      { email, password },
      { onSuccess: () => { navigate('/workouts'); } }
    )
  }

  return (
    <div
      style={{
        minHeight: '100dvh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--background)',
        padding: 'var(--space-4)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative background */}
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        <div style={{
          position: 'absolute', top: '-180px', right: '-120px',
          width: '560px', height: '560px', borderRadius: '50%',
          background: 'radial-gradient(circle, oklch(0.645 0.190 38 / 0.15) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', bottom: '-80px', left: '-80px',
          width: '380px', height: '380px', borderRadius: '50%',
          background: 'radial-gradient(circle, oklch(0.785 0.160 72 / 0.10) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', top: '40%', left: '-60px',
          width: '200px', height: '200px', borderRadius: '50%',
          background: 'radial-gradient(circle, oklch(0.645 0.190 38 / 0.08) 0%, transparent 70%)',
        }} />
      </div>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-6)' }}>
          <img
            src="/src/assets/logo/workout-wiz-logo-smile.png"
            alt="Workout Wiz"
            style={{ height: '3.5rem', width: 'auto' }}
          />
        </div>

        <div className="ww-card" style={{ padding: 'var(--space-6)' }}>
          <h1
            style={{
              margin: '0 0 var(--space-1)',
              fontSize: 'var(--text-xl)',
              fontWeight: 'var(--weight-semibold)',
            }}
          >
            Sign in
          </h1>
          <p
            style={{
              margin: '0 0 var(--space-5)',
              fontSize: 'var(--text-sm)',
              color: 'var(--muted-foreground)',
            }}
          >
            Your AI strength coach is ready.
          </p>

          {login.isError && (
            <div
              style={{
                marginBottom: 'var(--space-4)',
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-md)',
                background: 'oklch(0.97 0.02 25)',
                color: 'var(--destructive)',
                fontSize: 'var(--text-sm)',
              }}
            >
              {login.error instanceof Error ? login.error.message : 'Login failed'}
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
              <label
                htmlFor="email"
                style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                className="ww-input"
                value={email}
                onChange={(e) => { setEmail(e.target.value) }}
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
              <label
                htmlFor="password"
                style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                className="ww-input"
                value={password}
                onChange={(e) => { setPassword(e.target.value) }}
                required
                autoComplete="current-password"
              />
            </div>
            <button
              type="submit"
              className="ww-btn ww-btn--gradient"
              style={{ width: '100%', justifyContent: 'center' }}
              disabled={login.isPending}
            >
              {login.isPending ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p
            style={{
              marginTop: 'var(--space-5)',
              textAlign: 'center',
              fontSize: 'var(--text-sm)',
              color: 'var(--muted-foreground)',
            }}
          >
            Need an account?{' '}
            <Link
              to="/register"
              style={{ color: 'var(--accent)', textDecoration: 'underline', textUnderlineOffset: 4 }}
            >
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
