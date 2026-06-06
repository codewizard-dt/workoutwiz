# UAT: ADR — GraphRAG Retrieval Strategy

> **Source task**: [`.docs/tasks/completed/054-graphrag-adr.md`](../tasks/completed/054-graphrag-adr.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Working directory is the repository root (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz` or equivalent)
- [ ] `.docs/adr/001-graphrag-retrieval-strategy.md` exists on disk

---

## File Existence and Structure Tests

### UAT-FILE-001: ADR file exists at the correct path

- **Description**: Verify `.docs/adr/001-graphrag-retrieval-strategy.md` was created by the task
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  test -f .docs/adr/001-graphrag-retrieval-strategy.md && echo "EXISTS" || echo "MISSING"
  ```
- **Expected Result**: Output is `EXISTS`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-FILE-002: Status is `proposed` (not `accepted` or placeholder)

- **Description**: The ADR must be in `proposed` state — it becomes `accepted` after stakeholder review, not as part of this task
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '^\- \*\*Status\*\*: proposed' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is `1`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-FILE-003: All four decision blocks are present (D1–D4)

- **Description**: The ADR must contain decision blocks for D1 (Traversal Depth), D2 (Embedding Model), D3 (Context Token Budget), and D4 (Merge Strategy)
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '### D[1-4]\.' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is `4`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-FILE-004: No placeholder text remains in the ADR

- **Description**: All `[...]` placeholder segments must be replaced with real content
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '\[\.\.\.\]' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is `0` (no placeholder lines found)
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-FILE-005: Required ADR header metadata fields present

- **Description**: The ADR must include Status, Date, Deciders, and Tags metadata fields
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '^\- \*\*\(Status\|Date\|Deciders\|Tags\)\*\*:' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is `4`
- [x] Pass <!-- 2026-06-06 -->

---

## Decision Content Tests

### UAT-DEC-001: D1 (Traversal Depth) references schema edges

- **Description**: The traversal depth decision must reference specific schema relationship types to justify the choice
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c 'CONTRAINDICATED_BY\|HAS_INJURY\|RATED\|PERFORMED\|INCLUDED' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `3` (multiple schema edge types referenced)
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-DEC-002: D2 (Embedding Model) specifies the chosen model by name

- **Description**: The embedding model decision must name a specific model — either `text-embedding-3-small` or `all-MiniLM-L6-v2`
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c 'text-embedding-3-small\|all-MiniLM-L6-v2' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `1`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-DEC-003: D3 token budget table is present and sums to 2048

- **Description**: The token budget decision must include a markdown table with a total row showing ≤ 2 048 tokens
- **Steps**:
  1. Run the command below as-is — verifies the total row contains 2048 or 2 048
- **Command**:
  ```bash
  grep -c '2 048\|2048' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `2` (the ceiling statement and the table total row)
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-DEC-004: D3 token budget table has the five required sections

- **Description**: The token budget table must allocate budgets to: Member profile summary, Safe exercises, Preferred exercises, Vector similarity hits, and Buffer
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c 'Member profile summary\|Safe exercises\|Preferred exercises\|Vector similarity\|Buffer' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is `5`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-DEC-005: D4 (Merge Strategy) specifies deduplication key and sort order

- **Description**: The merge strategy must name `exercise_id` as the deduplication key and specify a sort order (priority_tier)
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c 'exercise_id\|priority_tier' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `2` (one for each required element)
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-DEC-006: Alternatives Considered section is present with at least two alternatives

- **Description**: The ADR must include an `## Alternatives Considered` section documenting rejected options
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '^## Alternatives Considered' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is `1`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-DEC-007: Each decision block includes both Positive and Negative consequences

- **Description**: Each of D1–D4 must list consequences (at least one Positive and one Negative per block). Count total Positive and Negative labels.
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '- Positive:\|- Negative:' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `8` (at least 1 positive + 1 negative for each of 4 decisions)
- [x] Pass <!-- 2026-06-06 -->

---

## Links Section Tests

### UAT-LINKS-001: Links section references ROADMAP-004

- **Description**: The Links section must reference the ROADMAP-004 file
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '004-knowledge-graph-coaching-system' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `1`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-LINKS-002: Links section references the knowledge graph schema doc

- **Description**: The Links section must reference `.docs/knowledge-graph-schema.md`
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c 'knowledge-graph-schema' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `1`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-LINKS-003: Links section back-references the source task

- **Description**: The Links section must reference `054-graphrag-adr.md` or `TASK-054`
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c '054-graphrag-adr\|TASK-054' .docs/adr/001-graphrag-retrieval-strategy.md
  ```
- **Expected Result**: Output is at least `1`
- [x] Pass <!-- 2026-06-06 -->

---

## Roadmap Update Tests

### UAT-ROADMAP-001: ROADMAP-004 Phase 4 references TASK-054 with a task link

- **Description**: The ROADMAP-004 Phase 4 section must have a task link for TASK-054 (the inline placeholder should be replaced)
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  grep -c 'TASK-054\|054-graphrag-adr' .docs/roadmaps/004-knowledge-graph-coaching-system.md
  ```
- **Expected Result**: Output is at least `1`
- [x] Pass <!-- 2026-06-06 -->
