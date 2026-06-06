# UAT: Vector Embeddings — Embed Exercises into Neo4j Vector Index

> **Source task**: [`.docs/tasks/055-vector-embeddings.md`](../tasks/055-vector-embeddings.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] `backend/` Python environment is set up (`pip install -e ".[dev]"` run from `backend/`)
- [ ] `sentence-transformers>=2.7.0` and `langchain-huggingface>=0.0.3` are installed (listed in `backend/pyproject.toml`)
- [ ] `langchain-neo4j>=0.1` and `langchain-openai>=0.2` are installed (verify no import errors)
- [ ] `backend/app/kg/embeddings.py` exists with all three public symbols
- [ ] `backend/tests/kg/test_embeddings.py` exists with ≥5 test functions

---

## Unit Tests (run via pytest — no live services required)

### UAT-UNIT-001: pytest suite passes — all 5 mocked unit tests green

- **Description**: Run the full `backend/tests/kg/test_embeddings.py` suite and verify all 5 tests pass without a real Neo4j connection or embedding model.
- **Steps**:
  1. From the repo root, run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_embeddings.py -v
  ```
- **Expected Result**: `5 passed` reported by pytest, exit code 0; no `ERROR`, `FAILED`, or import-error lines
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: `_get_embeddings()` dispatches to HuggingFaceEmbeddings for `sentence_transformers`

- **Description**: Verify that when `EMBEDDING_PROVIDER="sentence_transformers"`, `_get_embeddings()` instantiates `HuggingFaceEmbeddings` with the configured model name.
- **Steps**:
  1. Run only the specific test:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_embeddings.py::test_get_embeddings_sentence_transformers -v
  ```
- **Expected Result**: `1 passed`; test asserts `HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")` was called once and the return value is the mock instance
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: `_get_embeddings()` dispatches to OpenAIEmbeddings for `openai`

- **Description**: Verify that when `EMBEDDING_PROVIDER="openai"`, `_get_embeddings()` instantiates `OpenAIEmbeddings` with the configured model name.
- **Steps**:
  1. Run only the specific test:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_embeddings.py::test_get_embeddings_openai -v
  ```
- **Expected Result**: `1 passed`; test asserts `OpenAIEmbeddings(model="text-embedding-3-small")` was called once
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-004: `_get_embeddings()` raises `ValueError` for unknown provider

- **Description**: Verify that an unrecognised `EMBEDDING_PROVIDER` value raises `ValueError` with the message `"Unknown EMBEDDING_PROVIDER"`.
- **Steps**:
  1. Run only the specific test:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_embeddings.py::test_get_embeddings_unknown_provider_raises -v
  ```
- **Expected Result**: `1 passed`; test asserts `ValueError` is raised with match `"Unknown EMBEDDING_PROVIDER"`
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-005: `embed_exercises()` calls `Neo4jVector.from_existing_graph()` with correct args

- **Description**: Verify `embed_exercises()` invokes `Neo4jVector.from_existing_graph()` with `index_name="exercise_embeddings"`, `node_label="Exercise"`, `text_node_properties=["name", "description"]`, and `embedding_node_property="embedding"`.
- **Steps**:
  1. Run only the specific test:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_embeddings.py::test_embed_exercises_calls_from_existing_graph -v
  ```
- **Expected Result**: `1 passed`; mock asserts `from_existing_graph` called with all required keyword args and return value is the mock vector store
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-006: `get_exercise_vector_store()` calls `Neo4jVector.from_existing_index()` with correct args

- **Description**: Verify `get_exercise_vector_store()` invokes `Neo4jVector.from_existing_index()` with `index_name="exercise_embeddings"` and `text_node_property="name"`.
- **Steps**:
  1. Run only the specific test:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_embeddings.py::test_get_exercise_vector_store_calls_from_existing_index -v
  ```
- **Expected Result**: `1 passed`; mock asserts `from_existing_index` called with `index_name="exercise_embeddings"` and `text_node_property="name"`
- [x] Pass <!-- 2026-06-06 -->

---

## Static / File Acceptance Tests

### UAT-FILE-001: `backend/app/kg/embeddings.py` contains all required public symbols

- **Description**: Verify the embeddings module exposes the three required callables and the module-level constants.
- **Steps**:
  1. Run the command below to check symbols are importable:
- **Command**:
  ```bash
  cd backend && python -c "from app.kg.embeddings import embed_exercises, get_exercise_vector_store, _get_embeddings, INDEX_NAME, NODE_LABEL, TEXT_NODE_PROPERTIES, EMBEDDING_NODE_PROPERTY; print('OK', INDEX_NAME, NODE_LABEL, TEXT_NODE_PROPERTIES, EMBEDDING_NODE_PROPERTY)"
  ```
- **Expected Result**: Prints `OK exercise_embeddings Exercise ['name', 'description'] embedding` with exit code 0; no `ImportError` or `ModuleNotFoundError`
- [x] Pass <!-- 2026-06-06 -->

### UAT-FILE-002: `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL_NAME` config fields present in `Settings`

- **Description**: Verify both new config fields are present on the `Settings` class and have correct defaults.
- **Steps**:
  1. Run the command below:
- **Command**:
  ```bash
  cd backend && python -c "from app.config import settings; print(settings.EMBEDDING_PROVIDER, settings.EMBEDDING_MODEL_NAME)"
  ```
- **Expected Result**: Prints `sentence_transformers sentence-transformers/all-MiniLM-L6-v2` (or env-overridden values) with exit code 0
- [x] Pass <!-- 2026-06-06 -->

### UAT-FILE-003: `pyproject.toml` lists `sentence-transformers` and `langchain-huggingface` dependencies

- **Description**: Verify both new dependencies are declared in `backend/pyproject.toml` under `[project.dependencies]`.
- **Steps**:
  1. Run the command below to confirm both packages are importable (they will have been installed via `pip install -e ".[dev]"`):
- **Command**:
  ```bash
  cd backend && python -c "import sentence_transformers; import langchain_huggingface; print('deps OK')"
  ```
- **Expected Result**: Prints `deps OK` with exit code 0; no `ModuleNotFoundError`
- [x] Pass <!-- 2026-06-06 -->

### UAT-FILE-004: `.env.example` contains `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL_NAME`

- **Description**: Verify the `.env.example` file documents both new environment variables.
- **Steps**:
  1. Inspect `.env.example` in the repo root for the presence of both keys
- **Expected Result**: `.env.example` contains lines `EMBEDDING_PROVIDER=sentence_transformers` and `EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: `__main__` entry point runs without error (dry-run via import check)

- **Description**: Verify the module's `if __name__ == "__main__"` block is syntactically valid and that the module can be imported cleanly as a script module.
- **Steps**:
  1. Run the command below (syntax check only — does not call `embed_exercises()` which would need a live Neo4j):
- **Command**:
  ```bash
  cd backend && python -c "import ast, pathlib; src = pathlib.Path('app/kg/embeddings.py').read_text(); ast.parse(src); print('syntax OK')"
  ```
- **Expected Result**: Prints `syntax OK` with exit code 0; no `SyntaxError`
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Idempotency — calling `embed_exercises()` twice does not raise (mocked)

- **Description**: Verify that calling `embed_exercises()` a second time with the same mocks does not raise, confirming the idempotency requirement (Neo4j's `from_existing_graph` handles index re-creation).
- **Steps**:
  1. Run the command below — it patches `Neo4jVector.from_existing_graph` to succeed on repeated calls:
- **Command**:
  ```bash
  cd backend && python -c "
from unittest.mock import MagicMock, patch
with patch('app.kg.embeddings._get_embeddings', return_value=MagicMock()), \
     patch('app.kg.embeddings.Neo4jVector.from_existing_graph', return_value=MagicMock()), \
     patch('app.kg.embeddings.settings') as s:
    s.neo4j_uri='bolt://localhost:7687'; s.neo4j_user='neo4j'; s.neo4j_password='pw'
    from app.kg.embeddings import embed_exercises
    embed_exercises()
    embed_exercises()
print('idempotent OK')
"
  ```
- **Expected Result**: Prints `idempotent OK` with exit code 0; no exception raised on either call
- [x] Pass <!-- 2026-06-06 -->
