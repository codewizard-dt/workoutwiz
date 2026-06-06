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

from langchain_neo4j import Neo4jVector

from app.config import settings

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

INDEX_NAME = "exercise_embeddings"
NODE_LABEL = "Exercise"
# Properties to embed: combined as "name. description" text
TEXT_NODE_PROPERTIES = ["name", "description"]
EMBEDDING_NODE_PROPERTY = "embedding"


def _get_embeddings() -> Embeddings:
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
        url=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
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
        url=settings.neo4j_uri,
        username=settings.neo4j_user,
        password=settings.neo4j_password,
        index_name=INDEX_NAME,
        text_node_property=TEXT_NODE_PROPERTIES[0],  # primary display property
    )


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    embed_exercises()
    print("Done.")
