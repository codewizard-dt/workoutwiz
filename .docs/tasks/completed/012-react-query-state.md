# 012 — Set Up React Query (TanStack Query) State Management

> **Depends on**: [010-vite-react-ts-scaffold](010-vite-react-ts-scaffold.md)
> **Blocks**: [014-port-react-components](014-port-react-components.md)
> **Parallel-safe with**: [011-tailwind-shadcn-ui](011-tailwind-shadcn-ui.md)

## Objective

Install TanStack Query v5 and configure the `QueryClientProvider`. Define typed query hooks for exercises, workouts, and auth state. No Redux — all server state via React Query, auth/UI state via local `useState`.

## Approach

- `@tanstack/react-query` v5 for server state (exercises, workouts, user)
- `QueryClient` with sensible defaults: `staleTime: 5 * 60 * 1000`, `retry: 1`
- Custom hooks in `src/hooks/`: `useExercises`, `useWorkouts`, `useWorkout`, `useCreateWorkout`, `useUpdateWorkout`, `useDeleteWorkout`
- Auth state: a simple `useAuthStore` using `useState` + React Context (no Zustand needed — just token in localStorage + React context)
- React Query DevTools in development

## Steps

### 1. Install TanStack Query  <!-- agent: general-purpose -->

From `frontend/`:
```bash
npm install @tanstack/react-query
npm install -D @tanstack/react-query-devtools
```

- [x] `@tanstack/react-query` installed

---

### 2. Configure QueryClientProvider in main.tsx  <!-- agent: general-purpose -->

Update `frontend/src/main.tsx`:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import './index.css'
import App from './App'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>
)
```

- [x] `QueryClientProvider` wraps the app in `main.tsx`
- [x] `ReactQueryDevtools` included (dev only — Vite tree-shakes in production)

---

### 3. Create auth context  <!-- agent: general-purpose -->

Create `frontend/src/context/AuthContext.tsx`:
```tsx
import { createContext, useContext, useState, ReactNode } from 'react'

interface AuthContextValue {
  token: string | null
  setToken: (token: string | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(
    () => localStorage.getItem('auth_token')
  )

  const setToken = (t: string | null) => {
    setTokenState(t)
    if (t) localStorage.setItem('auth_token', t)
    else localStorage.removeItem('auth_token')
  }

  const logout = () => setToken(null)

  return <AuthContext.Provider value={{ token, setToken, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
```

Wrap `App` with `AuthProvider` in `main.tsx` (inside `QueryClientProvider`).

- [x] `frontend/src/context/AuthContext.tsx` created
- [x] `useAuth()` hook returns `{ token, setToken, logout }`
- [x] Token persisted in `localStorage`

---

### 4. Create React Query hooks  <!-- agent: general-purpose -->

Create `frontend/src/hooks/useExercises.ts`:
```ts
import { useQuery } from '@tanstack/react-query'
import { getExercises, ExerciseFilters } from '@/api/exercises'

export function useExercises(filters?: ExerciseFilters) {
  return useQuery({
    queryKey: ['exercises', filters],
    queryFn: () => getExercises(filters),
  })
}
```

Create `frontend/src/hooks/useWorkouts.ts`:
```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWorkouts, getWorkout, createWorkout, updateWorkout, deleteWorkout } from '@/api/workouts'
import { useAuth } from '@/context/AuthContext'

export function useWorkouts() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['workouts'],
    queryFn: () => getWorkouts(token!),
    enabled: !!token,
  })
}

export function useWorkout(id: string) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['workouts', id],
    queryFn: () => getWorkout(token!, id),
    enabled: !!token && !!id,
  })
}

export function useCreateWorkout() {
  const { token } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Parameters<typeof createWorkout>[1]) => createWorkout(token!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts'] }),
  })
}

export function useUpdateWorkout() {
  const { token } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updateWorkout>[2] }) =>
      updateWorkout(token!, id, data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['workouts'] })
      qc.invalidateQueries({ queryKey: ['workouts', id] })
    },
  })
}

export function useDeleteWorkout() {
  const { token } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteWorkout(token!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts'] }),
  })
}
```

Note: these hooks import from `@/api/exercises` and `@/api/workouts` — those are created in TASK-013.

- [x] `frontend/src/hooks/useExercises.ts` created
- [x] `frontend/src/hooks/useWorkouts.ts` created with 5 hooks
- [x] `frontend/src/hooks/` directory has `__index__.ts` or individual exports

## Acceptance Criteria

- [x] `@tanstack/react-query` v5 installed
- [x] `QueryClientProvider` wraps app in `main.tsx`
- [x] `AuthProvider` wraps app and persists token in localStorage
- [x] `useExercises`, `useWorkouts`, `useWorkout`, `useCreateWorkout`, `useUpdateWorkout`, `useDeleteWorkout` hooks defined
- [x] `npm run build` succeeds without TypeScript errors
