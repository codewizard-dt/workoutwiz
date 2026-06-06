# UAT: React Query (TanStack Query) State Management

> **Source task**: [`.docs/tasks/completed/012-react-query-state.md`](../tasks/completed/012-react-query-state.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Node.js 18+ is available (`node --version`)
- [ ] `frontend/` directory exists in the project root
- [ ] Dependencies installed: run `npm install` from `frontend/`

---

## Static File Tests

### UAT-STATIC-001: @tanstack/react-query v5 is listed as a dependency

- **Description**: Verify `frontend/package.json` lists `@tanstack/react-query` v5.x as a dependency and `@tanstack/react-query-devtools` as a devDependency.
- **Command**:
  ```bash
  node -e "
  const pkg = JSON.parse(require('fs').readFileSync('frontend/package.json', 'utf8'));
  const dep = pkg.dependencies?.['@tanstack/react-query'] || '';
  const dev = pkg.devDependencies?.['@tanstack/react-query-devtools'] || '';
  if (!dep.startsWith('^5') && !dep.startsWith('5')) {
    console.error('@tanstack/react-query v5 not found in dependencies:', dep);
    process.exit(1);
  }
  if (!dev) {
    console.error('@tanstack/react-query-devtools not found in devDependencies');
    process.exit(1);
  }
  console.log('react-query dep:', dep);
  console.log('react-query-devtools devDep:', dev);
  console.log('PASS');
  "
  ```
- **Expected Result**: Exits 0. Prints the version strings and `PASS`.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-002: frontend/src/context/AuthContext.tsx exists with expected exports

- **Description**: Verify `AuthContext.tsx` exists and exports `AuthProvider` and `useAuth`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const path = 'frontend/src/context/AuthContext.tsx';
  if (!fs.existsSync(path)) { console.error('AuthContext.tsx not found'); process.exit(1); }
  const src = fs.readFileSync(path, 'utf8');
  const checks = [
    [src.includes('export function AuthProvider'), 'AuthProvider export missing'],
    [src.includes('export function useAuth'), 'useAuth export missing'],
    [src.includes('localStorage'), 'localStorage usage missing'],
    [src.includes('token'), 'token state missing'],
    [src.includes('logout'), 'logout function missing'],
  ];
  const failed = checks.filter(([ok]) => !ok).map(([, msg]) => msg);
  if (failed.length) { console.error('Failures:', failed); process.exit(1); }
  console.log('AuthContext.tsx has all required exports');
  "
  ```
- **Expected Result**: Exits 0. Prints `AuthContext.tsx has all required exports`.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-003: frontend/src/hooks/useExercises.ts exists with useExercises hook

- **Description**: Verify `useExercises.ts` exists and exports a `useExercises` function that calls `useQuery`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const path = 'frontend/src/hooks/useExercises.ts';
  if (!fs.existsSync(path)) { console.error('useExercises.ts not found'); process.exit(1); }
  const src = fs.readFileSync(path, 'utf8');
  const checks = [
    [src.includes('export function useExercises'), 'useExercises export missing'],
    [src.includes('useQuery'), 'useQuery call missing'],
    [src.includes('exercises'), 'exercises query key missing'],
  ];
  const failed = checks.filter(([ok]) => !ok).map(([, msg]) => msg);
  if (failed.length) { console.error('Failures:', failed); process.exit(1); }
  console.log('useExercises.ts is correct');
  "
  ```
- **Expected Result**: Exits 0. Prints `useExercises.ts is correct`.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-004: frontend/src/hooks/useWorkouts.ts exports all five workout hooks

- **Description**: Verify `useWorkouts.ts` exists and exports all five required hooks: `useWorkouts`, `useWorkout`, `useCreateWorkout`, `useUpdateWorkout`, `useDeleteWorkout`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const path = 'frontend/src/hooks/useWorkouts.ts';
  if (!fs.existsSync(path)) { console.error('useWorkouts.ts not found'); process.exit(1); }
  const src = fs.readFileSync(path, 'utf8');
  const hooks = ['useWorkouts', 'useWorkout', 'useCreateWorkout', 'useUpdateWorkout', 'useDeleteWorkout'];
  const missing = hooks.filter(h => !src.includes('export function ' + h));
  if (missing.length) { console.error('Missing hook exports:', missing); process.exit(1); }
  const checks = [
    [src.includes('useQuery'), 'useQuery missing'],
    [src.includes('useMutation'), 'useMutation missing'],
    [src.includes('useQueryClient'), 'useQueryClient missing'],
    [src.includes('invalidateQueries'), 'invalidateQueries missing'],
    [src.includes('enabled: !!token'), 'enabled guard missing'],
  ];
  const failed = checks.filter(([ok]) => !ok).map(([, msg]) => msg);
  if (failed.length) { console.error('Failures:', failed); process.exit(1); }
  console.log('useWorkouts.ts exports all five hooks');
  "
  ```
- **Expected Result**: Exits 0. Prints `useWorkouts.ts exports all five hooks`.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-005: main.tsx wraps app with QueryClientProvider and AuthProvider

- **Description**: Verify `main.tsx` imports and uses `QueryClientProvider`, `AuthProvider`, and `ReactQueryDevtools`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const path = 'frontend/src/main.tsx';
  if (!fs.existsSync(path)) { console.error('main.tsx not found'); process.exit(1); }
  const src = fs.readFileSync(path, 'utf8');
  const checks = [
    [src.includes('QueryClientProvider'), 'QueryClientProvider missing'],
    [src.includes('QueryClient'), 'QueryClient instantiation missing'],
    [src.includes('AuthProvider'), 'AuthProvider missing'],
    [src.includes('ReactQueryDevtools'), 'ReactQueryDevtools missing'],
    [src.includes('staleTime'), 'staleTime default config missing'],
    [src.includes('retry'), 'retry default config missing'],
  ];
  const failed = checks.filter(([ok]) => !ok).map(([, msg]) => msg);
  if (failed.length) { console.error('Failures:', failed); process.exit(1); }
  console.log('main.tsx correctly wraps app with providers');
  "
  ```
- **Expected Result**: Exits 0. Prints `main.tsx correctly wraps app with providers`.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-006: QueryClient defaults use staleTime 5 min and retry 1

- **Description**: Verify `main.tsx` configures `staleTime: 5 * 60 * 1000` (or the literal `300000`) and `retry: 1`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/main.tsx', 'utf8');
  const hasStaleTime = src.includes('5 * 60 * 1000') || src.includes('300000');
  const hasRetry = src.includes('retry: 1');
  if (!hasStaleTime) { console.error('staleTime 5min not found'); process.exit(1); }
  if (!hasRetry) { console.error('retry: 1 not found'); process.exit(1); }
  console.log('QueryClient defaults are correct');
  "
  ```
- **Expected Result**: Exits 0. Prints `QueryClient defaults are correct`.
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-007: useAuth() throws when used outside AuthProvider

- **Description**: Verify `AuthContext.tsx` contains a guard that throws an error when `useAuth` is called outside `AuthProvider`.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/context/AuthContext.tsx', 'utf8');
  if (!src.includes('throw new Error')) {
    console.error('Missing throw guard in useAuth');
    process.exit(1);
  }
  console.log('useAuth throw guard present');
  "
  ```
- **Expected Result**: Exits 0. Prints `useAuth throw guard present`.
- [x] Pass <!-- 2026-06-04 -->

---

## Build Tests

### UAT-BUILD-001: npm run build succeeds without TypeScript errors

- **Description**: Run the production build from `frontend/` and verify it exits 0 with no TypeScript errors.
- **Command**:
  ```bash
  cd frontend && npm run build
  ```
- **Expected Result**: Exits 0. No `TS` error lines in output. `frontend/dist/index.html` exists afterwards.
- [x] Pass <!-- 2026-06-04 -->

---

## Lint Tests

### UAT-LINT-001: npm run lint passes without errors

- **Description**: Run ESLint over `frontend/src/` and confirm exit code 0.
- **Command**:
  ```bash
  cd frontend && npm run lint
  ```
- **Expected Result**: Exits 0 with no error output.
- [x] Pass <!-- 2026-06-04 -->
