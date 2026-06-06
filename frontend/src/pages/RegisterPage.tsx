import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useRegister } from '@/hooks/useAuthMutations'
import { useLogin } from '@/hooks/useAuthMutations'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const register = useRegister()
  const login = useLogin()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    register.mutate(
      { email, password },
      {
        onSuccess: () => {
          login.mutate(
            { email, password },
            { onSuccess: () => navigate('/workouts') }
          )
        },
      }
    )
  }

  const isPending = register.isPending || login.isPending
  const error = register.error || login.error

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 p-8 border rounded-lg shadow-sm">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold">Create account</h1>
          <p className="text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" className="underline underline-offset-4">
              Sign in
            </Link>
          </p>
        </div>

        {error && (
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : 'Registration failed'}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? 'Creating account…' : 'Create account'}
          </Button>
        </form>
      </div>
    </div>
  )
}
