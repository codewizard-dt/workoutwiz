# Personas: Fitness Coach and Member (PRD-002)

Introduced in PRD-002 (Knowledge Graph Coaching System).

## Alex's Coach (fitness coach)
- Professional or semi-professional coach managing multiple members
- Needs to trust and explain every AI recommendation
- Primary ask: injury-aware workout generation + "why was X skipped?" explainability
- Interacts with the system directly via API/frontend

## Alex (member)
- Has documented injuries, equipment constraints, goals, and workout history stored in the knowledge graph
- Does NOT interact with the system directly — their context shapes outputs
- Synthetic data only (no real personal/health data)

## Key product constraint
Injury contraindication filtering must be 100% reliable — no contraindicated exercise can ever appear in a generated workout. Every skip must be traceable to a real graph path, not a vague LLM rationale.

See PRD-002: `.docs/prd/002-knowledge-graph-coaching-system.md`
