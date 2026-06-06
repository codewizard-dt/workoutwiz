# Workout Wiz — Design System

**Workout Wiz** is an AI-powered fitness coaching web app. You chat with a coach that **plans** workouts tuned to your body and equipment, **logs** what you did in natural language, and **answers** training questions — routed through a multi-agent layer behind the scenes. The product also offers a browsable exercise library and a manual workout builder. The throughline: *train smarter, not harder*, with a coach that adapts to you.

This design system recreates the product's foundations and components, recolored from the stock neutral/shadcn base into a warm **"ember"** palette — flame orange + amber gold over sand-stone neutrals (per brand direction: warm reddish-yellowish, **no green**).

---

## Sources

Everything here was reverse-engineered from the real product and brand inputs. Store these for future iteration; the reader may not have access.

- **Codebase (primary source of truth):** `codewizard-dt/workoutwiz` → https://github.com/codewizard-dt/workoutwiz
  - Frontend: `frontend/` — Vite + React 19 + TypeScript + Tailwind 3 + **shadcn/ui** (on Base UI primitives), TanStack Query, Axios. Key files read: `src/index.css` (token contract), `src/components/ui/{button,card,badge,input,select}.tsx`, `src/pages/{Login,Register,Workouts,WorkoutNew,Exercises}.tsx`, `package.json`.
  - Backend (context only): FastAPI + SQLAlchemy + PostgreSQL + a LangGraph multi-agent hub routing `COACH | WORKOUT_GENERATE | WORKOUT_LOG | FALLBACK`.
  - **Explore the repo further** to build higher-fidelity work — the page components and API types (`types.ts`, hooks under `src/hooks/`) describe the real data shapes (workouts → sequences → sets; exercises with muscle groups, equipment, priority tiers).
- **Brand mark:** the app's `favicon.svg` — a lightning-bolt sigil (originally purple). Recolored to ember and used as the Workout Wiz mark.
- **Mood references** (user-supplied screenshots): athletic training photography, dark workout-app UIs with exercise cards, calendars, set tables, and timers. Directional only.
- **Font:** Geist (the product ships `@fontsource-variable/geist`). Loaded here from Google Fonts.
- **Icons:** Lucide (`lucide-react` in product; Lucide UMD/CDN here).

> ⚠️ The repo's stock `index.css` tokens are **neutral greyscale** (shadcn default). The warm ember palette in this system is an intentional brand layer on top of that contract — the *semantic aliases* (`--primary`, `--card`, `--border`, …) match shadcn 1:1 so the recolor drops into the real app cleanly.

---

## Content Fundamentals

How Workout Wiz writes. Pulled from the product's microcopy and coaching transcripts.

- **Voice:** a knowledgeable training partner — direct, encouraging, never preachy or hype-y. Thinks in sets, reps, recovery, and volume.
- **Person:** addresses the user as **"you"**; the coach speaks as **"I"** ("I can help with planning, logging, and coaching"). Plain, confident.
- **Tone:** practical and warm. Celebrates effort with specifics ("that's 1,800 kg of volume on chest today") rather than empty praise ("Great job!!").
- **Casing:** Sentence case everywhere — buttons ("Save workout", "Add to Today"), nav ("Build workout"), titles. Reserve UPPERCASE for tiny overlines/eyebrows and the agent route tags (`WORKOUT_GENERATE`).
- **Numbers are the content.** Reps, weight, duration, volume, streaks. Written compactly: `3×10`, `60 kg`, `0:45`, `12,480 kg`. Always in the mono face.
- **Brevity:** UI copy is terse; coach replies are 1–3 sentences, then offer the next action ("Want me to add it to Today?").
- **Scope discipline:** off-topic asks get a friendly redirect, not a refusal ("I'm your fitness coach — I can plan workouts, answer training questions, and log sessions.").
- **Emoji:** none in the UI. Energy comes from the flame/bolt iconography and ember color, not emoji.
- **Examples:**
  - Empty coach state: *"What are we training today?"*
  - Hero: *"Train smarter, not harder."* / *"Your AI strength coach"*
  - Logging confirmation: *"Logged — bench press 3×10 @ 60 kg plus a 20-min run."*
  - Coaching: *"For hypertrophy most lifters do well with 1–2 rest days a week…"*

---

## Visual Foundations

- **Color vibe:** warm and energetic. **Ember** flame-orange (`--ember-500`, oklch 0.645 0.190 38) is the brand core and primary action color; **amber** gold (`--amber-500`) is the secondary accent for highlights, PRs and "energy." Neutrals are **stone** — greys warmed with a low-chroma orange hue (~50) so nothing reads cold or blue. Backgrounds are a warm off-white (`--stone-50`). **No green anywhere** — even "success / logged" reads as honey-gold.
- **Signature gradient:** `--gradient-ember` (amber → ember → deep ember, 135°) on the logo, the one hero CTA per view (`Button variant="gradient"`), progress fills, and the rest-timer ring. Used sparingly — it's the brand's exclamation point.
- **Type:** **Geist** for everything UI and display — clean, modern, athletic; tightened tracking at display sizes (`-0.03em`). **Geist Mono** for *all* numerics (reps × weight, timers, stats, volume) with tabular figures + slashed zero — the mono numerals are a core brand signature. Scale is a 1.2 minor-third on a 16px base; UI default body is a dense 14px.
- **Backgrounds:** flat warm surfaces, not photography or texture in-app. One soft radial ember wash behind the login. No noise/grain. Imagery (when present, e.g. marketing) skews warm and high-energy.
- **Spacing & density:** 4px grid, app-dense. Controls are 32px tall (h-8) by default; cards pad 16px; stacks gap 16px. Reading columns cap ~672px; the app shell is a 240px sidebar + fluid main.
- **Corner radii:** soft. `--radius` base 10px; cards use 14px (`--radius-xl`), sheets/hero 20px, pills/badges/avatars fully round. Inputs/buttons 8px.
- **Cards:** a warm hairline **ring** (`--ring-card`, ~8% brown) plus a soft warm shadow — not a hard 1px border. Rounded 14px, white surface. `interactive` cards lift 2px with a larger shadow on hover.
- **Shadows:** warm-tinted (brown/amber cast, never neutral grey), in five steps (xs → xl) plus a dedicated **ember glow** (`--shadow-ember`) for the gradient CTA and active timer.
- **Borders:** `--border` = stone-200 hairlines for dividers/tables; `--border-strong` = stone-300 for inputs and outline buttons.
- **Motion:** quick and confident. `--ease-out` (cubic 0.22,1,0.36,1) at 120–180ms for hovers/state; a gentle spring (`--ease-spring`) for toggles, checkmarks, and the switch thumb. Timer/progress fills ease over 280ms. No bounce on content, no infinite decorative loops.
- **Hover states:** buttons darken to the `-600` step (primary→ember-600); ghost/outline fill with `--muted`; cards lift; table rows wash to `--ember-50`; chips gain an ember border + tint.
- **Press states:** buttons translate down 1px (`active:translateY(1px)`) — a physical "push." No scale-down.
- **Focus:** 3px ember ring at ~18–40% opacity plus a solid ember border. Consistent across inputs, buttons, toggles.
- **Transparency & blur:** sparingly — the sticky topbar uses an 86% surface tint + 10px backdrop-blur; focus rings and tints use `oklch(… / α)`. Surfaces themselves are opaque.
- **Dark mode:** a "coal & ember" scope (`.dark` / `[data-theme="dark"]`) for active-workout / focus contexts — near-black warm stone surfaces with the same ember primary.

---

## Iconography

- **System:** **Lucide** — the product uses `lucide-react`. Outline, **1.75px** stroke, rounded caps/joins, 24px default (scales to 14–18px inline). This is the only icon system; match its weight if you add glyphs.
- **Color:** stone-800 by default; **ember tint** (`--ember-500`) for activity/energy glyphs (`dumbbell`, `flame`, `sparkles`, `timer`, `trophy`, `heart-pulse`, `trending-up`).
- **Common glyphs:** `dumbbell`, `flame`, `sparkles` (coach/AI), `calendar-days` / `calendar-check`, `trophy`, `timer`, `play` / `pause`, `plus` / `plus-circle`, `check`, `search`, `trash-2`, `arrow-up` (send), `log-out`, `layers`.
- **Brand mark:** the lightning-**bolt** sigil (`assets/logo-mark.svg`), ember-gradient filled — energy/spark/"wizard." Light-on-dark variant `assets/logo-mark-light.svg`; wordmark `assets/logo-wordmark.svg`. The coach avatar is the bolt glyph on a coal disc.
- **Emoji / unicode:** not used as iconography. (Stat deltas use small ▲/▼ glyphs only.)
- **No hand-rolled SVG icons** — use Lucide. Available via CDN: `https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js`.

---

## Index / Manifest

**Root**
- `styles.css` — entry point (imports only). Consumers link this.
- `readme.md` — this guide.
- `SKILL.md` — Agent-Skill front matter for Claude Code use.

**`tokens/`** (all `@import`ed by `styles.css`)
- `colors.css` — ember / amber / stone ramps, semantic status, shadcn aliases (light + `.dark`), gradients.
- `typography.css` — Geist + Geist Mono (Google Fonts), families, weights, type scale, tracking.
- `spacing.css` — 4px scale, control heights, layout widths.
- `effects.css` — radii, warm shadows, motion (easings/durations), z-index.
- `base.css` — light resets + element defaults + utilities (`.ww-num`, `.ww-eyebrow`, `.ww-scroll`).

**`components/`** (React primitives — `window.WorkoutWizDesignSystem_1665e3`)
- `core/` — **Button**, **IconButton**, **Badge**, **Tag**, **Avatar**, **Card** (+Header/Title/Description/Content/Footer).
- `forms/` — **Input**, **Textarea**, **Select**, **Field**/**Label**, **Checkbox**/**Radio**, **Switch**.
- `navigation/` — **Tabs** (segmented + underline).
- `fitness/` — **StatTile**, **Progress**, **ProgressRing** (rest timer), **ChatBubble** (coach — signature), **SetRow**.
- `ui.css` — component classes (consumed via `styles.css`).

**`guidelines/`** — foundation specimen cards (Colors, Type, Spacing, Brand) for the Design System tab.

**`ui_kits/app/`** — full interactive app recreation (login → coach chat → today → exercises → builder). See its `README.md`.

**`assets/`** — `logo-mark.svg`, `logo-mark-light.svg`, `logo-wordmark.svg`.

---

## Substitutions & flags
- **Font:** Geist is loaded from **Google Fonts** rather than bundled `.ttf` files (the product pulls it from `@fontsource-variable/geist`, not committed binaries). If you need offline/self-hosted fonts, drop the Geist + Geist Mono `.woff2` files into an `assets/fonts/` folder and add `@font-face` rules. *Flagged for the user.*
- **Palette:** the warm ember palette is a **brand recolor** of the repo's neutral shadcn tokens, per the user's direction. The structural token contract is unchanged.
- **Mark color:** the original favicon bolt is purple; recolored to ember to fit the brand. Confirm if a different official mark exists.
