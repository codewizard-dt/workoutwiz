"""
Unit tests for app.kg.embeddings.

All tests fully mock Neo4j and embedding model calls — no real connections required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# _get_embeddings() tests
# ---------------------------------------------------------------------------


def test_get_embeddings_sentence_transformers() -> None:
    """_get_embeddings() returns a HuggingFaceEmbeddings instance when provider is sentence_transformers."""
    mock_hf_instance = MagicMock()
    mock_hf_class = MagicMock(return_value=mock_hf_instance)
    mock_hf_module = MagicMock(HuggingFaceEmbeddings=mock_hf_class)

    with (
        patch("app.kg.embeddings.settings") as mock_settings,
        patch.dict("sys.modules", {"langchain_huggingface": mock_hf_module}),
    ):
        mock_settings.EMBEDDING_PROVIDER = "sentence_transformers"
        mock_settings.EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

        from app.kg.embeddings import _get_embeddings

        result = _get_embeddings()

    mock_hf_class.assert_called_once_with(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    assert result is mock_hf_instance


def test_get_embeddings_openai() -> None:
    """_get_embeddings() returns an OpenAIEmbeddings instance when provider is openai."""
    mock_openai_instance = MagicMock()
    mock_openai_class = MagicMock(return_value=mock_openai_instance)
    mock_openai_module = MagicMock(OpenAIEmbeddings=mock_openai_class)

    with (
        patch("app.kg.embeddings.settings") as mock_settings,
        patch.dict("sys.modules", {"langchain_openai": mock_openai_module}),
    ):
        mock_settings.EMBEDDING_PROVIDER = "openai"
        mock_settings.EMBEDDING_MODEL_NAME = "text-embedding-3-small"

        from app.kg.embeddings import _get_embeddings

        result = _get_embeddings()

    mock_openai_class.assert_called_once_with(model="text-embedding-3-small")
    assert result is mock_openai_instance


def test_get_embeddings_unknown_provider_raises() -> None:
    """_get_embeddings() raises ValueError for an unrecognised provider."""
    with patch("app.kg.embeddings.settings") as mock_settings:
        mock_settings.EMBEDDING_PROVIDER = "unknown_provider"
        mock_settings.EMBEDDING_MODEL_NAME = "some-model"

        from app.kg.embeddings import _get_embeddings

        with pytest.raises(ValueError, match="Unknown EMBEDDING_PROVIDER"):
            _get_embeddings()


# ---------------------------------------------------------------------------
# embed_exercises() tests
# ---------------------------------------------------------------------------


def test_embed_exercises_calls_from_existing_graph() -> None:
    """embed_exercises() delegates to Neo4jVector.from_existing_graph() with correct args."""
    mock_embeddings = MagicMock()
    mock_vector_store = MagicMock()

    with (
        patch(
            "app.kg.embeddings._get_embeddings",
            return_value=mock_embeddings,
        ),
        patch(
            "app.kg.embeddings.Neo4jVector.from_existing_graph",
            return_value=mock_vector_store,
        ) as mock_feg,
        patch("app.kg.embeddings.settings") as mock_settings,
    ):
        mock_settings.neo4j_uri = "bolt://localhost:7687"
        mock_settings.neo4j_user = "neo4j"
        mock_settings.neo4j_password = "password"

        from app.kg.embeddings import embed_exercises

        result = embed_exercises()

    mock_feg.assert_called_once_with(
        embedding=mock_embeddings,
        url="bolt://localhost:7687",
        username="neo4j",
        password="password",
        index_name="exercise_embeddings",
        node_label="Exercise",
        text_node_properties=["name", "description"],
        embedding_node_property="embedding",
    )
    assert result is mock_vector_store


# ---------------------------------------------------------------------------
# get_exercise_vector_store() tests
# ---------------------------------------------------------------------------


def test_get_exercise_vector_store_calls_from_existing_index() -> None:
    """get_exercise_vector_store() delegates to Neo4jVector.from_existing_index() with correct args."""
    mock_embeddings = MagicMock()
    mock_vector_store = MagicMock()

    with (
        patch(
            "app.kg.embeddings._get_embeddings",
            return_value=mock_embeddings,
        ),
        patch(
            "app.kg.embeddings.Neo4jVector.from_existing_index",
            return_value=mock_vector_store,
        ) as mock_fei,
        patch("app.kg.embeddings.settings") as mock_settings,
    ):
        mock_settings.neo4j_uri = "bolt://localhost:7687"
        mock_settings.neo4j_user = "neo4j"
        mock_settings.neo4j_password = "password"

        from app.kg.embeddings import get_exercise_vector_store

        result = get_exercise_vector_store()

    mock_fei.assert_called_once_with(
        embedding=mock_embeddings,
        url="bolt://localhost:7687",
        username="neo4j",
        password="password",
        index_name="exercise_embeddings",
        text_node_property="name",
    )
    assert result is mock_vector_store
