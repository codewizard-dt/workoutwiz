"""
Load backend/data/snomed_subset.json into Neo4j.

Creates:
  (:BodyStructure)                 — one per joint (9) + all child sub-structures
  (:Disorder)                      — one per resolved injury label (19)
  (:BodyStructure)-[:PART_OF]->(:BodyStructure)   — child → parent hierarchy
  (:Disorder)-[:FINDING_SITE]->(:BodyStructure)   — disorder → body structure
  (:Exercise)-[:MAPS_TO]->(:BodyStructure)         — replaces string-match safety filter
  (:Injury)-[:MAPS_TO_DISORDER]->(:Disorder)       — links ingested injuries to SNOMED

All operations are idempotent (MERGE).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, cast

import neo4j

from app.config import settings

logger = logging.getLogger(__name__)

_SUBSET_PATH = Path(__file__).parent.parent.parent / "data" / "snomed_subset.json"


def _load_subset() -> dict[str, Any]:
    if not _SUBSET_PATH.exists():
        raise FileNotFoundError(
            f"SNOMED subset not found at {_SUBSET_PATH}. "
            "Run: cd backend && python scripts/build_snomed_subset.py"
        )
    return cast(dict[str, Any], json.loads(_SUBSET_PATH.read_text()))


# ── BodyStructure nodes ────────────────────────────────────────────────────

def _merge_body_structure(tx: neo4j.ManagedTransaction, node: dict[str, Any]) -> None:
    tx.run(
        """
        MERGE (b:BodyStructure {snomed_code: $code})
        SET b.snomed_name    = $name,
            b.catalog_term   = $catalog_term,
            b.skos_relation  = $skos_relation
        """,
        code=node["snomed_code"],
        name=node["snomed_name"],
        catalog_term=node.get("catalog_term"),
        skos_relation=node.get("skos_relation"),
    )


def _merge_part_of(tx: neo4j.ManagedTransaction, child_code: str, parent_code: str) -> None:
    tx.run(
        """
        MATCH (child:BodyStructure {snomed_code: $child_code})
        MATCH (parent:BodyStructure {snomed_code: $parent_code})
        MERGE (child)-[:PART_OF]->(parent)
        """,
        child_code=child_code,
        parent_code=parent_code,
    )


# ── Disorder nodes ─────────────────────────────────────────────────────────

def _merge_disorder(tx: neo4j.ManagedTransaction, disorder: dict[str, Any]) -> None:
    tx.run(
        """
        MERGE (d:Disorder {snomed_code: $code})
        SET d.snomed_name        = $name,
            d.label              = $label,
            d.expected_joint     = $expected_joint,
            d.finding_site_code  = $finding_site_code,
            d.finding_site_name  = $finding_site_name,
            d.validated          = $validated
        """,
        code=disorder["disorder_code"],
        name=disorder["disorder_name"],
        label=disorder["label"],
        expected_joint=disorder["expected_joint"],
        finding_site_code=disorder.get("finding_site_code"),
        finding_site_name=disorder.get("finding_site_name"),
        validated=disorder.get("validated", False),
    )


def _merge_finding_site_edge(
    tx: neo4j.ManagedTransaction,
    disorder: dict[str, Any],
    joint_code_map: dict[str, str],
) -> None:
    fs_code = disorder.get("finding_site_code")
    if not fs_code:
        return
    tx.run(
        """
        MATCH (d:Disorder {snomed_code: $disorder_code})
        MATCH (b:BodyStructure {snomed_code: $fs_code})
        MERGE (d)-[:FINDING_SITE]->(b)
        """,
        disorder_code=disorder["disorder_code"],
        fs_code=fs_code,
    )
    # Bridge PART_OF: finding-site → catalog joint root.
    # Tendons, bursae, and muscle groups near a joint are often in a parallel
    # SNOMED hierarchy and don't have pathsToRoot through the joint node.
    # Adding this edge closes the safety traversal loop without misrepresenting
    # the ontology — the finding site IS anatomically at the catalog joint.
    catalog_code = joint_code_map.get(disorder.get("expected_joint", ""))
    if catalog_code and catalog_code != fs_code:
        tx.run(
            """
            MATCH (fs:BodyStructure {snomed_code: $fs_code})
            MATCH (joint:BodyStructure {snomed_code: $joint_code})
            MERGE (fs)-[:PART_OF]->(joint)
            """,
            fs_code=fs_code,
            joint_code=catalog_code,
        )


# ── Exercise → BodyStructure MAPS_TO edges ─────────────────────────────────

def _wire_exercise_maps_to(session: neo4j.Session, joint_catalog_terms: list[str]) -> int:
    """
    For each catalog joint, wire Exercise-[:MAPS_TO]->BodyStructure for every
    exercise whose joints_loaded contains that joint term.
    """
    result = session.run(
        """
        UNWIND $catalog_terms AS term
        MATCH (e:Exercise)
        WHERE term IN e.joints_loaded
        MATCH (b:BodyStructure {catalog_term: term})
        MERGE (e)-[r:MAPS_TO]->(b)
        ON CREATE SET r.catalog_term = term
        RETURN count(r) AS created
        """,
        catalog_terms=joint_catalog_terms,
    )
    record = result.single()
    return int(record["created"]) if record is not None else 0


# ── Injury → Disorder MAPS_TO_DISORDER edges ───────────────────────────────

def _wire_injury_maps_to_disorder(session: neo4j.Session) -> int:
    """
    Link each Injury node to its Disorder by matching snomedct_hint to
    Disorder.label.  Falls back to matching on injury name via expected_joint.
    """
    result = session.run(
        """
        MATCH (i:Injury)
        WHERE i.snomedct_hint IS NOT NULL
        MATCH (d:Disorder {label: i.snomedct_hint})
        MERGE (i)-[r:MAPS_TO_DISORDER]->(d)
        RETURN count(r) AS linked
        """
    )
    record = result.single()
    return int(record["linked"]) if record is not None else 0


# ── public entry point ─────────────────────────────────────────────────────

def ingest_snomed(driver: neo4j.Driver) -> dict[str, int]:
    """Load snomed_subset.json into Neo4j. Idempotent.

    Returns a summary dict with counts of nodes and edges created/merged.
    """
    subset = _load_subset()
    joints: list[dict[str, Any]] = subset.get("joints", [])
    disorders: list[dict[str, Any]] = subset.get("injuries", [])

    counts: dict[str, int] = {}

    with driver.session() as session:
        # 1. BodyStructure nodes — catalog joint roots
        for j in joints:
            session.execute_write(_merge_body_structure, {
                "snomed_code": j["snomed_code"],
                "snomed_name": j["snomed_name"],
                "catalog_term": j["catalog_term"],
                "skos_relation": j["skos_relation"],
            })
        counts["joint_root_nodes"] = len(joints)

        # 2. BodyStructure nodes — children + PART_OF edges
        child_count = 0
        part_of_count = 0
        for j in joints:
            for child in j.get("children", []):
                session.execute_write(_merge_body_structure, {
                    "snomed_code": child["snomed_code"],
                    "snomed_name": child["snomed_name"],
                    "catalog_term": None,
                    "skos_relation": None,
                })
                session.execute_write(
                    _merge_part_of, child["snomed_code"], j["snomed_code"]
                )
                child_count += 1
                part_of_count += 1
        counts["child_body_structure_nodes"] = child_count
        counts["part_of_edges"] = part_of_count

        # 3. Finding-site BodyStructure nodes (may be distinct from joint roots/children)
        fs_codes_seen: set[str] = {j["snomed_code"] for j in joints}
        for c in [c for j in joints for c in j.get("children", [])]:
            fs_codes_seen.add(c["snomed_code"])

        fs_node_count = 0
        for d in disorders:
            fs_code = d.get("finding_site_code")
            fs_name = d.get("finding_site_name", "")
            if fs_code and fs_code not in fs_codes_seen:
                session.execute_write(_merge_body_structure, {
                    "snomed_code": fs_code,
                    "snomed_name": fs_name,
                    "catalog_term": None,
                    "skos_relation": None,
                })
                fs_codes_seen.add(fs_code)
                fs_node_count += 1
        counts["finding_site_nodes"] = fs_node_count

        # 4. Disorder nodes + FINDING_SITE edges + bridge PART_OF to catalog joint
        joint_code_map = {j["catalog_term"]: j["snomed_code"] for j in joints}
        for d in disorders:
            session.execute_write(_merge_disorder, d)
            session.execute_write(_merge_finding_site_edge, d, joint_code_map)
        counts["disorder_nodes"] = len(disorders)
        counts["finding_site_edges"] = sum(1 for d in disorders if d.get("finding_site_code"))

        # 5. Exercise -[:MAPS_TO]-> BodyStructure
        catalog_terms = [j["catalog_term"] for j in joints]
        counts["exercise_maps_to_edges"] = _wire_exercise_maps_to(session, catalog_terms)

        # 6. Injury -[:MAPS_TO_DISORDER]-> Disorder
        counts["injury_maps_to_disorder_edges"] = _wire_injury_maps_to_disorder(session)

    logger.info("SNOMED ingestion complete: %s", counts)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    with neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    ) as _driver:
        summary = ingest_snomed(_driver)
    for k, v in summary.items():
        print(f"  {k}: {v}")
