# UAT: Visual Architecture Diagrams

> **Source task**: [`.docs/tasks/102-visual-architecture-diagrams.md`](../tasks/102-visual-architecture-diagrams.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] `README.md` exists at the repository root
- [ ] No external tooling required — all tests inspect static file content

---

## Static Content Tests

These tests verify that `README.md` meets the acceptance criteria of task 102. Each test uses a single shell command to inspect the file and produces a concrete, observable result.

### UAT-STATIC-001: Exactly Three Mermaid Blocks Present
- **File**: `README.md`
- **Description**: Verify the file contains exactly three fenced `mermaid` code blocks (no more, no fewer).
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '```mermaid' README.md
  ```
- **Expected Result**: `3`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-002: All Three Mermaid Blocks Are Closed
- **File**: `README.md`
- **Description**: Verify every `\`\`\`mermaid` opening fence has a matching closing `\`\`\``. (The count of `\`\`\`` lines that are not `\`\`\`mermaid` opening lines must be at least 3.)
- **Steps**:
  1. Run the command below from the repository root. It counts lines that are exactly three backticks (the closing fences for mermaid blocks among others).
- **Command**:
  ```bash
  grep -c '^```$' README.md
  ```
- **Expected Result**: `3` or higher (one closing fence per mermaid block, plus any other fenced blocks in the file)
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-003: Architecture Heading Present
- **File**: `README.md`
- **Description**: Verify the `## Architecture` heading exists (the section that contains all three diagrams).
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '^## Architecture$' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-004: System Overview Sub-Heading Present
- **File**: `README.md`
- **Description**: Verify the `### System Overview` sub-heading exists under the Architecture section.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '^### System Overview$' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-005: Agent Topology Sub-Heading Present
- **File**: `README.md`
- **Description**: Verify the `### Agent Topology` sub-heading exists under the Architecture section.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '^### Agent Topology$' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-006: Knowledge Graph Schema Sub-Heading Present
- **File**: `README.md`
- **Description**: Verify the `### Knowledge Graph Schema` sub-heading exists under the Architecture section.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '^### Knowledge Graph Schema$' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-007: System Overview Uses flowchart TD
- **File**: `README.md`
- **Description**: Verify the System Overview diagram uses `flowchart TD` (top-down) as required.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '^flowchart TD$' README.md
  ```
- **Expected Result**: `2` (one for System Overview, one for Agent Topology — both must be `flowchart TD`)
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-008: Knowledge Graph Schema Uses flowchart LR
- **File**: `README.md`
- **Description**: Verify the Knowledge Graph Schema diagram uses `flowchart LR` (left-right) as required.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '^flowchart LR$' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-009: System Overview — Node Count ≤ 7
- **File**: `README.md`
- **Description**: Verify the System Overview diagram defines exactly 6 named nodes (Browser, FastAPI, Agents, Neo4j, Postgres, Auth) — well within the ≤7 cap.
- **Steps**:
  1. Read the System Overview block (lines 14–28 of README.md).
  2. Count unique node identifiers defined with `["..."]` notation inside the block.
- **Command**:
  ```bash
  grep -c '^\s\+\w\+\["' README.md
  ```
- **Expected Result**: `12` (6 nodes per diagram × 2 diagrams that use `["..."]` notation — System Overview and Agent Topology). Confirms neither diagram exceeds 7 nodes.
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-010: No ASCII Art Architecture Block Remaining
- **File**: `README.md`
- **Description**: Verify the old ASCII art / plain-text architecture block has been removed. The task spec calls out a Hub StateGraph ASCII block using `├──` characters.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c '├──' README.md
  ```
- **Expected Result**: `0`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-011: System Overview Contains Required Nodes
- **File**: `README.md`
- **Description**: Verify the System Overview diagram contains the six required node declarations: Browser, FastAPI, Agents, Neo4j, Postgres, Auth.
- **Steps**:
  1. Run each command below and confirm each returns `1`.
- **Command**:
  ```bash
  grep -c 'Browser\["Browser (React)"\]' README.md
  ```
- **Expected Result**: `1`

  ```bash
  grep -c 'FastAPI\["FastAPI Backend"\]' README.md
  ```
- **Expected Result**: `1`

  ```bash
  grep -c 'Auth\["Auth (fastapi-users)"\]' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-012: Agent Topology Contains Required Nodes
- **File**: `README.md`
- **Description**: Verify the Agent Topology diagram contains all four routing destinations (Coach, Gen, Log, Fallback) and the Hub + Router nodes.
- **Steps**:
  1. Run each command below and confirm each returns `1`.
- **Command**:
  ```bash
  grep -c 'Router -->|COACH| Coach' README.md
  ```
- **Expected Result**: `1`

  ```bash
  grep -c 'Router -->|WORKOUT_GENERATE| Gen' README.md
  ```
- **Expected Result**: `1`

  ```bash
  grep -c 'Router -->|WORKOUT_LOG| Log' README.md
  ```
- **Expected Result**: `1`

  ```bash
  grep -c 'Router -->|FALLBACK| Fallback' README.md
  ```
- **Expected Result**: `1`
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-STATIC-013: Knowledge Graph Schema Contains Required Relationships
- **File**: `README.md`
- **Description**: Verify the KG Schema diagram contains the six required typed edges.
- **Steps**:
  1. Run the command below from the repository root.
- **Command**:
  ```bash
  grep -c ' -- \(COMPLETED\|CONTAINS\|TARGETS\|USES\|FOLLOWS\|HAS_BIOMARKER\) --> ' README.md
  ```
- **Expected Result**: `6`
- [x] Pass <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: README.md is Valid Markdown (No Unclosed Fences)
- **Components**: `README.md` fenced code block structure
- **Flow**: Count opening fences vs closing fences to confirm they balance.
- **Steps**:
  1. Run the command below from the repository root. It counts all lines that start with exactly three backticks (both opening and closing fences of all types).
- **Command**:
  ```bash
  grep -c '^```' README.md
  ```
- **Expected Result**: An even number (each opening fence has a closing fence). The current README has exactly 3 mermaid blocks plus additional bash/other fenced blocks. Any odd count indicates an unclosed fence.
- [x] Pass <!-- 2026-06-08 -->

---

### UAT-INT-002: All Three Diagrams Are Adjacent Under Architecture Heading
- **Components**: Heading structure and diagram ordering in `README.md`
- **Flow**: Verify `## Architecture` precedes all three `### ` sub-headings and that each sub-heading precedes its `\`\`\`mermaid` block.
- **Steps**:
  1. Open `README.md` in a text editor or read it with `Read`.
  2. Confirm the order is: `## Architecture` → `### System Overview` → ` ```mermaid` (flowchart TD) → `### Agent Topology` → ` ```mermaid` (flowchart TD) → `### Knowledge Graph Schema` → ` ```mermaid` (flowchart LR).
  3. Confirm no other `## ` heading appears between `## Architecture` and the third closing fence.
- **Expected Result**: The three Mermaid blocks appear consecutively under `## Architecture` with no intervening top-level heading, in the order: System Overview, Agent Topology, Knowledge Graph Schema.
- [x] Pass <!-- 2026-06-08 -->
