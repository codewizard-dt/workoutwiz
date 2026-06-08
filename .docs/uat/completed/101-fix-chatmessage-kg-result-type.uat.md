# UAT: Add kg_result to Exported ChatMessage Type

> **Source task**: [`.docs/tasks/101-fix-chatmessage-kg-result-type.md`](../tasks/101-fix-chatmessage-kg-result-type.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Node.js and npm installed
- [ ] `cd frontend && npm install` has been run (dependencies present)
- [ ] Working directory is the repo root for all commands

---

## Static Verification Tests

All tests are static (compile-time). No backend server or browser is required.

### UAT-STATIC-001: TypeScript strict type-check passes for touched files

- **Description**: Verify `tsc --noEmit` exits cleanly with no errors in the four files changed by TASK-101: `types/index.ts`, `hooks/useChat.ts`, `hooks/index.ts`, and `pages/ChatPage.tsx`. Pre-existing errors in `hooks/useDraftWorkout.ts` and `pages/CoachPage.tsx` are out of scope.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd frontend && npx tsc --noEmit 2>&1 | grep -E "error TS" | grep -v "useDraftWorkout\|CoachPage"
  ```
- **Expected Result**: No output (empty). The grep produces no lines, meaning zero `error TS` entries in the TASK-101 files.
- [x] Pass <!-- 2026-06-08 -->

### UAT-STATIC-002: `RecommendedExercise` interface is exported from `types/index.ts`

- **Description**: Verify `RecommendedExercise` is declared and exported at the canonical type location with all required fields.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  grep -n 'export interface RecommendedExercise' frontend/src/types/index.ts
  ```
- **Expected Result**: One line matching `export interface RecommendedExercise` in `frontend/src/types/index.ts`, e.g. `46:export interface RecommendedExercise {`
- [x] Pass <!-- 2026-06-08 -->

### UAT-STATIC-003: `KGResult` interface is exported from `types/index.ts`

- **Description**: Verify `KGResult` is declared and exported from the canonical type file.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  grep -n 'export interface KGResult' frontend/src/types/index.ts
  ```
- **Expected Result**: One line matching `export interface KGResult` in `frontend/src/types/index.ts`, e.g. `56:export interface KGResult {`
- [x] Pass <!-- 2026-06-08 -->

### UAT-STATIC-004: `ChatMessage` in `types/index.ts` includes `kg_result` field

- **Description**: Verify the canonical exported `ChatMessage` interface has the `kg_result?: KGResult | null` field.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  grep -n 'kg_result' frontend/src/types/index.ts
  ```
- **Expected Result**: At least one line showing `kg_result?: KGResult | null` inside the `ChatMessage` interface body in `frontend/src/types/index.ts`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-STATIC-005: `useChat.ts` has no local `ChatMessage`, `KGResult`, or `RecommendedExercise` declarations

- **Description**: Verify the divergent local interface declarations have been removed from `useChat.ts`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  grep -n 'export interface' frontend/src/hooks/useChat.ts
  ```
- **Expected Result**: No output (empty). `useChat.ts` exports no interfaces of its own.
- [x] Pass <!-- 2026-06-08 -->

### UAT-STATIC-006: `useChat.ts` imports `ChatMessage`, `KGResult`, `WorkoutDraft` from `@/types`

- **Description**: Verify `useChat.ts` imports all previously-local types from the canonical `@/types` path.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  grep -n "from '@/types'" frontend/src/hooks/useChat.ts
  ```
- **Expected Result**: One line: `import type { AgentStep, ChatMessage, KGResult, WorkoutDraft } from '@/types'`
- [x] Pass <!-- 2026-06-08 -->

### UAT-STATIC-007: `hooks/index.ts` barrel re-exports `ChatMessage` and `AgentStep` from `@/types`

- **Description**: Verify the hooks barrel file re-exports the types from `@/types` (not the old `./useChat` source).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  grep -n 'ChatMessage\|AgentStep' frontend/src/hooks/index.ts
  ```
- **Expected Result**: One line: `export type { ChatMessage, AgentStep } from "@/types"` — with no reference to `./useChat`.
- [x] Pass <!-- 2026-06-08 -->

---

## UI Tests

### UAT-UI-001: Chat page renders `kg_result` data from assistant messages

- **Description**: Verify the Chat UI correctly reads `msg.kg_result` using the unified `ChatMessage` type from `@/types`. This confirms `ChatPage.tsx` resolves the type without source changes.
- **Page**: `http://localhost:5173/chat` (or the dev server port)
- **Steps**:
  1. Start the frontend dev server (`cd frontend && npm run dev`)
  2. Start the backend dev server if not already running
  3. Log in and navigate to `/chat`
  4. Send a message that triggers the `KNOWLEDGE_GRAPH` route (e.g., "What exercises suit my injuries?")
  5. Wait for the assistant reply
  6. Observe the assistant message card
- **Expected Result**: When the response route is `KNOWLEDGE_GRAPH` and `kg_result` is non-null, the chat message card renders: the "Knowledge Graph" section header, a "Recommended Exercises (N)" count, at least one exercise name, and the `overall_reasoning` text block. No TypeScript or runtime errors in the browser console.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->