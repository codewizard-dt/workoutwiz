# 011 — Install Tailwind CSS and shadcn/ui (Replace Semantic UI)

> **Depends on**: [010-vite-react-ts-scaffold](010-vite-react-ts-scaffold.md)
> **Blocks**: [014-port-react-components](014-port-react-components.md)
> **Parallel-safe with**: [012-react-query-state](012-react-query-state.md)

## Objective

Install and configure Tailwind CSS v3 and shadcn/ui in the Vite frontend. Add the core shadcn/ui components needed by the workout tracker UI: Button, Input, Card, Form, Select, Table.

## Approach

- Tailwind CSS v3 via PostCSS (standard Vite integration)
- shadcn/ui CLI (`npx shadcn@latest init`) for component installation
- Components added: Button, Input, Card, Label, Form, Select, Table, Badge
- `cn()` utility from `clsx` + `tailwind-merge` (installed by shadcn init)

## Steps

### 1. Install and configure Tailwind CSS  <!-- agent: general-purpose -->

From `frontend/`:
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Update `frontend/tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

Replace `frontend/src/index.css` content with Tailwind directives:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [x] `tailwindcss`, `postcss`, `autoprefixer` installed
- [x] `tailwind.config.js` created with correct `content` paths
- [x] `index.css` uses Tailwind directives

---

### 2. Initialize shadcn/ui  <!-- agent: general-purpose -->

From `frontend/`:
```bash
npx shadcn@latest init
```

Accept defaults: New York style, Zinc base color, CSS variables for colors. This creates:
- `frontend/src/lib/utils.ts` — exports `cn()` utility
- `frontend/components.json` — shadcn config
- Updates `tailwind.config.js` with shadcn theme extensions

- [x] `shadcn init` completes without errors
- [x] `frontend/src/lib/utils.ts` exists with `cn()` function
- [x] `frontend/components.json` created

---

### 3. Add core UI components  <!-- agent: general-purpose -->

From `frontend/`:
```bash
npx shadcn@latest add button input card label form select table badge
```

This creates component files in `frontend/src/components/ui/`.

- [x] `frontend/src/components/ui/button.tsx` exists
- [x] `frontend/src/components/ui/input.tsx` exists
- [x] `frontend/src/components/ui/card.tsx` exists
- [x] `frontend/src/components/ui/form.tsx` exists
- [x] `frontend/src/components/ui/select.tsx` exists
- [x] `frontend/src/components/ui/table.tsx` exists

---

### 4. Smoke-test component rendering  <!-- agent: general-purpose -->

Update `frontend/src/App.tsx` to render one Button component:
```tsx
import { Button } from '@/components/ui/button'

export default function App() {
  return (
    <div className="p-8">
      <Button>Workout Wiz</Button>
    </div>
  )
}
```

Run `npm run dev` and verify the button renders with Tailwind styles.

- [x] `npm run dev` shows a styled Button component
- [x] `npm run build` succeeds without errors

## Acceptance Criteria

- [x] Tailwind CSS processes classes in all `src/**/*.{ts,tsx}` files
- [x] shadcn/ui components importable from `@/components/ui/`
- [x] `cn()` utility exported from `@/lib/utils`
- [x] `npm run build` succeeds with Tailwind and shadcn installed
- [x] Button, Input, Card, Form, Select, Table, Badge components all exist

---
**UAT**: [`.docs/uat/011-tailwind-shadcn-ui.uat.md`](../uat/011-tailwind-shadcn-ui.uat.md)
