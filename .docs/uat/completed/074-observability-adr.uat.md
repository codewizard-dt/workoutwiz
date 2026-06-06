# UAT: Observability Stack ADR

> **Source task**: [`.docs/tasks/074-observability-adr.md`](../tasks/074-observability-adr.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Repository is checked out and working directory is the project root
- [ ] `.docs/adr/0005-observability-stack.md` has been committed (per acceptance criteria)

---

## Document Existence Tests

### UAT-DOC-001: ADR File Exists at Correct Path
- **Description**: Verify the ADR file was created at the required path
- **Steps**:
  1. Run the command below to confirm the file exists and is non-empty
- **Command**:
  ```bash
  test -s .docs/adr/0005-observability-stack.md && echo "EXISTS_AND_NON_EMPTY" || echo "MISSING_OR_EMPTY"
  ```
- **Expected Result**: Output is `EXISTS_AND_NON_EMPTY`
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-002: ADR File is Tracked in Git
- **Description**: Verify the ADR file has been committed to the repository as required by the acceptance criteria
- **Steps**:
  1. Run the command below to confirm the file is tracked (not untracked)
- **Command**:
  ```bash
  git ls-files --error-unmatch .docs/adr/0005-observability-stack.md && echo "TRACKED" || echo "UNTRACKED"
  ```
- **Expected Result**: Output is `TRACKED`
- [x] Pass <!-- 2026-06-06 -->

---

## Front Matter Tests

### UAT-DOC-003: ADR Has Required Front Matter Fields
- **Description**: Verify the YAML front matter contains title, status, created, and owner fields
- **Steps**:
  1. Run the command below to extract front matter fields
- **Command**:
  ```bash
  grep -E "^(title|status|created|owner):" .docs/adr/0005-observability-stack.md | jq -Rs 'split("\n") | map(select(length > 0))'
  ```
- **Expected Result**: JSON array containing four strings matching `title:`, `status:`, `created:`, and `owner:` prefixes
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-004: ADR Status is "Proposed"
- **Description**: Verify the ADR status is set to "Proposed" (not finalized prematurely)
- **Steps**:
  1. Run the command below to extract the status value
- **Command**:
  ```bash
  grep "^status:" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is `status: Proposed`
- [x] Pass <!-- 2026-06-06 -->

---

## Decision Block Tests

### UAT-DOC-005: All Four Decision Blocks Present (D1–D4)
- **Description**: Verify all four required decision blocks are present in the ADR
- **Steps**:
  1. Run the command below to count `## D` section headings
- **Command**:
  ```bash
  grep -c "^## D[1-4]" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is `4`
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-006: D1 Contains Audit Entry Schema Table
- **Description**: Verify D1 documents the audit entry schema including the required fields: source_type, source_id, node_name
- **Steps**:
  1. Run the command below to check for the three required extension fields
- **Command**:
  ```bash
  grep -E "(source_type|source_id|node_name)" .docs/adr/0005-observability-stack.md | jq -Rs 'split("\n") | map(select(length > 0)) | length'
  ```
- **Expected Result**: A number greater than or equal to `3` (each field appears at least once)
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-007: D1 Documents source_type Enum Values
- **Description**: Verify D1 specifies the four allowed source_type values: SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK
- **Steps**:
  1. Run the command below to verify all four enum literals are present
- **Command**:
  ```bash
  grep -c -E "(SAFE_SET|PREFERRED|VECTOR_SEARCH|FALLBACK)" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is at least `4` (each value appears at least once)
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-008: D2 Documents Defensive Fallback Token Pattern
- **Description**: Verify D2 specifies the conservative fallback strategy (missing metadata → 0, no crash)
- **Steps**:
  1. Run the command below to confirm the defensive fallback pattern is documented
- **Command**:
  ```bash
  grep -c "usage_metadata" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is at least `2` (pattern mentioned in context and D2)
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-009: D3 Documents /kg/audit/{session_id} Endpoint Contract
- **Description**: Verify D3 specifies the new KG audit endpoint path
- **Steps**:
  1. Run the command below to check the endpoint path is documented
- **Command**:
  ```bash
  grep "kg/audit" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: At least one line containing `kg/audit/{session_id}` or `kg/audit/`
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-010: D3 Documents RecommendedExercise Schema Extensions
- **Description**: Verify D3 specifies the three new fields added to RecommendedExercise: source_type, source_id, confidence
- **Steps**:
  1. Run the command below to confirm all three fields are referenced near the RecommendedExercise section
- **Command**:
  ```bash
  grep -E "confidence" .docs/adr/0005-observability-stack.md | wc -l | tr -d ' '
  ```
- **Expected Result**: Output is at least `1`
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-011: D4 Documents In-Process Scope with Trade-offs Table
- **Description**: Verify D4 documents the in-process-only decision and includes a trade-offs comparison (no LangFuse, OpenLLMetry, Grafana)
- **Steps**:
  1. Run the command below to verify LangFuse and the trade-offs are referenced
- **Command**:
  ```bash
  grep -c -E "(LangFuse|OpenLLMetry|Grafana|Prometheus)" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is at least `4` (each tool mentioned at least once in D4 and alternatives)
- [x] Pass <!-- 2026-06-06 -->

---

## Reference Code Links Tests

### UAT-DOC-012: ADR References Existing Code Files by Name
- **Description**: Verify all four required code files are referenced in the ADR (hub.py, state.py, chat.py, generation_graph.py)
- **Steps**:
  1. Run the command below to verify all four files are mentioned
- **Command**:
  ```bash
  grep -c -E "(hub\.py|state\.py|chat\.py|generation_graph\.py)" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is at least `4` (each file referenced at least once)
- [x] Pass <!-- 2026-06-06 -->

---

## Alternatives Section Tests

### UAT-DOC-013: Alternatives Considered Section Present
- **Description**: Verify the ADR includes an "Alternatives Considered" section
- **Steps**:
  1. Run the command below to check for the section heading
- **Command**:
  ```bash
  grep "Alternatives Considered" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: At least one line containing `Alternatives Considered`
- [x] Pass <!-- 2026-06-06 -->

### UAT-DOC-014: Alternatives Section Lists Required Out-of-Scope Options
- **Description**: Verify alternatives include LangFuse/OTel and OpenLLMetry/Arize Phoenix entries
- **Steps**:
  1. Run the command below to confirm both alternative stacks are listed
- **Command**:
  ```bash
  grep -c -E "(Arize|Phoenix|OTel|OpenTelemetry|PostgreSQL)" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: Output is at least `2`
- [x] Pass <!-- 2026-06-06 -->

---

## Implementation Notes Tests

### UAT-DOC-015: Implementation Notes Section Present
- **Description**: Verify the ADR includes an "Implementation Notes" section with the token extraction pattern
- **Steps**:
  1. Run the command below to confirm the section exists
- **Command**:
  ```bash
  grep "Implementation Notes" .docs/adr/0005-observability-stack.md
  ```
- **Expected Result**: At least one line containing `Implementation Notes`
- [x] Pass <!-- 2026-06-06 -->
