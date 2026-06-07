# UAT: README — Knowledge Graph (GraphRAG) System Production Evaluation Subsection

> **Source task**: [`.docs/tasks/086-readme-kg-production-eval.md`](../tasks/086-readme-kg-production-eval.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] `README.md` exists at the repository root (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md`)

---

## Document Tests

### UAT-DOC-001: `### Knowledge Graph (GraphRAG) System` subsection heading is present

- **Description**: Verify `README.md` contains an H3-level heading `Knowledge Graph (GraphRAG) System` inside the `## How I Would Evaluate This System in Production` section.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c '^### Knowledge Graph (GraphRAG) System' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1` (exactly one matching heading line).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-002: Subsection is placed under the correct H2 parent

- **Description**: Verify the new `### Knowledge Graph (GraphRAG) System` heading appears after the `## How I Would Evaluate This System in Production` heading and before any subsequent `##`-level heading (or end of file).
- **Steps**:
  1. Run the command below to list H2 and H3 headings with line numbers.
- **Command**:
  ```bash
  grep -n '^##\{1,2\} ' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md | grep -E '## How I Would Evaluate|### Knowledge Graph'
  ```
- **Expected Result**: Two lines are printed. The `## How I Would Evaluate This System in Production` line has a **lower** line number than the `### Knowledge Graph (GraphRAG) System` line, confirming correct placement.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-003: Named-metric table — required rows present

- **Description**: Verify the named-metric table contains rows for all seven required metrics: Recall@K, Precision@K, contraindicated-leak rate, safety-gate trip rate, GraphRAG end-to-end latency, concept-resolution rate, and context-window token budget.
- **Steps**:
  1. Run each command below.
- **Command**:
  ```bash
  grep -c 'Recall@K' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 2` (at least one hit in the named-metric table and one in the Retrieval Quality prose/existing subsection).
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'Precision@K' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 2`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'Contraindicated-leak rate\|contraindicated-leak rate' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'Safety-gate trip rate\|safety-gate trip rate' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'GraphRAG end-to-end latency' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'Concept-resolution rate\|concept-resolution rate' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'Context-window token budget\|context-window token budget' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-004: Named-metric table — correct column headers

- **Description**: Verify the named-metric table uses the three required columns: `Metric`, `Target`, and `How you'd know it's working`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c "| Metric | Target | How you'd know it's working |" /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1` (exactly one table with those column headers).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-005: Contraindicated-leak rate is a 0% hard gate and a release blocker

- **Description**: Verify the subsection explicitly marks the contraindicated-leak rate as 0% and describes it as a release blocker (not merely a metric to trend), consistent with the task's "hard gate" requirement.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c '0%\|0 %' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'release blocker\|hard gate' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-006: GraphRAG latency target is < 5 s (Assessment 2 target)

- **Description**: Verify the subsection uses `< 5 s` (not the `< 3 s` figure from the sibling `### Latency` subsection) as the GraphRAG end-to-end P95 target, and that the contradiction with the existing `### Latency` subsection is explained.
- **Steps**:
  1. Run the command below to confirm the 5 s figure is present.
- **Command**:
  ```bash
  grep -c '< 5 s\|5 seconds' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'Assessment 2\|KNOWLEDGE_GRAPH_ASSESSMENT\|GraphRAG path' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1` — the 5 s figure is tied to its Assessment 2 source.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-007: Per-stage latency breakdown table is present

- **Description**: Verify a per-stage latency breakdown table exists inside the subsection, covering Neo4j SNOMED injury traversal, vector similarity search, context assembly + safety gate, and LLM generation — and that the stages sum to the < 5 s end-to-end target.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c 'Neo4j SNOMED injury traversal\|SNOMED injury traversal' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c '< 100 ms' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1` (Neo4j traversal budget of < 100 ms P99).
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c '< 300 ms\|< 4 s' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 2` (vector search budget of < 300 ms and LLM budget of < 4 s P95).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-008: Concept-resolution failure modes paragraph covers all four failure modes

- **Description**: Verify the subsection's Concept-Resolution Failure Modes content covers the four required failure modes: no matching SNOMED node, ambiguous/multi-joint complaints, missing `MAPS_TO_DISORDER` edges, and SNOMED snapshot drift.
- **Steps**:
  1. Run each command below.
- **Command**:
  ```bash
  grep -c 'MAPS_TO_DISORDER' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'snapshot drift\|SNOMED snapshot' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'ambiguous\|multi-joint' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'snomed_provenance_records' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1` (failure-mode signal referenced in the missing-edges and drift cases).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-009: "How you'd know it's working" wrap-up is present

- **Description**: Verify the subsection contains an explicit "How You'd Know It's Working" (or equivalent H4) section summarising the steady-state signals required by Assessment 2 requirement 9.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c "How You'd Know It's Working\|How you'd know it's working" /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c 'SNOMED-grounded provenance\|provenance' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1` — the wrap-up references SNOMED-grounded provenance traces.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-010: Concept-resolution rate target is ≥ 0.90

- **Description**: Verify the metric table or prose specifies a concept-resolution rate target of ≥ 0.90 (or 90%), matching the task acceptance criteria.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c '0\.90\|0\.9\b\|90%' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-011: Token budget target is < 2 048 tokens / < 2048 tokens

- **Description**: Verify the subsection references the 2 048-token context-window budget in the named-metric table (consistent with the existing `### Token Efficiency` subsection).
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c '2 048\|2048' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 2` (at least one reference in the existing `### Token Efficiency` subsection and at least one in the new KG metric table row).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-012: `kg_safety_gate_trips_total` Prometheus counter is referenced

- **Description**: Verify the subsection references the exact Prometheus counter name `kg_safety_gate_trips_total` used for safety-gate trip rate alerting, consistent with the existing `### Safety Monitoring` subsection.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c 'kg_safety_gate_trips_total' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 1`.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-013: Markdown renders cleanly — tables have aligned pipes and separator rows

- **Description**: Verify the two tables (named-metric table and per-stage latency table) each contain a header separator row (a row of dashes between the header and data rows), and that the file has no unclosed code fences (even count of triple-backtick lines).
- **Steps**:
  1. Run the command below to count header separator rows (rows consisting only of `|`, `-`, `:`, and whitespace).
- **Command**:
  ```bash
  grep -cE '^\|[-: |]+\|$' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `≥ 2` (one separator row per table; existing tables from earlier sections also contribute, so actual count will be higher).
- [x] Pass <!-- 2026-06-07 -->
- **Command**:
  ```bash
  grep -c '^\`\`\`' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is an **even number** (all code fences are properly closed).
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-014: Subsection position — after `### Token Efficiency`, before end of H2 section

- **Description**: Verify `### Knowledge Graph (GraphRAG) System` appears after `### Token Efficiency` within the `## How I Would Evaluate This System in Production` section (i.e., the KG subsection is the last subsection under that H2).
- **Steps**:
  1. Run the command below to get line numbers for both headings.
- **Command**:
  ```bash
  grep -n '### Token Efficiency\|### Knowledge Graph (GraphRAG) System' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Two lines are printed. The `### Token Efficiency` line has a **lower** line number than the `### Knowledge Graph (GraphRAG) System` line.
- [x] Pass <!-- 2026-06-07 -->

---

### UAT-DOC-015: Subsection word count — minimum substantive content

- **Description**: Verify the `### Knowledge Graph (GraphRAG) System` subsection is substantive (not a stub). Extract text from the subsection heading to the next same-or-higher-level heading (or end of file) and count words.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  awk '/^### Knowledge Graph \(GraphRAG\) System/,/^##[^#]/' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md | wc -w
  ```
- **Expected Result**: Word count is **≥ 300** (the subsection spans multiple paragraphs, two tables, and a wrap-up list; prose content alone exceeds this threshold).
- [x] Pass <!-- 2026-06-07 -->
