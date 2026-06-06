import { useMutation, useQuery } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'
import type { User } from '@/types'

export function useLogin() {
  const { setToken } = useAuth()
  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const form = new FormData()
      form.append('username', email)
      form.append('password', password)
      const res = await fetch('/api/auth/jwt/login', { method: 'POST', body: form })
      if (!res.ok) throw new Error('Invalid credentials')
      const { access_token } = await res.json()
      return access_token as string
    },
    onSuccess: (token) => setToken(token),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) throw new Error('Registration failed')
      return res.json() as Promise<User>
    },
  })
}

export function useMe() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token!}` },
      })
      if (!res.ok) throw new Error('Failed to fetch user')
      return res.json() as Promise<User>
    },
    enabled: !!token,
  })
}