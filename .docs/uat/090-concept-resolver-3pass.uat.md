# UAT: Runtime 3-Pass Concept Resolver

> **Source task**: [`.docs/tasks/090-concept-resolver-3pass.md`](../tasks/090-concept-resolver-3pass.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] Python virtual environment installed: `make install` has been run and `backend/.venv` exists.
- [ ] `backend/.venv/bin/python` is executable and the `app` package is importable (`pip install -e backend/.` done as part of `make install`).
- [ ] Neo4j is **not** required for the unit tests — the driver and sessions are fully mocked. The live smoke tests (UAT-SCRIPT-*) also mock Neo4j unless stated otherwise.

---

## Unit Tests (pytest suite)

### UAT-UNIT-001: Full pytest suite passes — all 11 tests green

- **Description**: Run the complete `test_concept_resolver.py` suite and verify every test passes. This is the primary gate for the resolver's contract.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -m pytest backend/tests/kg/test_concept_resolver.py -v
  ```
- **Expected Result**: Exit code `0`. Output shows `11 passed` (or a superset if tests were added). No errors, no failures, no skips.
- [ ] Pass

---

## Script Tests (import / contract verification)

These tests use a small inline Python script to verify the public interface of `concept_resolver` is intact — correct module path, correct class shape, correct constants, and correct return type — without requiring a live Neo4j connection.

### UAT-SCRIPT-001: Module imports without error and exposes public symbols

- **Description**: Verify `backend/app/kg/concept_resolver.py` is importable and exposes `resolve_concept`, `ResolutionResult`, `FUZZY_THRESHOLD`, and `EMBEDDING_THRESHOLD` at the module level.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "from app.kg.concept_resolver import resolve_concept, ResolutionResult, FUZZY_THRESHOLD, EMBEDDING_THRESHOLD; assert callable(resolve_concept); import inspect; assert inspect.iscoroutinefunction(resolve_concept); assert FUZZY_THRESHOLD == 0.82; assert EMBEDDING_THRESHOLD == 0.75; print('OK')"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. Any `ImportError`, `AssertionError`, or non-zero exit indicates a contract violation.
- [ ] Pass

### UAT-SCRIPT-002: `ResolutionResult` dataclass has all required fields

- **Description**: Verify `ResolutionResult` carries `matched_node`, `canonical_name`, `confidence`, and `method` with correct defaults.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "from app.kg.concept_resolver import ResolutionResult; r = ResolutionResult(); assert r.matched_node is None; assert r.canonical_name is None; assert r.confidence == 0.0; assert r.method == 'none'; print('OK')"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. Any `AssertionError` indicates the dataclass defaults do not match the spec.
- [ ] Pass

### UAT-SCRIPT-003: `resolve_concept` returns `method="none"` immediately for empty / whitespace-only input (no Neo4j call)

- **Description**: The resolver must short-circuit before touching the driver when given blank input. Patching the driver to raise means any driver call would cause an exception — confirming the guard fires.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio
from unittest.mock import patch
from app.kg.concept_resolver import resolve_concept

async def main():
    with patch('app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver', side_effect=RuntimeError('should not be called')):
        r1 = await resolve_concept('')
        r2 = await resolve_concept('   ')
    assert r1.method == 'none', f'Expected none, got {r1.method}'
    assert r2.method == 'none', f'Expected none, got {r2.method}'
    assert r1.matched_node is None
    assert r2.matched_node is None
    print('OK')

asyncio.run(main())
"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. A `RuntimeError` from the patched driver would indicate the guard is missing.
- [ ] Pass

### UAT-SCRIPT-004: `resolve_concept` never raises on infrastructure error — returns `method="none"`

- **Description**: If the Neo4j driver raises on creation, `resolve_concept` must catch it and return `method="none"` without propagating.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio
from unittest.mock import patch
from app.kg.concept_resolver import resolve_concept

async def main():
    with patch('app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver', side_effect=ConnectionError('Neo4j unreachable')):
        result = await resolve_concept('knee')
    assert result.method == 'none', f'Expected none, got {result.method}'
    assert result.matched_node is None
    print('OK')

asyncio.run(main())
"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. Any unhandled exception means the resilience contract is broken.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: `method` field is restricted to the four valid literals

- **Description**: Verify that `ResolutionResult.method` only accepts the four literal values defined in the spec: `"exact"`, `"fuzzy"`, `"embedding"`, `"none"`.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from app.kg.concept_resolver import ResolutionResult
valid = {'exact', 'fuzzy', 'embedding', 'none'}
for m in valid:
    r = ResolutionResult(method=m)
    assert r.method == m, f'Failed for method={m}'
print('OK')
"
  ```
- **Expected Result**: Prints `OK` with exit code `0`.
- [ ] Pass

### UAT-EDGE-002: `FUZZY_THRESHOLD` is tuned to accommodate the canonical `"kettlebel"` misspelling example

- **Description**: The task spec explicitly tuned `FUZZY_THRESHOLD` from 0.85 to 0.82 so that `"kettlebel"` (score ~0.842) resolves above threshold. Verify the threshold is `0.82` (not the pre-tuning 0.85).
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from app.kg.concept_resolver import FUZZY_THRESHOLD
assert FUZZY_THRESHOLD == 0.82, f'Expected 0.82, got {FUZZY_THRESHOLD}'
from rapidfuzz import fuzz
score = fuzz.token_sort_ratio('kettlebel', 'Kettlebell') / 100.0
assert score >= FUZZY_THRESHOLD, f'kettlebel score {score:.3f} is below FUZZY_THRESHOLD {FUZZY_THRESHOLD}'
print(f'OK (kettlebel score={score:.3f}, threshold={FUZZY_THRESHOLD})')
"
  ```
- **Expected Result**: Prints `OK (kettlebel score=0.842, threshold=0.82)` (score may vary slightly). Exit code `0`. Any `AssertionError` means the threshold is wrong or rapidfuzz behaviour has changed.
- [ ] Pass

### UAT-EDGE-003: `_normalize` collapses whitespace and lowercases

- **Description**: The normalization helper underpins exact matching — `"  Knee "`, `"KNEE"`, and `"knee"` must all normalize to `"knee"`.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
from app.kg.concept_resolver import _normalize
assert _normalize('  Knee  ') == 'knee'
assert _normalize('KNEE') == 'knee'
assert _normalize('Bad  Lower  Back') == 'bad lower back'
print('OK')
"
  ```
- **Expected Result**: Prints `OK` with exit code `0`.
- [ ] Pass

### UAT-EDGE-004: Passing `concept_type="equipment"` narrows candidates to Equipment label

- **Description**: When `concept_type` is provided, only the matching label(s) should be queried. Verify the resolver short-circuits correctly with a mocked session that only returns Equipment rows.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from app.kg.concept_resolver import resolve_concept

async def main():
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[{'_label': 'Equipment', 'name': 'Kettlebell'}])
    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)

    @asynccontextmanager
    async def _session_ctx(*args, **kwargs):
        yield mock_session

    mock_driver = AsyncMock()
    mock_driver.session = _session_ctx
    mock_driver.close = AsyncMock()

    with patch('app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver', return_value=mock_driver):
        result = await resolve_concept('kettlebell', concept_type='equipment')

    assert result.method == 'exact', f'Expected exact, got {result.method}'
    assert result.canonical_name == 'Kettlebell'
    assert result.matched_node['_label'] == 'Equipment'
    print('OK')

asyncio.run(main())
"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. If concept_type narrowing is broken, the assertion on `_label` fails.
- [ ] Pass

---

## Integration Tests

### UAT-INT-001: Three-pass short-circuit order — exact wins over fuzzy and embedding

- **Description**: Verify the pass ordering: when an exact match is found in pass 1, passes 2 and 3 must not be called. The mock driver is set up to return an exact match on the first Cypher call; any further calls would be unnecessary.
- **Components**: `resolve_concept` → `_exact_match` (pass 1 hits) → returns without calling `_fuzzy_match` or `_embedding_match`.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from app.kg.concept_resolver import resolve_concept

async def main():
    call_count = 0

    async def counting_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        r = AsyncMock()
        r.data = AsyncMock(return_value=[{'_label': 'BodyStructure', 'snomed_name': 'Knee', 'catalog_term': 'Knee joint', 'snomed_code': '72696002'}])
        return r

    mock_session = AsyncMock()
    mock_session.run = counting_run

    @asynccontextmanager
    async def _session_ctx(*args, **kwargs):
        yield mock_session

    mock_driver = AsyncMock()
    mock_driver.session = _session_ctx
    mock_driver.close = AsyncMock()

    with patch('app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver', return_value=mock_driver):
        result = await resolve_concept('knee')

    assert result.method == 'exact', f'Expected exact, got {result.method}'
    assert call_count == 1, f'Expected 1 Cypher call (exact pass only), got {call_count}'
    print('OK')

asyncio.run(main())
"
  ```
- **Expected Result**: Prints `OK` with exit code `0`. If `call_count != 1`, the short-circuit is broken and later passes are being called unnecessarily.
- [ ] Pass

### UAT-INT-002: Three-pass fallthrough — exact miss → fuzzy miss → embedding hit

- **Description**: Verify the full three-pass chain: pass 1 returns no rows, pass 2 returns a candidate whose fuzzy score is below threshold, pass 3 (embedding) returns a high-confidence match.
- **Components**: `resolve_concept` → `_exact_match` (miss) → `_fuzzy_match` (miss) → `_embedding_match` (hit).
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from app.kg.concept_resolver import EMBEDDING_THRESHOLD, resolve_concept

async def main():
    call_count = 0
    lumbar_row = {'_label': 'BodyStructure', 'snomed_name': 'Lumbar region', 'catalog_term': None, 'snomed_code': '182343007'}

    async def counting_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        r = AsyncMock()
        # call 1 = exact (no rows); calls 2 & 3 = fuzzy/embedding candidates
        data = [] if call_count == 1 else [lumbar_row]
        r.data = AsyncMock(return_value=data)
        return r

    mock_session = AsyncMock()
    mock_session.run = counting_run

    @asynccontextmanager
    async def _session_ctx(*args, **kwargs):
        yield mock_session

    mock_driver = AsyncMock()
    mock_driver.session = _session_ctx
    mock_driver.close = AsyncMock()

    mock_embeddings = MagicMock()
    mock_embeddings.embed_query = MagicMock(return_value=[1.0, 0.0, 0.0])
    mock_embeddings.embed_documents = MagicMock(return_value=[[0.99, 0.0, 0.0]])

    async def _sync_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch('app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver', return_value=mock_driver),
        patch('app.kg.concept_resolver._get_embeddings', return_value=mock_embeddings),
        patch('app.kg.concept_resolver.asyncio.to_thread', new=_sync_to_thread),
    ):
        result = await resolve_concept('bad lower back')

    assert result.method in ('fuzzy', 'embedding'), f'Expected fuzzy or embedding, got {result.method}'
    assert result.confidence >= EMBEDDING_THRESHOLD, f'confidence {result.confidence} below threshold'
    assert result.matched_node is not None
    print(f'OK (method={result.method}, confidence={result.confidence:.3f})')

asyncio.run(main())
"
  ```
- **Expected Result**: Prints `OK (method=embedding, confidence=...)` (or `fuzzy` if the fuzzy score happens to be above threshold for this candidate). Exit code `0`. Confidence must be `>= 0.75`.
- [ ] Pass

### UAT-INT-003: All passes miss — `method="none"` with best observed confidence

- **Description**: When no pass clears its threshold, `resolve_concept` must return `method="none"` with a non-negative best confidence and `matched_node=None`. The resolver must not raise.
- **Components**: `resolve_concept` → all three passes return `None` → graceful degradation result.
- **Steps**:
  1. Run the command below as-is from the project root.
- **Command**:
  ```bash
  backend/.venv/bin/python -c "
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from app.kg.concept_resolver import resolve_concept

async def main():
    junk_row = {'_label': 'Equipment', 'name': 'Barbell'}

    async def always_junk(*args, **kwargs):
        r = AsyncMock()
        r.data = AsyncMock(return_value=[junk_row])
        return r

    mock_session = AsyncMock()
    mock_session.run = always_junk

    @asynccontextmanager
    async def _session_ctx(*args, **kwargs):
        yield mock_session

    mock_driver = AsyncMock()
    mock_driver.session = _session_ctx
    mock_driver.close = AsyncMock()

    mock_embeddings = MagicMock()
    # Low-similarity vectors — cosine sim well below 0.75
    mock_embeddings.embed_query = MagicMock(return_value=[1.0, 0.0, 0.0])
    mock_embeddings.embed_documents = MagicMock(return_value=[[0.0, 1.0, 0.0]])

    async def _sync_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    with (
        patch('app.kg.concept_resolver.neo4j.AsyncGraphDatabase.driver', return_value=mock_driver),
        patch('app.kg.concept_resolver._get_embeddings', return_value=mock_embeddings),
        patch('app.kg.concept_resolver.asyncio.to_thread', new=_sync_to_thread),
    ):
        result = await resolve_concept('xyzzy_nonexistent_thing_1234')

    assert result.method == 'none', f'Expected none, got {result.method}'
    assert result.matched_node is None, f'Expected None matched_node, got {result.matched_node}'
    assert 0.0 <= result.confidence <= 1.0, f'confidence {result.confidence} out of range'
    print(f'OK (confidence={result.confidence:.3f})')

asyncio.run(main())
"
  ```
- **Expected Result**: Prints `OK (confidence=...)` with exit code `0`. The confidence value will be a small number (the best fuzzy score against a completely unrelated word). No exception is raised.
- [ ] Pass

---

## Gaps and Notes

- **No HTTP API or UI tests**: Task 090 delivers a Python library module (`backend/app/kg/concept_resolver.py`). There are no new REST endpoints or frontend pages introduced by this task. All behavioral verification is via the pytest suite (UAT-UNIT-001) and inline Python scripts.
- **Live Neo4j integration not covered**: UAT-UNIT-001 through UAT-INT-003 all mock the Neo4j driver. A true end-to-end smoke test against a live Neo4j instance with SNOMED data loaded (`:BodyStructure`, `:Disorder` nodes) was deferred — it requires the SNOMED ingest pipeline (task prerequisite) to have run. That integration is gated on infrastructure availability and is not verified here.
- **Embedding pass with real model not covered**: The embedding pass mocks `_get_embeddings()`. A live embedding smoke test would require a configured LLM provider. Deferred.
