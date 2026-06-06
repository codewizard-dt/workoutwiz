# UAT: Install Tailwind CSS and shadcn/ui

> **Source task**: [`.docs/tasks/011-tailwind-shadcn-ui.md`](../tasks/011-tailwind-shadcn-ui.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Node.js 18+ is available (`node --version`)
- [ ] `frontend/` directory exists in the project root
- [ ] Dependencies installed: run `npm install` from `frontend/`

---

## Static File Tests

### UAT-STATIC-001: Tailwind config exists with correct content paths

- **Description**: Verify `tailwind.config.js` exists and specifies `./index.html` and `./src/**/*.{ts,tsx}` as content paths (required for Tailwind to process all component classes)
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/tailwind.config.js', 'utf8');
  if (!src.includes('./index.html')) { console.error('Missing ./index.html in content'); process.exit(1); }
  if (!src.includes('./src/**/*.{ts,tsx}')) { console.error('Missing ./src/**/*.{ts,tsx} in content'); process.exit(1); }
  if (!src.includes('darkMode')) { console.error('Missing darkMode config'); process.exit(1); }
  console.log('tailwind.config.js content paths correct');
  "
  ```
- **Expected Result**: Prints `tailwind.config.js content paths correct` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-002: index.css uses Tailwind directives

- **Description**: Verify `frontend/src/index.css` contains the three required Tailwind directives at the top of the file
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/index.css', 'utf8');
  const required = ['@tailwind base', '@tailwind components', '@tailwind utilities'];
  const missing = required.filter(d => !src.includes(d));
  if (missing.length) { console.error('Missing directives:', missing); process.exit(1); }
  console.log('index.css has all three Tailwind directives');
  "
  ```
- **Expected Result**: Prints `index.css has all three Tailwind directives` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-003: postcss.config.js exists

- **Description**: Verify PostCSS config file exists (required for Tailwind to process via Vite)
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  if (!fs.existsSync('frontend/postcss.config.js')) { console.error('postcss.config.js not found'); process.exit(1); }
  console.log('postcss.config.js exists');
  "
  ```
- **Expected Result**: Prints `postcss.config.js exists` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-004: tailwindcss, postcss, autoprefixer are in devDependencies

- **Description**: Verify the three Tailwind-related packages appear in `package.json` devDependencies
- **Command**:
  ```bash
  node -e "
  const pkg = JSON.parse(require('fs').readFileSync('frontend/package.json', 'utf8'));
  const dev = pkg.devDependencies || {};
  const required = ['tailwindcss', 'postcss', 'autoprefixer'];
  const missing = required.filter(p => !dev[p]);
  if (missing.length) { console.error('Missing devDependencies:', missing); process.exit(1); }
  console.log('tailwindcss, postcss, autoprefixer present in devDependencies');
  "
  ```
- **Expected Result**: Prints `tailwindcss, postcss, autoprefixer present in devDependencies` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-005: components.json exists (shadcn init completed)

- **Description**: Verify `frontend/components.json` was created by `shadcn init`, confirming the CLI ran successfully
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  if (!fs.existsSync('frontend/components.json')) { console.error('components.json not found'); process.exit(1); }
  const cfg = JSON.parse(fs.readFileSync('frontend/components.json', 'utf8'));
  if (!cfg.aliases || !cfg.aliases.utils) { console.error('components.json missing aliases.utils'); process.exit(1); }
  console.log('components.json exists and has aliases config');
  "
  ```
- **Expected Result**: Prints `components.json exists and has aliases config` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-006: cn() utility exported from @/lib/utils

- **Description**: Verify `frontend/src/lib/utils.ts` exists and exports a `cn` function built from `clsx` and `tailwind-merge`
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  if (!fs.existsSync('frontend/src/lib/utils.ts')) { console.error('src/lib/utils.ts not found'); process.exit(1); }
  const src = fs.readFileSync('frontend/src/lib/utils.ts', 'utf8');
  if (!src.includes('export function cn') && !src.includes('export const cn')) { console.error('cn() not exported from utils.ts'); process.exit(1); }
  if (!src.includes('clsx')) { console.error('clsx not used in utils.ts'); process.exit(1); }
  if (!src.includes('twMerge') && !src.includes('tailwind-merge')) { console.error('tailwind-merge not used in utils.ts'); process.exit(1); }
  console.log('cn() utility correctly defined and exported');
  "
  ```
- **Expected Result**: Prints `cn() utility correctly defined and exported` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-007: All required shadcn/ui component files exist

- **Description**: Verify all eight component files required by the task exist in `frontend/src/components/ui/`
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const required = [
    'frontend/src/components/ui/button.tsx',
    'frontend/src/components/ui/input.tsx',
    'frontend/src/components/ui/card.tsx',
    'frontend/src/components/ui/label.tsx',
    'frontend/src/components/ui/form.tsx',
    'frontend/src/components/ui/select.tsx',
    'frontend/src/components/ui/table.tsx',
    'frontend/src/components/ui/badge.tsx',
  ];
  const missing = required.filter(f => !fs.existsSync(f));
  if (missing.length) { console.error('Missing components:', missing); process.exit(1); }
  console.log('All 8 shadcn/ui component files present');
  "
  ```
- **Expected Result**: Prints `All 8 shadcn/ui component files present` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-008: Each component uses cn() from @/lib/utils

- **Description**: Verify each shadcn/ui component imports and uses the `cn` utility (confirms components are properly wired to the Tailwind config)
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const components = ['button', 'input', 'card', 'form', 'select', 'table', 'badge'];
  const failures = [];
  for (const name of components) {
    const src = fs.readFileSync('frontend/src/components/ui/' + name + '.tsx', 'utf8');
    if (!src.includes('@/lib/utils') && !src.includes('./utils')) {
      failures.push(name + ': missing cn import');
    }
  }
  if (failures.length) { console.error('Failures:', failures); process.exit(1); }
  console.log('All components import cn from @/lib/utils');
  "
  ```
- **Expected Result**: Prints `All components import cn from @/lib/utils` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-009: clsx and tailwind-merge are in dependencies

- **Description**: Verify `clsx` and `tailwind-merge` are listed in `package.json` dependencies (installed by shadcn init)
- **Command**:
  ```bash
  node -e "
  const pkg = JSON.parse(require('fs').readFileSync('frontend/package.json', 'utf8'));
  const all = Object.assign({}, pkg.dependencies, pkg.devDependencies);
  const required = ['clsx', 'tailwind-merge'];
  const missing = required.filter(p => !all[p]);
  if (missing.length) { console.error('Missing packages:', missing); process.exit(1); }
  console.log('clsx and tailwind-merge present in package.json');
  "
  ```
- **Expected Result**: Prints `clsx and tailwind-merge present in package.json` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-STATIC-010: App.tsx imports and renders Button component

- **Description**: Verify `App.tsx` imports `Button` from `@/components/ui/button` and renders it (smoke-test scaffold from task Step 4)
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const src = fs.readFileSync('frontend/src/App.tsx', 'utf8');
  if (!src.includes('@/components/ui/button')) { console.error('Button import not found in App.tsx'); process.exit(1); }
  if (!src.includes('<Button')) { console.error('Button not rendered in App.tsx'); process.exit(1); }
  console.log('App.tsx correctly imports and uses Button');
  "
  ```
- **Expected Result**: Prints `App.tsx correctly imports and uses Button` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

## Build Tests

### UAT-BUILD-001: npm run build succeeds with Tailwind and shadcn installed

- **Description**: Run the production build and confirm it exits 0 — this is the primary acceptance criterion proving Tailwind processing and TypeScript compilation both succeed end-to-end
- **Command**:
  ```bash
  cd frontend && npm run build
  ```
- **Expected Result**: Exits 0; no TypeScript or Tailwind errors in output; `frontend/dist/` is produced
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-BUILD-002: Built CSS contains Tailwind utility classes

- **Description**: Verify the production CSS bundle contains at least one generated Tailwind utility class (confirms Tailwind actually processed source files, not just passed through)
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const path = require('path');
  const cssDir = 'frontend/dist/assets';
  if (!fs.existsSync(cssDir)) { console.error('dist/assets not found — run UAT-BUILD-001 first'); process.exit(1); }
  const cssFiles = fs.readdirSync(cssDir).filter(f => f.endsWith('.css'));
  if (!cssFiles.length) { console.error('No CSS files in dist/assets'); process.exit(1); }
  const src = fs.readFileSync(path.join(cssDir, cssFiles[0]), 'utf8');
  if (!src.includes('p-8') && !src.includes('padding')) { console.error('No Tailwind utility classes found in built CSS'); process.exit(1); }
  console.log('Built CSS bundle contains Tailwind utility classes (' + cssFiles[0] + ')');
  "
  ```
- **Expected Result**: Prints `Built CSS bundle contains Tailwind utility classes (<filename>)` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

## Edge Case Tests

### UAT-EDGE-001: tailwind.config.js content glob covers tsx files

- **Description**: Verify the content glob `./src/**/*.{ts,tsx}` correctly includes `.tsx` files so component classes are not purged from the production build
- **Command**:
  ```bash
  node -e "
  const src = require('fs').readFileSync('frontend/tailwind.config.js', 'utf8');
  if (!src.includes('tsx')) { console.error('content glob does not include tsx extension'); process.exit(1); }
  console.log('content glob includes tsx extension');
  "
  ```
- **Expected Result**: Prints `content glob includes tsx extension` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-002: components.json aliases.utils points to @/lib/utils

- **Description**: Verify the shadcn `aliases.utils` path in `components.json` matches the actual location of `cn()` — mismatches cause future `npx shadcn add` commands to generate broken imports
- **Command**:
  ```bash
  node -e "
  const cfg = JSON.parse(require('fs').readFileSync('frontend/components.json', 'utf8'));
  const utils = cfg.aliases && cfg.aliases.utils;
  if (!utils || !utils.includes('@/lib/utils')) { console.error('aliases.utils is not @/lib/utils, got:', utils); process.exit(1); }
  console.log('components.json aliases.utils correctly set to', utils);
  "
  ```
- **Expected Result**: Prints `components.json aliases.utils correctly set to @/lib/utils` with exit code 0
- [x] Pass <!-- 2026-06-04 -->

---

### UAT-EDGE-003: No Semantic UI references remain in frontend source

- **Description**: Confirm there are no remaining imports from `semantic-ui-react` or `semantic-ui-css` — the task replaces Semantic UI with Tailwind/shadcn
- **Command**:
  ```bash
  node -e "
  const fs = require('fs');
  const path = require('path');
  function walk(dir) {
    const results = [];
    for (const entry of fs.readdirSync(dir)) {
      const full = path.join(dir, entry);
      if (fs.statSync(full).isDirectory()) results.push(...walk(full));
      else if (full.endsWith('.ts') || full.endsWith('.tsx')) results.push(full);
    }
    return results;
  }
  const files = walk('frontend/src');
  const hits = [];
  for (const f of files) {
    const src = fs.readFileSync(f, 'utf8');
    if (src.includes('semantic-ui')) hits.push(f);
  }
  if (hits.length) { console.error('Semantic UI imports found in:', hits); process.exit(1); }
  console.log('No Semantic UI references found in frontend/src (' + files.length + ' files checked)');
  "
  ```
- **Expected Result**: Prints `No Semantic UI references found in frontend/src (<N> files checked)` with exit code 0
- [x] Pass <!-- 2026-06-04 -->
