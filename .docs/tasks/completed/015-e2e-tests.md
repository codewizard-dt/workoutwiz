# 015 — End-to-End Tests (User Auth Flow, Workout Creation, Exercise Search)

> **Depends on**: [014-port-react-components](014-port-react-components.md)
> **Blocks**: none
> **Parallel-safe with**: [016-edge-case-testing](016-edge-case-testing.md), [017-performance-baseline](017-performance-baseline.md), [018-production-readme](018-production-readme.md)

## Objective

Write Playwright E2E tests that exercise the three core user flows against a running stack (FastAPI + PostgreSQL + Vite frontend): user registration/login, exercise search, and workout creation.

## Approach

- Playwright with TypeScript (`@playwright/test`)
- Tests run against `http://localhost:5173` with backend on `http://localhost:8000`
- Use a fresh test user per test (unique email via timestamp)
- Page Object Model for the three pages (LoginPage, ExercisesPage, WorkoutsPage)
- CI-friendly: `playwright.config.ts` with `webServer` to auto-start both servers

## Steps

### 1. Install Playwright  <!-- agent: general-purpose -->

From `frontend/`:
```bash
npm install -D @playwright/test
npx playwright install chromium
```

Create `frontend/playwright.config.ts`:
```ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'cd ../backend && .venv/bin/uvicorn app.main:app --port 8000',
      port: 8000,
      reuseExistingServer: true,
    },
    {
      command: 'npm run dev',
      port: 5173,
      reuseExistingServer: true,
    },
  ],
})
```

- [x] `@playwright/test` installed <!-- Completed: 2026-06-04 -->
- [x] `frontend/playwright.config.ts` created <!-- Completed: 2026-06-04 -->
- [x] `frontend/e2e/` directory created <!-- Completed: 2026-06-04 -->

---

### 2. Write auth flow E2E test  <!-- agent: general-purpose -->

Create `frontend/e2e/auth.spec.ts`:

Tests:
- Register with a new email → redirected to `/workouts`
- Login with valid credentials → redirected to `/workouts`
- Login with invalid password → error message shown
- Logout → redirected to `/login`
- Accessing `/workouts` without auth → redirected to `/login`

- [x] `frontend/e2e/auth.spec.ts` created with 5 auth tests <!-- Completed: 2026-06-04 -->

---

### 3. Write exercise search E2E test  <!-- agent: general-purpose -->

Create `frontend/e2e/exercises.spec.ts`:

Tests:
- Navigate to `/exercises` → 50 exercises visible (no auth)
- Search by name "squat" → results filtered
- Filter by muscle group "chest" → results filtered
- Clear filters → all 50 results visible again

- [x] `frontend/e2e/exercises.spec.ts` created with 4 exercise tests <!-- Completed: 2026-06-04 -->

---

### 4. Write workout creation E2E test  <!-- agent: general-purpose -->

Create `frontend/e2e/workouts.spec.ts`:

Tests:
- Register + login → create a workout with one sequence and one set → workout appears in list
- Delete the workout → it disappears from list

- [x] `frontend/e2e/workouts.spec.ts` created with 2 workout tests <!-- Completed: 2026-06-04 -->

---

### 5. Run E2E tests  <!-- agent: general-purpose -->

From `frontend/` with backend and DB already running:
```bash
npx playwright test
```

All 11 tests must pass. Fix any failures.

- [x] `npx playwright test` exits with code 0 <!-- Completed: 2026-06-04 -->
- [x] All 11 tests pass (5 auth + 4 exercises + 2 workouts) <!-- Completed: 2026-06-04 -->

## Acceptance Criteria

- [x] Playwright installed with chromium browser <!-- Completed: 2026-06-04 -->
- [x] `playwright.config.ts` configures `webServer` for both backend and frontend <!-- Completed: 2026-06-04 -->
- [x] Auth flow tests: register, login, invalid login, logout, unauth redirect <!-- Completed: 2026-06-04 -->
- [x] Exercise search tests: list all, name filter, muscle filter, clear <!-- Completed: 2026-06-04 -->
- [x] Workout tests: create + view, delete <!-- Completed: 2026-06-04 -->
- [x] All tests pass with `npx playwright test` <!-- Completed: 2026-06-04 -->

---
**UAT**: [`.docs/uat/completed/015-e2e-tests.uat.md`](../uat/completed/015-e2e-tests.uat.md)
