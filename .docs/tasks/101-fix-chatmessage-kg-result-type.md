# 101 — Add kg_result to Exported ChatMessage Type

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [099-seed-multi-persona-context](099-seed-multi-persona-context.md), [100-document-ope-copper-ontologies](100-document-ope-copper-ontologies.md)

## Objective

Add the missing `kg_result` field (with its `KGResult` shape) to the exported `ChatMessage` interface in `frontend/src/types/index.ts` so it matches the API response and is no longer only present on a divergent inline type inside `useChat`.

## Approach

Lift the `RecommendedExercise` and `KGResult` interfaces (currently declared locally in `frontend/src/hooks/useChat.ts`) into `frontend/src/types/index.ts`, add `kg_result?: KGResult | null` to the exported `ChatMessage`, then update `useChat.ts` to import these types from `@/types` and delete its divergent local `ChatMessage`, `KGResult`, and `RecommendedExercise` declarations. This restores a single source of truth.

## Prerequisites

- [ ] Confirm `frontend/src/pages/ChatPage.tsx` consumes `msg.kg_result` (`.fallback_used`, `.overall_reasoning`, `.exercises[].exercise_id`, `.exercises.length`) so the lifted shape must stay structurally identical.
- [ ] Confirm `AgentStep` and `WorkoutDraft` already exist in `frontend/src/types/index.ts` (they do) so the lifted `ChatMessage` field set needs no other new types.

---

## Steps

### 1. Define KGResult type & extend ChatMessage in types/index.ts  <!-- agent: general-purpose -->

- [ ] In `frontend/src/types/index.ts`, add an exported `RecommendedExercise` interface with the exact fields from the current `useChat.ts` copy: `exercise_id: string`, `name: string`, `sets?: number`, `reps?: number`, `duration_seconds?: number`, `weight_kg?: number`, `reasoning: string`.
- [ ] In `frontend/src/types/index.ts`, add an exported `KGResult` interface: `exercises: RecommendedExercise[]`, `overall_reasoning: string`, `fallback_used: boolean`.
- [ ] In the exported `ChatMessage` interface (currently lines 68-76, fields `id`, `role`, `content`, `route?`, `confidence?`, `steps?`, `workout_draft?`), add `kg_result?: KGResult | null`.

### 2. Have useChat use the exported type  <!-- agent: general-purpose -->

- [ ] In `frontend/src/hooks/useChat.ts`, delete the local `export interface RecommendedExercise`, `export interface KGResult`, and `export interface ChatMessage` declarations (the inline divergence).
- [ ] Import `ChatMessage`, `KGResult`, and `AgentStep` (and any other now-undefined names such as `WorkoutDraft`) from `@/types` at the top of `useChat.ts`, replacing the inline `import('@/types').WorkoutDraft` usages.
- [ ] Verify the API-response object literal type inside `sendMessage` (the `data` cast with `kg_result?: KGResult | null`) still resolves against the imported `KGResult`.

### 3. Verification  <!-- agent: general-purpose -->

- [ ] `cd frontend && npm run build` (or `tsc`) passes with no type errors.

## Acceptance Criteria

- [ ] The exported `ChatMessage` in `frontend/src/types/index.ts` includes `kg_result?: KGResult | null`, and `KGResult` + `RecommendedExercise` are exported from `frontend/src/types/index.ts`.
- [ ] `frontend/src/hooks/useChat.ts` no longer declares its own `ChatMessage`, `KGResult`, or `RecommendedExercise`; it imports them from `@/types`.
- [ ] `frontend/src/pages/ChatPage.tsx` still type-checks against the single exported `ChatMessage`/`KGResult` with no source changes required.
- [ ] `npm run build` (or `tsc`) in `frontend/` reports zero type errors.
