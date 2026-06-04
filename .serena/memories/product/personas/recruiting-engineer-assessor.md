# Persona: Recruiting Engineer / Assessor

The fitness coaching multi-agent system (PRD-001) has a second key persona beyond the end user: the **recruiting engineer / assessor** who reviews the submitted public GitHub repo.

**Goals in this product:**
- Evaluate routing correctness (LLM structured output, not regex)
- Assess LangGraph architecture quality (typed StateGraph, separate sub-agent graphs)
- Judge resilience design (edge cases handled without exceptions)
- Read the candidate's production-readiness thinking in the README

**Implication:** The README "How I would evaluate this in production" section is a first-class product requirement (US-4, AC-3), not optional documentation. Treat assessor-facing artifacts with the same care as user-facing features.

See PRD-001: `.docs/prd/active/001-fitness-coaching-multi-agent.md`
