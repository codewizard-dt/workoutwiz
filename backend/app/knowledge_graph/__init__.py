"""Knowledge graph package — Neo4j schema, seeding, and ingestion utilities."""

from app.knowledge_graph.ingest_workout_history import ingest_workout_history

__all__ = ["ingest_workout_history"]