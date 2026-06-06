# UAT: Port React Components and Test UI Against Backend

> **Source task**: [`.docs/tasks/014-port-react-components.md`](../tasks/014-port-react-components.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Node.js 18+ is available (`node --version`)
- [ ] `frontend/` directory exists in the project root
- [ ] Dependencies installed: run `npm install` from `frontend/`
- [ ] Working directory for all `node -e` scripts: project root (i.e. `workout-wiz/`)

---

## Static File Tests

### UAT-STATIC-001: router.tsx exists with 5 routes

- **Description**: Verify `frontend/src/router.tsx` exists and defines routes for `/login`, `/register`, `/exercises`, `/workouts`, and `/workouts/new`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/router.tsx', 'utf8');
  const routes = ['/login', '/register', '/exercises', '/workouts', '/workouts/new'];
  const missing = routes.filter(r => !src.includes(r));
  if (missing.length) { console.error('Missing routes:', missing); process.exit(1); }
  console.log('All 5 routes present in router.tsx');
  "
  ```
- **Expected Result**: Prints `All 5 routes present in router.tsx` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-002: ProtectedRoute guards /workouts and /workouts/new

- **Description**: Verify `router.tsx` wraps `/workouts` and `/workouts/new` with `ProtectedRoute` and redirects to `/login` when no token.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/router.tsx', 'utf8');
  if (!src.includes('ProtectedRoute')) { console.error('ProtectedRoute not defined'); process.exit(1); }
  if (!src.includes('Navigate') || !src.includes('/login')) { console.error('Missing Navigate to /login in ProtectedRoute'); process.exit(1); }
  const workoutsWrapped = src.match(/ProtectedRoute[\s\S]*?WorkoutsPage/);
  const newWrapped = src.match(/ProtectedRoute[\s\S]*?WorkoutNewPage/);
  if (!workoutsWrapped) { console.error('WorkoutsPage not inside ProtectedRoute'); process.exit(1); }
  if (!newWrapped) { console.error('WorkoutNewPage not inside ProtectedRoute'); process.exit(1); }
  console.log('ProtectedRoute correctly guards workout routes');
  "
  ```
- **Expected Result**: Prints `ProtectedRoute correctly guards workout routes` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-003: All page files exist

- **Description**: Verify all 5 page components exist in `frontend/src/pages/`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const pages = [
    'frontend/src/pages/LoginPage.tsx',
    'frontend/src/pages/RegisterPage.tsx',
    'frontend/src/pages/ExercisesPage.tsx',
    'frontend/src/pages/WorkoutsPage.tsx',
    'frontend/src/pages/WorkoutNewPage.tsx',
  ];
  const missing = pages.filter(p => !fs.existsSync(p));
  if (missing.length) { console.error('Missing pages:', missing); process.exit(1); }
  console.log('All 5 page files present');
  "
  ```
- **Expected Result**: Prints `All 5 page files present` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-004: React Query hook files exist

- **Description**: Verify hook files for exercises, workouts, and auth mutations exist in `frontend/src/hooks/`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const hooks = [
    'frontend/src/hooks/useExercises.ts',
    'frontend/src/hooks/useWorkouts.ts',
    'frontend/src/hooks/useAuthMutations.ts',
    'frontend/src/hooks/index.ts',
  ];
  const missing = hooks.filter(h => !fs.existsSync(h));
  if (missing.length) { console.error('Missing hook files:', missing); process.exit(1); }
  console.log('All hook files present');
  "
  ```
- **Expected Result**: Prints `All hook files present` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-005: AuthContext exists with token, setToken, and logout

- **Description**: Verify `frontend/src/context/AuthContext.tsx` exports a context with `token`, `setToken`, and `logout`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/context/AuthContext.tsx', 'utf8');
  const required = ['token', 'setToken', 'logout'];
  const missing = required.filter(t => !src.includes(t));
  if (missing.length) { console.error('Missing from AuthContext:', missing); process.exit(1); }
  console.log('AuthContext has token, setToken, and logout');
  "
  ```
- **Expected Result**: Prints `AuthContext has token, setToken, and logout` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-006: LoginPage uses useLogin hook and navigates to /workouts on success

- **Description**: Verify `LoginPage.tsx` uses `useLogin` from hooks and navigates to `/workouts` on successful login.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/pages/LoginPage.tsx', 'utf8');
  if (!src.includes('useLogin')) { console.error('Missing useLogin import/call'); process.exit(1); }
  if (!src.includes('/workouts')) { console.error('Missing /workouts redirect on success'); process.exit(1); }
  if (!src.includes('/register')) { console.error('Missing link to /register'); process.exit(1); }
  if (!src.includes('isError') || !src.includes('error')) { console.error('Missing error display logic'); process.exit(1); }
  console.log('LoginPage uses useLogin and navigates to /workouts');
  "
  ```
- **Expected Result**: Prints `LoginPage uses useLogin and navigates to /workouts` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-007: RegisterPage uses useRegister and useLogin hooks

- **Description**: Verify `RegisterPage.tsx` uses `useRegister` (and/or `useLogin`) for registration flow and links to `/login`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/pages/RegisterPage.tsx', 'utf8');
  if (!src.includes('useRegister')) { console.error('Missing useRegister'); process.exit(1); }
  if (!src.includes('/login')) { console.error('Missing link to /login'); process.exit(1); }
  console.log('RegisterPage uses useRegister and links to /login');
  "
  ```
- **Expected Result**: Prints `RegisterPage uses useRegister and links to /login` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-008: ExercisesPage uses useExercises with debouncing

- **Description**: Verify `ExercisesPage.tsx` uses the `useExercises` hook and implements debounced name/muscle/equipment filters.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/pages/ExercisesPage.tsx', 'utf8');
  if (!src.includes('useExercises')) { console.error('Missing useExercises'); process.exit(1); }
  if (!src.includes('debounce') && !src.includes('Debounce')) { console.error('Missing debounce logic'); process.exit(1); }
  if (!src.includes('muscle')) { console.error('Missing muscle_groups filter'); process.exit(1); }
  if (!src.includes('equipment')) { console.error('Missing equipment filter'); process.exit(1); }
  console.log('ExercisesPage uses useExercises with debouncing and filters');
  "
  ```
- **Expected Result**: Prints `ExercisesPage uses useExercises with debouncing and filters` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-009: WorkoutsPage uses useWorkouts and useDeleteWorkout, has logout

- **Description**: Verify `WorkoutsPage.tsx` uses `useWorkouts`, `useDeleteWorkout`, and calls `logout()` from AuthContext.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/pages/WorkoutsPage.tsx', 'utf8');
  if (!src.includes('useWorkouts')) { console.error('Missing useWorkouts'); process.exit(1); }
  if (!src.includes('useDeleteWorkout')) { console.error('Missing useDeleteWorkout'); process.exit(1); }
  if (!src.includes('logout')) { console.error('Missing logout call'); process.exit(1); }
  if (!src.includes('/workouts/new')) { console.error('Missing New Workout link'); process.exit(1); }
  console.log('WorkoutsPage has useWorkouts, useDeleteWorkout, and logout');
  "
  ```
- **Expected Result**: Prints `WorkoutsPage has useWorkouts, useDeleteWorkout, and logout` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-010: WorkoutNewPage uses useCreateWorkout and renders phase/set-type selectors

- **Description**: Verify `WorkoutNewPage.tsx` uses `useCreateWorkout` and renders warmup/main/cooldown phases and STRENGTH/CARDIO set types.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/pages/WorkoutNewPage.tsx', 'utf8');
  if (!src.includes('useCreateWorkout')) { console.error('Missing useCreateWorkout'); process.exit(1); }
  if (!src.includes('warmup') || !src.includes('main') || !src.includes('cooldown')) {
    console.error('Missing phase values (warmup/main/cooldown)'); process.exit(1);
  }
  if (!src.includes('STRENGTH') || !src.includes('CARDIO')) {
    console.error('Missing set type values (STRENGTH/CARDIO)'); process.exit(1);
  }
  if (!src.includes('useExercises')) { console.error('Missing useExercises for exercise selector'); process.exit(1); }
  console.log('WorkoutNewPage has useCreateWorkout, phases, and set types');
  "
  ```
- **Expected Result**: Prints `WorkoutNewPage has useCreateWorkout, phases, and set types` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-011: useExercises hook uses @tanstack/react-query and hits /api/exercises/

- **Description**: Verify `useExercises.ts` uses `useQuery` from `@tanstack/react-query` and targets the `/api/exercises/` endpoint.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/hooks/useExercises.ts', 'utf8');
  if (!src.includes('@tanstack/react-query')) { console.error('Missing @tanstack/react-query import'); process.exit(1); }
  if (!src.includes('useQuery')) { console.error('Missing useQuery'); process.exit(1); }
  if (!src.includes('/api/exercises/')) { console.error('Missing /api/exercises/ endpoint'); process.exit(1); }
  console.log('useExercises uses React Query and /api/exercises/');
  "
  ```
- **Expected Result**: Prints `useExercises uses React Query and /api/exercises/` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-012: useWorkouts hook uses Bearer token auth header

- **Description**: Verify `useWorkouts.ts` includes Bearer token authorization headers for authenticated requests.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/hooks/useWorkouts.ts', 'utf8');
  if (!src.includes('Bearer')) { console.error('Missing Bearer token in auth headers'); process.exit(1); }
  if (!src.includes('useCreateWorkout')) { console.error('Missing useCreateWorkout export'); process.exit(1); }
  if (!src.includes('useDeleteWorkout')) { console.error('Missing useDeleteWorkout export'); process.exit(1); }
  if (!src.includes('invalidateQueries')) { console.error('Missing cache invalidation after mutations'); process.exit(1); }
  console.log('useWorkouts uses Bearer auth and exports create/delete mutations with cache invalidation');
  "
  ```
- **Expected Result**: Prints `useWorkouts uses Bearer auth and exports create/delete mutations with cache invalidation` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-013: useAuthMutations hook targets /api/auth/jwt/login and /api/auth/register

- **Description**: Verify `useAuthMutations.ts` calls the correct FastAPI auth endpoints.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/hooks/useAuthMutations.ts', 'utf8');
  if (!src.includes('/api/auth/jwt/login')) { console.error('Missing /api/auth/jwt/login endpoint'); process.exit(1); }
  if (!src.includes('/api/auth/register')) { console.error('Missing /api/auth/register endpoint'); process.exit(1); }
  if (!src.includes('setToken')) { console.error('Missing setToken call after login'); process.exit(1); }
  console.log('useAuthMutations targets correct auth endpoints and calls setToken');
  "
  ```
- **Expected Result**: Prints `useAuthMutations targets correct auth endpoints and calls setToken` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-014: react-router-dom is listed as a dependency

- **Description**: Verify `react-router-dom` appears in `frontend/package.json` dependencies.
- **Command**:
  ```bash
  node -e "
  const pkg = JSON.parse(require('fs').readFileSync('frontend/package.json', 'utf8'));
  const deps = { ...pkg.dependencies, ...pkg.devDependencies };
  if (!deps['react-router-dom']) { console.error('react-router-dom not in package.json'); process.exit(1); }
  console.log('react-router-dom present in package.json:', deps['react-router-dom']);
  "
  ```
- **Expected Result**: Prints `react-router-dom present in package.json: <version>` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

## Build Tests

### UAT-BUILD-001: npm run build succeeds

- **Description**: Run the production build and verify it exits 0.
- **Command**:
  ```bash
  cd frontend && npm run build
  ```
- **Expected Result**: Exits 0; no TypeScript or Vite build errors
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-BUILD-002: dist/index.html exists after build

- **Description**: Confirm the build artifact is in place after UAT-BUILD-001.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  if (!fs.existsSync('frontend/dist/index.html')) { console.error('dist/index.html not found'); process.exit(1); }
  console.log('dist/index.html exists');
  "
  ```
- **Expected Result**: Prints `dist/index.html exists` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

## Lint Tests

### UAT-LINT-001: npm run lint passes without errors

- **Description**: Run ESLint over `frontend/src/` and confirm exit code 0.
- **Command**:
  ```bash
  cd frontend && npm run lint
  ```
- **Expected Result**: Exits 0 with no error output
- [x] Pass <!-- 2026-06-04 -->

---

## Golden Path Tests (Deferred — requires running backend + frontend)

The following tests were deferred from the task to UAT. They require:
- PostgreSQL running with migrations applied and seed data loaded
- FastAPI backend: `uvicorn app.main:app --reload` from `backend/`
- Frontend dev server: `npm run dev` from `frontend/`
- Browser at `http://localhost:5173`

### UAT-GOLDEN-001: Register redirects to /workouts

- **Description**: Navigate to `/register`, complete the form with a new email/password, submit, and verify redirect to `/workouts`.
- **Steps**:
  1. Open `http://localhost:5173/register`
  2. Enter a unique email and a valid password (8+ chars)
  3. Submit the form
- **Expected Result**: Page redirects to `/workouts` showing "My Workouts" heading with no errors

---

### UAT-GOLDEN-002: Exercises page shows all 50 exercises by default

- **Description**: Navigate to `/exercises` (no auth required) and verify 50 exercise rows are shown.
- **Steps**:
  1. Open `http://localhost:5173/exercises`
  2. Wait for the table to load
- **Expected Result**: Table renders 50 rows (one per exercise from the seed data)

---

### UAT-GOLDEN-003: Name search filter reduces exercise list

- **Description**: Type a partial name into the Name filter and verify the exercise list is filtered.
- **Steps**:
  1. On the `/exercises` page, type `bench` into the Name filter
  2. Wait 300 ms for debounce
- **Expected Result**: Table shows only exercises whose name contains "bench" (case-insensitive); other rows disappear

---

### UAT-GOLDEN-004: Create workout with sequences and sets succeeds

- **Description**: Authenticated user creates a workout with at least one sequence and one set.
- **Steps**:
  1. Log in and navigate to `/workouts/new`
  2. Click "+ Add Sequence", select phase "main"
  3. Click "+ Add Set", select an exercise, set type STRENGTH, enter reps and weight
  4. Click "Save Workout"
- **Expected Result**: Page redirects to `/workouts`; the new workout appears in the list with sequence count 1

---

### UAT-GOLDEN-005: Workout appears in list after creation

- **Description**: After UAT-GOLDEN-004, the created workout is visible in the `/workouts` list.
- **Steps**:
  1. On `/workouts`, observe the table
- **Expected Result**: At least one row is present showing the started_at date and sequence/set counts

---

### UAT-GOLDEN-006: Delete workout removes it from list

- **Description**: Click the Delete button on a workout row and verify it is removed from the list.
- **Steps**:
  1. On `/workouts`, click "Delete" on any workout row
- **Expected Result**: The row disappears from the table; the list refreshes automatically (React Query cache invalidated)

---

### UAT-GOLDEN-007: Unauthenticated access to /workouts redirects to /login

- **Description**: Verify ProtectedRoute works in a live browser session.
- **Steps**:
  1. Clear localStorage (or open incognito)
  2. Navigate directly to `http://localhost:5173/workouts`
- **Expected Result**: Browser immediately redirects to `/login`; the workout list is never shown
