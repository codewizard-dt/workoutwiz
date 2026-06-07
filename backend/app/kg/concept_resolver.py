"""
Runtime 3-pass concept resolver.

Maps coach free text (e.g. "knee", "kettlebell", "bad lower back") onto
canonical knowledge-graph nodes using three ordered passes:

  Pass 1 — exact Cypher match (confidence = 1.0)
  Pass 2 — rapidfuzz token_sort_ratio on candidate names (threshold FUZZY_THRESHOLD)
  Pass 3 — in-process cosine similarity over canonical-name embeddings (threshold EMBEDDING_THRESHOLD)

The resolver short-circuits on the first pass that exceeds its threshold.
It never raises on a no-match or infrastructure error — it always returns a
``ResolutionResult`` with ``method="none"`` and the best observed confidence.

Thresholds are module-level constants and are intentionally tunable.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

import neo4j

from app.config import settings
from app.kg.embeddings import _get_embeddings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunable thresholds — adjust without touching call-sites
# ---------------------------------------------------------------------------
FUZZY_THRESHOLD: float = 0.82
EMBEDDING_THRESHOLD: float = 0.75

# ---------------------------------------------------------------------------
# Node-label to name-properties mapping
#
# Keys are Neo4j node labels.  Values are the ordered list of string
# properties to match / compare against for that label.
# ---------------------------------------------------------------------------
_LABEL_PROPS: dict[str, list[str]] = {
    "BodyStructure": ["snomed_name", "catalog_term"],
    "Disorder": ["snomed_name", "label"],
    "Muscle": ["name"],
    "Equipment": ["name"],
    "MovementPattern": ["name"],
}

# concept_type → label(s) shortcut
_CONCEPT_TYPE_TO_LABELS: dict[str, list[str]] = {
    "joint": ["BodyStructure"],
    "body_structure": ["BodyStructure"],
    "disorder": ["Disorder"],
    "injury": ["Disorder"],
    "muscle": ["Muscle"],
    "equipment": ["Equipment"],
    "movement_pattern": ["MovementPattern"],
}


# ---------------------------------------------------------------------------
# Result schema
# ---------------------------------------------------------------------------


@dataclass
class ResolutionResult:
    """Result returned by :func:`resolve_concept` for every call."""

    matched_node: dict[str, object] | None = field(default=None)
    """Key properties of the resolved node, or ``None`` on no-match."""

    canonical_name: str | None = field(default=None)
    """The primary human-readable name of the resolved node, or ``None``."""

    confidence: float = field(default=0.0)
    """Confidence score in the range [0.0, 1.0]."""

    method: Literal["exact", "fuzzy", "embedding", "none"] = field(default="none")
    """Which pass produced the match, or ``"none"`` when nothing cleared threshold."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Lowercase, strip, and collapse internal whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _resolve_labels(concept_type: str | None) -> list[str]:
    """Return the list of Neo4j labels to search, narrowed by concept_type."""
    if concept_type is None:
        return list(_LABEL_PROPS.keys())
    return _CONCEPT_TYPE_TO_LABELS.get(concept_type, list(_LABEL_PROPS.keys()))


def _pick_canonical(record: dict[str, object]) -> str | None:
    """Extract the best human-readable name from a Cypher result record."""
    for key in ("snomed_name", "catalog_term", "label", "name"):
        val = record.get(key)
        if val:
            return str(val)
    return None


# ---------------------------------------------------------------------------
# Pass 1 — exact match
# ---------------------------------------------------------------------------


async def _exact_match(
    text: str,
    concept_type: str | None,
    driver: neo4j.AsyncDriver,
) -> ResolutionResult | None:
    """
    Cypher exact match: normalised input vs. normalised canonical property values.

    Returns a :class:`ResolutionResult` with ``method="exact"`` and
    ``confidence=1.0`` on hit; ``None`` when no row matches so the
    orchestrator advances to Pass 2.
    """
    norm = _normalize(text)
    labels = _resolve_labels(concept_type)

    # Build per-label UNION fragments dynamically so we search whichever
    # labels actually have nodes (graceful degradation: empty labels return 0 rows)
    union_parts: list[str] = []
    for label in labels:
        props = _LABEL_PROPS.get(label, ["name"])
        conditions = " OR ".join(
            f"toLower(trim(n.{p})) = $norm" for p in props
        )
        # Collect all relevant properties in the RETURN so _pick_canonical works
        return_props = ", ".join(f"n.{p} AS {p}" for p in props)
        extra = ""
        if label not in ("Muscle", "Equipment", "MovementPattern"):
            # SNOMED nodes carry snomed_code
            extra = ", n.snomed_code AS snomed_code"
        union_parts.append(
            f"MATCH (n:{label}) WHERE {conditions} "
            f"RETURN '{label}' AS _label, {return_props}{extra} LIMIT 1"
        )

    query = " UNION ALL ".join(union_parts) + " LIMIT 1"

    async with driver.session(database="neo4j") as session:
        result = await session.run(query, norm=norm)
        records = await result.data()

    if not records:
        return None

    row = records[0]
    canonical = _pick_canonical(row)
    return ResolutionResult(
        matched_node=dict(row),
        canonical_name=canonical,
        confidence=1.0,
        method="exact",
    )


# ---------------------------------------------------------------------------
# Pass 2 — fuzzy match
# ---------------------------------------------------------------------------


async def _fuzzy_match(
    text: str,
    concept_type: str | None,
    driver: neo4j.AsyncDriver,
) -> tuple[ResolutionResult | None, float]:
    """
    Fetch candidate node names from the graph, then score with rapidfuzz.

    Returns ``(ResolutionResult, best_confidence)`` where the result is
    non-None only when ``confidence >= FUZZY_THRESHOLD``.
    """
    from rapidfuzz import fuzz
    from rapidfuzz import process as fuzz_process

    labels = _resolve_labels(concept_type)

    # Fetch all candidate names for in-scope labels
    union_parts: list[str] = []
    for label in labels:
        props = _LABEL_PROPS.get(label, ["name"])
        return_props = ", ".join(f"n.{p} AS {p}" for p in props)
        extra = ""
        if label not in ("Muscle", "Equipment", "MovementPattern"):
            extra = ", n.snomed_code AS snomed_code"
        union_parts.append(
            f"MATCH (n:{label}) RETURN '{label}' AS _label, {return_props}{extra}"
        )

    query = " UNION ALL ".join(union_parts)

    async with driver.session(database="neo4j") as session:
        result = await session.run(query)
        records = await result.data()

    if not records:
        return None, 0.0

    # Build a flat list of (display_name, record) pairs — one entry per
    # non-null text property so the fuzzy scorer has the richest candidate set
    candidates: list[tuple[str, dict[str, object]]] = []
    for row in records:
        label = row.get("_label", "")
        props = _LABEL_PROPS.get(label, ["name"])
        for p in props:
            val = row.get(p)
            if val:
                candidates.append((str(val), row))

    if not candidates:
        return None, 0.0

    candidate_names = [c[0] for c in candidates]
    match_result = fuzz_process.extractOne(
        text, candidate_names, scorer=fuzz.token_sort_ratio
    )
    if match_result is None:
        return None, 0.0

    matched_name, score, idx = match_result
    confidence = score / 100.0
    best_row = candidates[idx][1]
    canonical = _pick_canonical(best_row)

    if confidence < FUZZY_THRESHOLD:
        return None, confidence

    return (
        ResolutionResult(
            matched_node=dict(best_row),
            canonical_name=canonical or matched_name,
            confidence=confidence,
            method="fuzzy",
        ),
        confidence,
    )


# ---------------------------------------------------------------------------
# Pass 3 — embedding fallback
# ---------------------------------------------------------------------------


async def _embedding_match(
    text: str,
    concept_type: str | None,
    driver: neo4j.AsyncDriver,
) -> tuple[ResolutionResult | None, float]:
    """
    In-process cosine similarity over canonical-name embeddings.

    Fetches candidate canonical names from the graph, encodes them with the
    configured embedding model (same ``_get_embeddings()`` used by
    ``embed_exercises``), and picks the closest match by cosine similarity.

    Runs the synchronous embedding calls inside a thread pool via
    ``asyncio.to_thread`` (matching the pattern in
    ``backend/app/kg/context_assembler.py``).

    Returns ``(ResolutionResult, best_confidence)`` where the result is
    non-None only when ``confidence >= EMBEDDING_THRESHOLD``.
    """
    import numpy as np

    labels = _resolve_labels(concept_type)

    # Fetch all canonical names + their rows from the graph
    union_parts: list[str] = []
    for label in labels:
        props = _LABEL_PROPS.get(label, ["name"])
        return_props = ", ".join(f"n.{p} AS {p}" for p in props)
        extra = ""
        if label not in ("Muscle", "Equipment", "MovementPattern"):
            extra = ", n.snomed_code AS snomed_code"
        union_parts.append(
            f"MATCH (n:{label}) RETURN '{label}' AS _label, {return_props}{extra}"
        )

    query = " UNION ALL ".join(union_parts)

    async with driver.session(database="neo4j") as session:
        result = await session.run(query)
        records = await result.data()

    if not records:
        return None, 0.0

    candidates: list[tuple[str, dict[str, object]]] = []
    for row in records:
        label = row.get("_label", "")
        props = _LABEL_PROPS.get(label, ["name"])
        for p in props:
            val = row.get(p)
            if val:
                candidates.append((str(val), row))
                break  # one representative name per node is enough for embedding

    if not candidates:
        return None, 0.0

    candidate_names = [c[0] for c in candidates]

    # Encode everything in a thread (synchronous LangChain embeddings API)
    embeddings_model = _get_embeddings()

    def _encode_all() -> tuple[list[float], list[list[float]]]:
        query_vec = embeddings_model.embed_query(text)
        doc_vecs = embeddings_model.embed_documents(candidate_names)
        return query_vec, doc_vecs

    query_vec, doc_vecs = await asyncio.to_thread(_encode_all)

    q = np.array(query_vec, dtype=np.float32)
    D = np.array(doc_vecs, dtype=np.float32)

    # Cosine similarity: dot(q, D.T) / (||q|| * ||D||)
    q_norm = np.linalg.norm(q)
    d_norms = np.linalg.norm(D, axis=1)

    if q_norm == 0 or np.any(d_norms == 0):
        return None, 0.0

    sims = D.dot(q) / (d_norms * q_norm)
    best_idx = int(np.argmax(sims))
    confidence = float(np.clip(sims[best_idx], 0.0, 1.0))

    if confidence < EMBEDDING_THRESHOLD:
        return None, confidence

    best_row = candidates[best_idx][1]
    canonical = _pick_canonical(best_row)

    return (
        ResolutionResult(
            matched_node=dict(best_row),
            canonical_name=canonical or candidate_names[best_idx],
            confidence=confidence,
            method="embedding",
        ),
        confidence,
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def resolve_concept(
    text: str,
    concept_type: str | None = None,
) -> ResolutionResult:
    """
    Map free text onto a canonical knowledge-graph node using 3 ordered passes.

    Passes run in order (exact → fuzzy → embedding) and short-circuit on the
    first hit above its threshold.  When all passes miss, returns a
    ``ResolutionResult`` with ``method="none"`` and the best observed
    confidence.  **Never raises** on a no-match or infrastructure error.

    Args:
        text:  Free-text input from the coach (e.g. ``"knee"``, ``"kettlebell"``).
        concept_type:  Optional narrowing hint — one of ``"joint"``,
            ``"body_structure"``, ``"disorder"``, ``"injury"``,
            ``"muscle"``, ``"equipment"``, ``"movement_pattern"``.
            Pass ``None`` to search all labels.

    Returns:
        A :class:`ResolutionResult` instance.
    """
    # Guard empty / whitespace-only input immediately
    if not text or not text.strip():
        logger.debug("resolve_concept called with empty text — returning none")
        return ResolutionResult(method="none")

    best_confidence: float = 0.0

    try:
        driver = neo4j.AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    except Exception as exc:
        logger.warning("resolve_concept: failed to create driver for %r: %s", text, exc)
        return ResolutionResult(method="none")

    try:
        # ------------------------------------------------------------------
        # Pass 1 — exact
        # ------------------------------------------------------------------
        try:
            exact_result = await _exact_match(text, concept_type, driver)
            if exact_result is not None:
                logger.debug(
                    "resolve_concept: exact hit for %r → %r",
                    text,
                    exact_result.canonical_name,
                )
                return exact_result
        except Exception as exc:
            logger.warning("resolve_concept: exact pass failed for %r: %s", text, exc)

        # ------------------------------------------------------------------
        # Pass 2 — fuzzy
        # ------------------------------------------------------------------
        try:
            fuzzy_result, fuzzy_conf = await _fuzzy_match(text, concept_type, driver)
            best_confidence = max(best_confidence, fuzzy_conf)
            if fuzzy_result is not None:
                logger.debug(
                    "resolve_concept: fuzzy hit for %r → %r (%.2f)",
                    text,
                    fuzzy_result.canonical_name,
                    fuzzy_conf,
                )
                return fuzzy_result
        except Exception as exc:
            logger.warning("resolve_concept: fuzzy pass failed for %r: %s", text, exc)

        # ------------------------------------------------------------------
        # Pass 3 — embedding
        # ------------------------------------------------------------------
        try:
            emb_result, emb_conf = await _embedding_match(
                text, concept_type, driver
            )
            best_confidence = max(best_confidence, emb_conf)
            if emb_result is not None:
                logger.debug(
                    "resolve_concept: embedding hit for %r → %r (%.2f)",
                    text,
                    emb_result.canonical_name,
                    emb_conf,
                )
                return emb_result
        except Exception as exc:
            logger.warning(
                "resolve_concept: embedding pass failed for %r: %s", text, exc
            )

    finally:
        await driver.close()

    logger.debug(
        "resolve_concept: no match for %r (best_confidence=%.2f)", text, best_confidence
    )
    return ResolutionResult(
        matched_node=None,
        canonical_name=None,
        confidence=best_confidence,
        method="none",
    )
