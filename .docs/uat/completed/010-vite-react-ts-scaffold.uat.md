# UAT: Vite + React + TypeScript Frontend Scaffold

> **Source task**: [`.docs/tasks/010-vite-react-ts-scaffold.md`](../tasks/010-vite-react-ts-scaffold.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [x] Node.js 18+ is available (`node --version`)
- [x] `frontend/` directory exists in the project root
- [x] Dependencies installed: run `npm install` from `frontend/`

---

## Static File Tests

### UAT-STATIC-001: frontend/ contains required scaffold files

- **Description**: Verify that `package.json`, `vite.config.ts`, and `tsconfig.app.json` exist in `frontend/`
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const required = [
    'frontend/package.json',
    'frontend/vite.config.ts',
    'frontend/tsconfig.app.json',
  ];
  const missing = required.filter(f => !fs.existsSync(f));
  if (missing.length) { console.error('Missing:', missing); process.exit(1); }
  console.log('All required scaffold files present');
  "
  ```
- **Expected Result**: Prints `All required scaffold files present` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-002: frontend/src/App.tsx is a minimal placeholder

- **Description**: Verify `App.tsx` contains no Vite demo boilerplate — only the minimal `export default function App()` placeholder
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/App.tsx', 'utf8');
  const forbidden = ['useState', 'reactLogo', 'viteLogo', 'App.css', 'count', 'vite.svg'];
  const found = forbidden.filter(t => src.includes(t));
  if (found.length) { console.error('Boilerplate tokens still present:', found); process.exit(1); }
  if (!src.includes('export default function App')) { console.error('Missing expected App function export'); process.exit(1); }
  console.log('App.tsx is a minimal placeholder');
  "
  ```
- **Expected Result**: Prints `App.tsx is a minimal placeholder` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-003: frontend/.prettierrc has correct config

- **Description**: Verify `.prettierrc` exists and contains the required keys: `semi: false`, `singleQuote: true`, `trailingComma: "es5"`, `printWidth: 100`
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const rc = JSON.parse(fs.readFileSync('frontend/.prettierrc', 'utf8'));
  const checks = [
    [rc.semi === false,            'semi should be false'],
    [rc.singleQuote === true,      'singleQuote should be true'],
    [rc.trailingComma === 'es5',   'trailingComma should be es5'],
    [rc.printWidth === 100,        'printWidth should be 100'],
  ];
  const failed = checks.filter(([ok]) => !ok).map(([, msg]) => msg);
  if (failed.length) { console.error('Failures:', failed); process.exit(1); }
  console.log('.prettierrc config is correct');
  "
  ```
- **Expected Result**: Prints `.prettierrc config is correct` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-004: tsconfig.app.json has strict mode and @ path alias

- **Description**: Verify `tsconfig.app.json` has `"strict": true` and `"paths": { "@/*": ["src/*"] }`. Note: file uses JSONC (comments allowed), so comment-stripping is required before JSON.parse.
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const raw = fs.readFileSync('frontend/tsconfig.app.json', 'utf8')
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\/\/[^\n]*/g, '')
    .replace(/,(\s*[}\]])/g, '\$1');
  const cfg = JSON.parse(raw);
  const co = cfg.compilerOptions || {};
  if (co.strict !== true) { console.error('strict is not true:', co.strict); process.exit(1); }
  const paths = co.paths || {};
  const alias = paths['@/*'];
  if (!alias || !alias.includes('src/*')) { console.error('@/* path not found or wrong:', JSON.stringify(paths)); process.exit(1); }
  console.log('tsconfig.app.json strict mode and @ alias correct');
  "
  ```
- **Expected Result**: Prints `tsconfig.app.json strict mode and @ alias correct` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-005: vite.config.ts has @ alias and /api proxy

- **Description**: Verify `vite.config.ts` source contains the `@` alias pointing to `./src` and a `/api` proxy targeting `http://localhost:8000`
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/vite.config.ts', 'utf8');
  if (!src.includes('@')) { console.error('@ alias not found in vite.config.ts'); process.exit(1); }
  if (!src.includes('./src')) { console.error('./src alias target not found in vite.config.ts'); process.exit(1); }
  if (!src.includes('/api')) { console.error('/api proxy not found in vite.config.ts'); process.exit(1); }
  if (!src.includes('http://localhost:8000')) { console.error('proxy target http://localhost:8000 not found'); process.exit(1); }
  console.log('vite.config.ts @ alias and /api proxy present');
  "
  ```
- **Expected Result**: Prints `vite.config.ts @ alias and /api proxy present` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

## Build Tests

### UAT-BUILD-001: npm run build produces frontend/dist/ without errors

- **Description**: Run the production build from the `frontend/` directory and verify `dist/` is created
- **Command**:
  ```bash
  cd frontend && npm run build
  ```
- **Expected Result**: Exits 0; `frontend/dist/index.html` exists afterwards
- [x] Pass <!-- 2026-06-04 -->

### UAT-BUILD-002: frontend/dist/index.html exists after build

- **Description**: Confirm the build artifact is in place (run after UAT-BUILD-001)
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

- **Description**: Run ESLint over `frontend/src/` and confirm exit code 0
- **Command**:
  ```bash
  cd frontend && npm run lint
  ```
- **Expected Result**: Exits 0 with no error output
- [x] Pass <!-- 2026-06-04 -->
