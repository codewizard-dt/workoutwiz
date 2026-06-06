# 055 — Vector Embeddings: Embed Exercises into Neo4j Vector Index

> **Depends on**: [054-graphrag-adr](054-graphrag-adr.md)
> **Blocks**: [059-retrieval-subgraph](059-retrieval-subgraph.md)
> **Parallel-safe with**: [049-injury-ingestion](049-injury-ingestion.md), [050-exercise-neo4j-ingestion](050-exercise-neo4j-ingestion.md), [051-member-profile-ingestion](051-member-profile-ingestion.md), [052-ingest-workout-history-neo4j](052-ingest-workout-history-neo4j.md), [053-feedback-ingestion-neo4j](053-feedback-ingestion-neo4j.md)

## Objective

Implement `backend/app/kg/embeddings.py` with an `embed_exercises()` function that reads all `Exercise` nodes from Neo4j, generates embeddings for the combined `name + description` text of each exercise, upserts the embedding vector as a node property, and creates/refreshes a Neo4j vector index named `exercise_embeddings`. The embedding model (sentence-transformers vs OpenAI) is selected via a config flag, in accordance with ADR-001 (TASK-054).

## Approach

This task implements the vector search foundation for the GraphRAG retrieval layer. All Exercise nodes must already exist in Neo4j (TASK-050). The embeddings module:

1. Reads the `EMBEDDING_PROVIDER` config value (`sentence_transformers` | `openai`) from `backend/app/config.py` — defaulting to whichever the ADR selects.
2. Instantiates the appropriate LangChain embedding class (`HuggingFaceEmbeddings` or `OpenAIEmbeddings`).
3. Uses `langchain-neo4j`'s `Neo4jVector.from_existing_graph()` to populate the vector index — this handles node property reading, embedding generation, property upsert, and index creation in one call.
4. Exposes a `get_exercise_vector_store()` function that returns a ready-to-query `Neo4jVector` instance (used by the retrieval sub-graph in TASK-059).
5. Provides a CLI entry point (`python -m backend.app.kg.embeddings`) for one-shot re-embedding (e.g. after adding new exercises).

The module is idempotent: calling it twice does not duplicate embeddings — `Neo4jVector.from_existing_graph()` with `index_name` already handles this via Neo4j's vector index semantics.

Key design constraint: sentence-transformers runs locally (no API key needed, ~80MB model download on first run). OpenAI requires `OPENAI_API_KEY` in the environment. The config flag makes it easy to switch per the ADR decision without code changes.

## Steps

### 1. Add embedding dependencies to `backend/pyproject.toml`  <!-- agent: general-purpose -->

Read `backend/pyproject.toml`. Under `[project.dependencies]`, add (if not already present):
- `sentence-transformers>=2.7.0` — local embedding model
- `langchain-huggingface>=0.0.3` — LangChain wrapper for HuggingFace/sentence-transformers

`openai` and `langchain-openai` should already be present from TASK-020; verify they are. `langchain-neo4j` should already be present from TASK-042; verify it is.

Use Serena's `replace_content` on `backend/pyproject.toml` to insert the new lines in the correct location within the dependencies block.

- [x] `sentence-transformers>=2.7.0` present in `backend/pyproject.toml`
- [x] `langchain-huggingface>=0.0.3` present in `backend/pyproject.toml`
- [x] `langchain-openai` already present (verify, do not duplicate)
- [x] `langchain-neo4j` already present (verify, do not duplicate)

### 2. Add `EMBEDDING_PROVIDER` config field to `backend/app/config.py`  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/config.py` to see the `Settings` class structure. Add a new field:

```python
EMBEDDING_PROVIDER: str = "sentence_transformers"  # "sentence_transformers" | "openai"
EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"  # overridable for OpenAI: "text-embedding-3-small"
```

These fields are read from environment variables (Pydantic Settings auto-reads `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL_NAME` from env). Add corresponding entries to `.env.example`:

```
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

Use Serena's `insert_after_symbol` or `replace_content` for `config.py`. Use `Edit` for `.env.example`.

- [x] `EMBEDDING_PROVIDER` field added to `Settings` in `backend/app/config.py`
- [x] `EMBEDDING_MODEL_NAME` field added to `Settings` in `backend/app/config.py`
- [x] `.env.example` updated with both new variables

### 3. Create `backend/app/kg/` package if it does not exist  <!-- agent: general-purpose -->

Check with `mcp__serena__list_dir` on `backend/app/` whether a `kg/` subdirectory exists. If not, create `backend/app/kg/__init__.py` as an empty file using the `Write` tool.

- [x] `backend/app/kg/__init__.py` exists (empty or with module docstring)

### 4. Create `backend/app/kg/embeddings.py`  <!-- agent: general-purpose -->

Create the file using the `Write` tool with the following implementation:

```python
"""
Exercise vector embeddings for the GraphRAG retrieval layer.

Embeds Exercise nodes from Neo4j using the configured embedding provider
(sentence-transformers or OpenAI) and stores vectors in a Neo4j vector index.

Usage:
    python -m backend.app.kg.embeddings   # one-shot re-embed all exercises
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_neo4j import Neo4jGraph, Neo4jVector

from backend.app.config import settings

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

INDEX_NAME = "exercise_embeddings"
NODE_LABEL = "Exercise"
# Properties to embed: combined as "name. description" text
TEXT_NODE_PROPERTIES = ["name", "description"]
EMBEDDING_NODE_PROPERTY = "embedding"


def _get_embeddings() -> "Embeddings":
    """Instantiate the configured embedding model."""
    provider = settings.EMBEDDING_PROVIDER
    model_name = settings.EMBEDDING_MODEL_NAME

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        logger.info("Using OpenAI embeddings: %s", model_name)
        return OpenAIEmbeddings(model=model_name)
    elif provider == "sentence_transformers":
        from langchain_huggingface import HuggingFaceEmbeddings
        logger.info("Using HuggingFace/sentence-transformers: %s", model_name)
        return HuggingFaceEmbeddings(model_name=model_name)
    else:
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER: {provider!r}. "
            "Must be 'sentence_transformers' or 'openai'."
        )


def embed_exercises() -> Neo4jVector:
    """
    Embed all Exercise nodes in Neo4j and create/refresh the vector index.

    Reads all Exercise nodes, combines the 'name' and 'description' properties
    into a text representation, generates embeddings, upserts the embedding
    property on each node, and creates (or refreshes) the vector index.

    Returns the Neo4jVector instance for immediate use.
    """
    embeddings = _get_embeddings()

    logger.info(
        "Embedding Exercise nodes into Neo4j vector index '%s'...", INDEX_NAME
    )

    vector_store = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        index_name=INDEX_NAME,
        node_label=NODE_LABEL,
        text_node_properties=TEXT_NODE_PROPERTIES,
        embedding_node_property=EMBEDDING_NODE_PROPERTY,
    )

    logger.info("Exercise embedding complete. Index '%s' is ready.", INDEX_NAME)
    return vector_store


def get_exercise_vector_store() -> Neo4jVector:
    """
    Return a Neo4jVector connected to the existing exercise_embeddings index.

    Use this in the retrieval sub-graph (TASK-059) for similarity search.
    Assumes embed_exercises() has already been run at least once.

    Raises:
        RuntimeError: if the vector index does not exist yet.
    """
    embeddings = _get_embeddings()

    return Neo4jVector.from_existing_index(
        embedding=embeddings,
        url=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        index_name=INDEX_NAME,
        text_node_property=TEXT_NODE_PROPERTIES[0],  # primary display property
    )


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    embed_exercises()
    print("Done.")
```

Verify that `settings.NEO4J_URI`, `settings.NEO4J_USERNAME`, `settings.NEO4J_PASSWORD` exist in `backend/app/config.py` (they should have been added in TASK-041/042). If they use different names, use the correct names.

- [x] `backend/app/kg/embeddings.py` created with `_get_embeddings()`, `embed_exercises()`, `get_exercise_vector_store()`, and `__main__` block
- [x] `_get_embeddings()` dispatches correctly on `EMBEDDING_PROVIDER` setting
- [x] `embed_exercises()` uses `Neo4jVector.from_existing_graph()` with `index_name=INDEX_NAME`
- [x] `get_exercise_vector_store()` uses `Neo4jVector.from_existing_index()` for the retrieval path
- [x] `__main__` block calls `embed_exercises()` so the module can be run directly

### 5. Write unit tests for the embeddings module  <!-- agent: general-purpose -->

Create `backend/tests/kg/test_embeddings.py`. The `kg/` test subdirectory may need an `__init__.py` — check with `mcp__serena__list_dir` on `backend/tests/` and create `backend/tests/kg/__init__.py` if absent.

Tests to write (all using `unittest.mock.patch` to avoid real Neo4j/model calls):

```python
# test_get_embeddings_sentence_transformers
# Patch settings.EMBEDDING_PROVIDER = "sentence_transformers"
# Patch HuggingFaceEmbeddings to a Mock
# Assert _get_embeddings() returns a HuggingFaceEmbeddings instance

# test_get_embeddings_openai
# Patch settings.EMBEDDING_PROVIDER = "openai"
# Patch OpenAIEmbeddings to a Mock
# Assert _get_embeddings() returns an OpenAIEmbeddings instance

# test_get_embeddings_unknown_provider_raises
# Patch settings.EMBEDDING_PROVIDER = "unknown"
# Assert _get_embeddings() raises ValueError

# test_embed_exercises_calls_from_existing_graph
# Patch _get_embeddings() to return a Mock
# Patch Neo4jVector.from_existing_graph to return a Mock
# Call embed_exercises()
# Assert from_existing_graph called with index_name="exercise_embeddings",
#   node_label="Exercise", text_node_properties=["name", "description"]

# test_get_exercise_vector_store_calls_from_existing_index
# Patch _get_embeddings() to return a Mock
# Patch Neo4jVector.from_existing_index to return a Mock
# Call get_exercise_vector_store()
# Assert from_existing_index called with index_name="exercise_embeddings"
```

- [x] `backend/tests/kg/__init__.py` exists
- [x] `backend/tests/kg/test_embeddings.py` created with ≥5 test functions
- [x] All tests pass without a real Neo4j connection (fully mocked)

### 6. Verify imports and run tests  <!-- agent: general-purpose -->

Run:
```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_embeddings.py -v
```

If imports fail due to missing packages (sentence-transformers not installed), install dev dependencies first:
```bash
cd backend && pip install -e ".[dev]"
```

Fix any import errors in `backend/app/kg/embeddings.py` or the test file before marking complete.

- [x] `pytest tests/kg/test_embeddings.py` exits with 0 failures
- [x] No import errors from `backend.app.kg.embeddings`

### 7. Update roadmap  <!-- agent: general-purpose -->

Read `.docs/roadmaps/004-knowledge-graph-coaching-system.md`. Replace the inline placeholder:

```
- [ ] Vector embeddings: embed exercise descriptions/names; store in Neo4j vector index
```

with:

```
- [ ] [TASK-055: Vector embeddings — embed exercises into Neo4j vector index](../tasks/055-vector-embeddings.md)
```

Use the `Edit` tool. Update the `**Last updated**` line to `2026-06-06`.

- [x] Roadmap placeholder replaced with task link

## Acceptance Criteria

- [x] `backend/app/kg/embeddings.py` exists with all three public symbols: `embed_exercises()`, `get_exercise_vector_store()`, `_get_embeddings()`
- [x] `EMBEDDING_PROVIDER` and `EMBEDDING_MODEL_NAME` config fields added to `backend/app/config.py`
- [x] `.env.example` updated with both new env vars
- [x] `sentence-transformers` and `langchain-huggingface` added to `backend/pyproject.toml`
- [x] `backend/tests/kg/test_embeddings.py` exists with ≥5 mocked unit tests, all passing
- [x] Module is idempotent: calling `embed_exercises()` twice does not raise errors
- [x] Roadmap TASK-055 link replaces the inline Phase 4 placeholder

---
**UAT**: [`.docs/uat/055-vector-embeddings.uat.md`](../uat/055-vector-embeddings.uat.md)
