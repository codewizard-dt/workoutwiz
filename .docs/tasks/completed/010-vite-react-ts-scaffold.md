# 010 — Scaffold Vite + React + TypeScript Frontend Project

> **Depends on**: none
> **Blocks**: [011-tailwind-shadcn-ui](011-tailwind-shadcn-ui.md), [012-react-query-state](012-react-query-state.md)
> **Parallel-safe with**: none

## Objective

Create the `frontend/` directory with a Vite + React + TypeScript project, configured with ESLint, Prettier, and path aliases. This is the foundational scaffold every subsequent frontend task builds on.

## Approach

- `npm create vite@latest frontend -- --template react-ts` for the base scaffold
- TypeScript strict mode
- ESLint flat config (`eslint.config.js`) with `@typescript-eslint` and `eslint-plugin-react-hooks`
- Prettier for formatting (`.prettierrc`)
- `@` path alias resolving to `frontend/src/` in both `tsconfig.json` and `vite.config.ts`
- Proxy `/api` → `http://localhost:8000` in `vite.config.ts` (avoids CORS in dev)

## Steps

### 1. Scaffold Vite project  <!-- agent: general-purpose -->

From the project root:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

This creates `frontend/` with:
- `vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`
- `src/main.tsx`, `src/App.tsx`, `src/App.css`, `src/index.css`
- `public/vite.svg`
- `index.html`

- [x] `frontend/` directory created with Vite scaffold
- [x] `npm run dev` starts the dev server on `http://localhost:5173`

---

### 2. Configure TypeScript strict mode and path alias  <!-- agent: general-purpose -->

Update `frontend/tsconfig.json`:
- Set `"strict": true` in `compilerOptions`
- Add `"baseUrl": "."` and `"paths": { "@/*": ["src/*"] }`

Update `frontend/tsconfig.app.json` (or `tsconfig.node.json` if that's where it belongs — check the scaffold output) with the same paths config.

Update `frontend/vite.config.ts` to add the `@` alias:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

Install `@types/node` for `path` module: `npm install -D @types/node`

- [x] `"strict": true` in tsconfig
- [x] `@` alias resolves to `src/` in both tsconfig and vite.config.ts
- [x] `/api` proxy configured in `vite.config.ts`
- [x] `npm run build` succeeds (no TS errors)

---

### 3. Configure ESLint and Prettier  <!-- agent: general-purpose -->

Install ESLint dependencies:
```bash
npm install -D eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-plugin-react-hooks eslint-plugin-react-refresh
```

The Vite scaffold may already create an `eslint.config.js`. Update it to use `@typescript-eslint/recommended` rules and `react-hooks` plugin.

Install Prettier:
```bash
npm install -D prettier eslint-config-prettier
```

Create `frontend/.prettierrc`:
```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100
}
```

Add scripts to `package.json`:
```json
"lint": "eslint src --ext .ts,.tsx",
"format": "prettier --write src"
```

- [x] `npm run lint` runs without errors on the scaffold files
- [x] `frontend/.prettierrc` created

---

### 4. Clean up scaffold boilerplate  <!-- agent: general-purpose -->

Replace `frontend/src/App.tsx` with a minimal placeholder:
```tsx
export default function App() {
  return <div>Workout Wiz</div>
}
```

Remove `frontend/src/App.css` and the Vite logo imports (keep `index.css` for global styles).

- [x] `frontend/src/App.tsx` is a minimal placeholder (no Vite demo content)
- [x] `npm run dev` still starts without errors

## Acceptance Criteria

- [x] `frontend/` directory exists with Vite + React + TypeScript scaffold
- [x] `npm run dev` starts on port 5173 without errors
- [x] `npm run build` produces `frontend/dist/` without TypeScript errors
- [x] `npm run lint` passes on all files in `src/`
- [x] `@` alias resolves to `src/` in both TS and Vite
- [x] `/api` proxy to `http://localhost:8000` configured
