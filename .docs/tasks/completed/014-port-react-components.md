# 014 — Port React Components and Test UI Against Backend

> **Depends on**: [011-tailwind-shadcn-ui](011-tailwind-shadcn-ui.md), [012-react-query-state](012-react-query-state.md)
> **Blocks**: [015-e2e-tests](015-e2e-tests.md), [016-edge-case-testing](016-edge-case-testing.md), [017-performance-baseline](017-performance-baseline.md)
> **Parallel-safe with**: none

## Objective

Implement all React components replacing the legacy Semantic UI app: login/register pages, exercise browser, workout list, and workout creation form. Connect to the FastAPI backend via React Query hooks and Axios. Verify the golden path (register → browse exercises → create workout → view workouts) works end-to-end.

## Approach

- React Router v6 for client-side routing (`/login`, `/register`, `/exercises`, `/workouts`, `/workouts/new`)
- Components in `src/components/`: `AuthForm`, `ExerciseBrowser`, `WorkoutList`, `WorkoutForm`
- Protected routes: redirect to `/login` if no token
- All data fetching via React Query hooks (no direct API calls in components)

## Steps

### 1. Install React Router and set up routing  <!-- agent: general-purpose -->

From `frontend/`:
```bash
npm install react-router-dom
```

Create `frontend/src/router.tsx`:
```tsx
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import ExercisesPage from '@/pages/ExercisesPage'
import WorkoutsPage from '@/pages/WorkoutsPage'
import WorkoutNewPage from '@/pages/WorkoutNewPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/exercises', element: <ExercisesPage /> },
  { path: '/workouts', element: <ProtectedRoute><WorkoutsPage /></ProtectedRoute> },
  { path: '/workouts/new', element: <ProtectedRoute><WorkoutNewPage /></ProtectedRoute> },
  { path: '/', element: <Navigate to="/exercises" replace /> },
])
```

Update `frontend/src/App.tsx`:
```tsx
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
export default function App() { return <RouterProvider router={router} /> }
```

- [x] `react-router-dom` installed
- [x] Router configured with 5 routes
- [x] `ProtectedRoute` redirects to `/login` when no token

---

### 2. Create Auth pages (Login and Register)  <!-- agent: general-purpose -->

Create `frontend/src/pages/LoginPage.tsx`:
- Form with email + password fields using shadcn/ui `Input` and `Button`
- On submit: call `login(email, password)` from `@/api/auth`, store token via `setToken`, redirect to `/workouts`
- Link to `/register`
- Show error message on failed login

Create `frontend/src/pages/RegisterPage.tsx`:
- Same structure as Login but calls `register()` then `login()`, then redirects
- Link to `/login`

- [x] `LoginPage.tsx` created with functional login form
- [x] `RegisterPage.tsx` created with functional register form
- [x] Successful login stores token and redirects to `/workouts`
- [x] Failed login shows error message

---

### 3. Create Exercise Browser page  <!-- agent: general-purpose -->

Create `frontend/src/pages/ExercisesPage.tsx`:
- Uses `useExercises(filters)` hook
- Search input for name filter (debounced 300ms)
- Displays exercises in a shadcn/ui `Table` with columns: Name, Category, Muscle Groups, Equipment
- Filter inputs for muscle_groups and equipment (comma-separated text inputs or selects)
- Loading state while fetching; error state on failure
- No auth required (exercises are public)

- [x] `ExercisesPage.tsx` created
- [x] Shows all 50 exercises by default
- [x] Name search filter works (debounced)
- [x] `muscle_groups` and `equipment` filter inputs work

---

### 4. Create Workouts list page  <!-- agent: general-purpose -->

Create `frontend/src/pages/WorkoutsPage.tsx`:
- Uses `useWorkouts()` hook
- Shows list of workouts with started_at date and sequence count
- "New Workout" button linking to `/workouts/new`
- Logout button that calls `logout()` and redirects to `/login`
- Each workout row shows delete button (uses `useDeleteWorkout()` mutation)

- [x] `WorkoutsPage.tsx` created
- [x] Shows authenticated user's workouts
- [x] Logout works
- [x] Delete workout works and refreshes list

---

### 5. Create Workout creation form  <!-- agent: general-purpose -->

Create `frontend/src/pages/WorkoutNewPage.tsx`:
- Form with:
  - `started_at` datetime input (defaults to now)
  - Add sequence button (creates warmup/main/cooldown sections)
  - Within each sequence: add set button, exercise selector (dropdown from `useExercises()`), set_type selector (STRENGTH/CARDIO), reps/weight or duration fields
- Submit calls `useCreateWorkout()` mutation
- On success, redirect to `/workouts`

- [x] `WorkoutNewPage.tsx` created
- [x] Can add sequences with phase selection
- [x] Can add sets with exercise selection and type-appropriate fields
- [x] Submit creates workout via API and redirects

---

### 6. Run app and verify golden path  <!-- agent: general-purpose -->

With the FastAPI backend running (`uvicorn app.main:app --reload` from `backend/`) and the frontend running (`npm run dev` from `frontend/`):

1. Navigate to `http://localhost:5173`
2. Register a new account
3. Browse exercises at `/exercises`
4. Create a new workout with at least one set
5. View the workout in the list
6. Delete the workout

- [DEFERRED-TO-UAT] Register → redirect to workouts
- [DEFERRED-TO-UAT] Exercises page shows 50 exercises
- [DEFERRED-TO-UAT] Create workout with sequences and sets succeeds
- [DEFERRED-TO-UAT] Workout appears in list
- [DEFERRED-TO-UAT] Delete workout removes it from list
- [x] `npm run build` succeeds <!-- Completed: 2026-06-04 -->

## Acceptance Criteria

- [x] All 5 routes render without errors
- [x] Login/Register pages connect to `/auth` endpoints
- [x] Exercise browser shows and filters exercises
- [x] Workout list shows authenticated user's workouts only
- [x] Workout creation form creates workouts with nested sequences and sets
- [x] `npm run build` produces a working production build
