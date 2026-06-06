---
name: workout-wiz-brand-design
description: Enforce Workout Wiz ember design guidelines when implementing or modifying frontend routes. Reads design tokens, component patterns, and brand rules. Auto-triggered by PostToolUse hook when route files are edited.
user-invocable: true
---

You are implementing a Workout Wiz frontend route. Before writing any UI code, read:

1. `frontend/src/design-system/design-system.css` — all CSS custom properties (entry point with @imports)
2. `frontend/src/design-system/tokens/` — token files: colors, typography, spacing, effects, base
3. `frontend/src/design-system/components/` — original prototype JSX for reference
4. `frontend/design-system/_ds/workout-wiz-design-system-1665e3a1-7ca2-48e0-9a8f-96a62adf5d5d/readme.md` — full brand rules

Key non-negotiables:

### Palette & Color
- **Ember** (`--ember-500`, oklch 0.645 0.190 38) is the brand primary and sole action color. Use it for CTAs, active states, and focus rings.
- **Amber** gold (`--amber-500`) is the secondary accent for highlights, PRs, and energy indicators only.
- Neutrals are **stone** — warm-tinted greys (hue ~50), never cold/blue.
- Background is warm off-white (`--stone-50`). All surfaces are opaque.
- **No green anywhere** — even "success / logged" states use honey-gold, not green.
- The signature gradient (`--gradient-ember`, amber → ember → deep ember, 135°) is used only on: logo, one hero CTA per view (`Button variant="gradient"`), progress fills, rest-timer ring. Never overuse it.

### Typography
- **Geist** for all UI text and display copy. No other typeface.
- **Geist Mono** for ALL numerics: reps × weight, timers, stats, volume totals. Apply tabular figures + slashed zero via `.ww-num`.
- Type scale is a 1.2 minor-third on a 16px base; default UI body is 14px.
- Display sizes use tightened tracking (`-0.03em`).

### Spacing & Density
- 4px grid throughout. App is dense.
- Default controls are 32px tall (h-8).
- Cards pad 16px; stacks gap 16px.
- Reading columns cap ~672px. App shell: 240px sidebar + fluid main.

### Corner Radii
- Base `--radius`: 10px
- Cards: 14px (`--radius-xl`)
- Sheets/hero: 20px
- Pills, badges, avatars: fully round
- Inputs and buttons: 8px

### Cards
- Warm hairline ring (`--ring-card`, ~8% brown) + soft warm shadow — NOT a hard 1px border.
- Rounded 14px, white surface.
- `interactive` cards: lift 2px + larger shadow on hover.

### Shadows
- Always warm-tinted (brown/amber cast), never neutral grey.
- Five steps: xs → xl, plus `--shadow-ember` for gradient CTA and active timer.

### Borders
- `--border` (stone-200): dividers and tables.
- `--border-strong` (stone-300): inputs and outline buttons.

### Motion
- `--ease-out` (cubic-bezier 0.22,1,0.36,1) at 120–180ms for hovers/state transitions.
- `--ease-spring` for toggles, checkmarks, switch thumb.
- Timer/progress fills ease over 280ms.
- No bounce on content. No infinite decorative loops.

### Interactive States
- **Hover:** buttons darken to `-600` step (ember-500 → ember-600); ghost/outline fill `--muted`; cards lift; table rows wash `--ember-50`; chips gain ember border + tint.
- **Press:** buttons translate down 1px (`active:translateY(1px)`). No scale-down.
- **Focus:** 3px ember ring at ~18–40% opacity + solid ember border. Consistent across all interactive elements.

### Iconography
- **Lucide only** — outline style, 1.75px stroke, rounded caps/joins, 24px default (scale to 14–18px inline). No hand-rolled SVG icons.
- Default color: stone-800. Ember tint (`--ember-500`) for: `dumbbell`, `flame`, `sparkles`, `timer`, `trophy`, `heart-pulse`, `trending-up`.
- Brand mark: lightning-bolt sigil (`assets/logo-mark.svg`), ember-gradient filled.
- No emoji as iconography.

### Copy & Voice
- **Sentence case everywhere** — buttons ("Save workout"), nav ("Build workout"), titles. UPPERCASE only for tiny overlines and agent route tags (`WORKOUT_GENERATE`).
- Voice: knowledgeable training partner — direct, encouraging, never preachy or hype-y.
- Numbers are the content: written compactly (`3×10`, `60 kg`, `0:45`) in Geist Mono.
- Coach replies: 1–3 sentences, then offer the next action.
- **No emoji in the UI.** Energy comes from ember color and bolt iconography.
- Off-topic asks: friendly redirect, not refusal ("I'm your fitness coach — I can plan workouts, answer training questions, and log sessions.").

### Dark Mode
- Scope: `.dark` / `[data-theme="dark"]` — "coal & ember."
- Near-black warm stone surfaces with same ember primary.
- Use only for active-workout / focus contexts.

### Topbar
- Sticky, 86% surface tint + 10px backdrop-blur.

### Prohibited
- No green in any state (success, valid, logged).
- No cold/blue-tinted greys or shadows.
- No emoji as UI elements.
- No infinite decorative CSS animations.
- No scale-down on press (use translateY(1px) instead).
- No hard 1px borders on cards (use ring + shadow).
- No gradient overuse — one gradient CTA per view maximum.
- No typefaces other than Geist / Geist Mono.
- No icon systems other than Lucide.
