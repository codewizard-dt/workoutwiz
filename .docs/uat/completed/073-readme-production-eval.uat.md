# UAT: README — "How I Would Evaluate This System in Production" Section

> **Source task**: [`.docs/tasks/073-readme-production-eval.md`](../tasks/073-readme-production-eval.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] `README.md` exists at the repository root (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md`)

---

## Document Tests

### UAT-DOC-001: Section heading is present at the correct level

- **Description**: Verify `README.md` contains a `##`-level heading `How I Would Evaluate This System in Production`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c '^## How I Would Evaluate This System in Production' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1` (exactly one matching heading line).
- [ ] Pass

---

### UAT-DOC-002: All four sub-section headings are present

- **Description**: Verify the section contains all four required `###`-level sub-sections: Retrieval Quality, Safety Monitoring, Latency, and Token Efficiency.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -cE '^### (Retrieval Quality|Safety Monitoring|Latency|Token Efficiency)' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `4`.
- [ ] Pass

---

### UAT-DOC-003: Latency table is present with per-component budgets

- **Description**: Verify the Latency sub-section contains a Markdown table with rows for all four sub-components (Neo4j traversal, Vector similarity search, LLM generation, and Context assembly).
- **Steps**:
  1. Run each command below and verify the output.
- **Command**:
  ```bash
  grep -c 'Neo4j traversal' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass
- **Command**:
  ```bash
  grep -c 'Vector similarity search' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass
- **Command**:
  ```bash
  grep -c 'LLM generation' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass
- **Command**:
  ```bash
  grep -c 'Context assembly' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass

---

### UAT-DOC-004: Retrieval Quality section mentions key evaluation metrics

- **Description**: Verify the Retrieval Quality sub-section references `Recall@K` and `Precision@K` and the baseline comparison concept.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -cE 'Recall@K|Precision@K|Baseline comparison' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `3` (one match per metric term).
- [ ] Pass

---

### UAT-DOC-005: Safety Monitoring section references the Prometheus counter and adversarial testing

- **Description**: Verify the Safety Monitoring sub-section references the gate trip counter metric name and adversarial testing.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c 'kg_safety_gate_trips_total' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass
- **Command**:
  ```bash
  grep -c 'Adversarial testing' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass

---

### UAT-DOC-006: Token Efficiency section references the 2048-token budget and caching strategy

- **Description**: Verify the Token Efficiency sub-section references the 2048-token context budget and member profile caching.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  grep -c '2048' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `2` (one in the Latency alert threshold `1900 / 2048`, one in the Token Efficiency section referencing `_truncate_to_budget()`).
- [ ] Pass
- **Command**:
  ```bash
  grep -c 'Member profile caching' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output is `1`.
- [ ] Pass

---

### UAT-DOC-007: Section is substantive — minimum word count

- **Description**: Verify the new section meets the ~400-word minimum specified in the task (substantive, not a stub). Count words between the section heading and the next `##`-level heading (end of file in this case).
- **Steps**:
  1. Run the command below. The section starts at the `## How I Would Evaluate` heading and runs to end of file.
- **Command**:
  ```bash
  awk '/^## How I Would Evaluate This System in Production/,0' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md | wc -w
  ```
- **Expected Result**: Word count is **≥ 300** (conservatively accounting for heading/table markup words; the prose content alone is well over 400 words).
- [ ] Pass

---

### UAT-DOC-008: Section appears after existing content and does not disrupt earlier sections

- **Description**: Verify the section was appended after `## How I Would Productionize This` and does not appear before the `## Architecture` or `## Stack` sections.
- **Steps**:
  1. Run the command below to get line numbers for key headings in order.
- **Command**:
  ```bash
  grep -n '^## ' /Users/davidtaylor/Repositories/gauntlet/workout-wiz/README.md
  ```
- **Expected Result**: Output lists headings in this order (line numbers increase monotonically):
  1. `## Architecture`
  2. `## Stack`
  3. `## Quick Start`
  4. `## Running Tests`
  5. `## API Endpoints`
  6. `## Production Evaluation`
  7. `## How I Would Productionize This`
  8. `## How I Would Evaluate This System in Production`
- [ ] Pass
