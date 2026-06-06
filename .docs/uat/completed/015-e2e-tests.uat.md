# UAT: End-to-End Tests (User Auth Flow, Workout Creation, Exercise Search)

> **Source task**: [`.docs/tasks/015-e2e-tests.md`](../tasks/015-e2e-tests.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] PostgreSQL running on localhost:5432; database `workoutwiz` exists with migrations applied
- [ ] Backend Python virtualenv exists at `backend/.venv` with all dependencies installed
- [ ] Frontend dependencies installed (`frontend/node_modules` exists — `npm install` run from `frontend/`)
- [ ] Playwright chromium browser installed (`npx playwright install chromium` from `frontend/`)
- [ ] Both servers are either already running (ports 8000 and 5173) or will be auto-started by `playwright.config.ts` `webServer` config
- [ ] Working directory for test commands: `frontend/`

---

## File Existence Tests

### UAT-FILE-001: `playwright.config.ts` exists with correct `testDir`, `webServer`, and `baseURL`

**Steps**:
1. Verify the config file exists and contains the required settings
2. Run the command below from `frontend/`

**Command**:
```bash
node -e "
const fs = require('fs');
const src = fs.readFileSync('playwright.config.ts', 'utf8');
console.assert(src.includes(\"testDir: './e2e'\"), 'testDir missing');
console.assert(src.includes('webServer'), 'webServer missing');
console.assert(src.includes('http://localhost:5173'), 'baseURL missing');
console.assert(src.includes('port: 8000'), 'backend port missing');
console.assert(src.includes('port: 5173'), 'frontend port missing');
console.assert(src.includes('chromium'), 'chromium project missing');
console.log('PASS: playwright.config.ts contains all required settings');
" 2>&1
```

**Expected**: `PASS: playwright.config.ts contains all required settings`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-002: `e2e/auth.spec.ts` exists with all 5 auth tests

**Steps**:
1. Verify `frontend/e2e/auth.spec.ts` exists and contains the 5 required test names
2. Run the command below from `frontend/`

**Command**:
```bash
node -e "
const fs = require('fs');
const src = fs.readFileSync('e2e/auth.spec.ts', 'utf8');
const required = [
  'register with new email',
  'login with valid credentials',
  'login with invalid password',
  'logout',
  'accessing /workouts without auth',
];
required.forEach(t => {
  console.assert(src.includes(t), \`Missing test: \${t}\`);
  console.log(\`PASS: found '\${t}'\`);
});
" 2>&1
```

**Expected**: 5 `PASS` lines, one per test name

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-003: `e2e/exercises.spec.ts` exists with all 4 exercise tests

**Steps**:
1. Verify `frontend/e2e/exercises.spec.ts` exists and contains the 4 required test names
2. Run the command below from `frontend/`

**Command**:
```bash
node -e "
const fs = require('fs');
const src = fs.readFileSync('e2e/exercises.spec.ts', 'utf8');
const required = [
  'navigate to /exercises',
  'search by name',
  'filter by muscle group',
  'clear filters',
];
required.forEach(t => {
  console.assert(src.includes(t), \`Missing test: \${t}\`);
  console.log(\`PASS: found '\${t}'\`);
});
" 2>&1
```

**Expected**: 4 `PASS` lines, one per test name

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-004: `e2e/workouts.spec.ts` exists with 2 workout tests

**Steps**:
1. Verify `frontend/e2e/workouts.spec.ts` exists and contains the 2 required test names
2. Run the command below from `frontend/`

**Command**:
```bash
node -e "
const fs = require('fs');
const src = fs.readFileSync('e2e/workouts.spec.ts', 'utf8');
const required = [
  'create a workout',
  'delete workout',
];
required.forEach(t => {
  console.assert(src.includes(t), \`Missing test: \${t}\`);
  console.log(\`PASS: found '\${t}'\`);
});
" 2>&1
```

**Expected**: 2 `PASS` lines, one per test name

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-FILE-005: Playwright and Chromium are installed

**Steps**:
1. Verify `@playwright/test` is resolvable and chromium browser directory exists
2. Run the command below from `frontend/`

**Command**:
```bash
node -e "
require('@playwright/test');
console.log('PASS: @playwright/test package is installed');
" && npx playwright install --list 2>&1 | grep -q 'chromium' && echo 'PASS: chromium browser is installed'
```

**Expected**:
- `PASS: @playwright/test package is installed`
- `PASS: chromium browser is installed`

- [x] Pass <!-- 2026-06-04 -->

---

## Full E2E Test Suite

### UAT-SUITE-001: `npx playwright test` exits code 0 with all 11 tests passing

This is the primary acceptance test. It exercises the full stack — FastAPI backend, PostgreSQL, and the Vite frontend — using Playwright's Chromium browser. The `webServer` config auto-starts both servers if they are not already running.

**Steps**:
1. Ensure PostgreSQL is running with the `workoutwiz` database and migrations applied
2. Run from `frontend/`:

**Command**:
```bash
npx playwright test --reporter=list 2>&1
```

**Expected**:
- Exit code 0
- Output shows `11 passed`
- All of the following test names appear and show `passed`:
  - `auth.spec.ts > register with new email → redirected to /workouts`
  - `auth.spec.ts > login with valid credentials → redirected to /workouts`
  - `auth.spec.ts > login with invalid password → error message shown`
  - `auth.spec.ts > logout → redirected to /login`
  - `auth.spec.ts > accessing /workouts without auth → redirected to /login`
  - `exercises.spec.ts > navigate to /exercises → 50 exercises visible (no auth)`
  - `exercises.spec.ts > search by name "squat" → results filtered`
  - `exercises.spec.ts > filter by muscle group "chest" → results filtered`
  - `exercises.spec.ts > clear filters → all 50 results visible again`
  - `workouts.spec.ts > create a workout with one sequence and one set → workout appears in list`
  - `workouts.spec.ts > delete workout → it disappears from list`

- [x] Pass <!-- 2026-06-04 -->

---

## Individual Flow Tests (selective re-runs)

### UAT-E2E-001: Auth spec alone passes (5 tests)

**Steps**:
1. Run from `frontend/`:

**Command**:
```bash
npx playwright test e2e/auth.spec.ts --reporter=list 2>&1
```

**Expected**: Exit code 0, `5 passed`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-E2E-002: Exercise search spec alone passes (4 tests)

**Steps**:
1. Run from `frontend/`:

**Command**:
```bash
npx playwright test e2e/exercises.spec.ts --reporter=list 2>&1
```

**Expected**: Exit code 0, `4 passed`

- [x] Pass <!-- 2026-06-04 -->

---

### UAT-E2E-003: Workouts spec alone passes (2 tests)

**Steps**:
1. Run from `frontend/`:

**Command**:
```bash
npx playwright test e2e/workouts.spec.ts --reporter=list 2>&1
```

**Expected**: Exit code 0, `2 passed`

- [x] Pass <!-- 2026-06-04 -->

---

## Coverage Summary

| Area | Test IDs | Count | Criteria |
|------|----------|-------|----------|
| File existence | UAT-FILE-001 to 005 | 5 | Config, spec files, and playwright/chromium installed |
| Full suite | UAT-SUITE-001 | 1 | All 11 E2E tests pass together |
| Auth flow | UAT-E2E-001 | 1 | 5 auth tests pass in isolation |
| Exercise search | UAT-E2E-002 | 1 | 4 exercise tests pass in isolation |
| Workout creation | UAT-E2E-003 | 1 | 2 workout tests pass in isolation |
| **Total** | | **9** | All must pass |
