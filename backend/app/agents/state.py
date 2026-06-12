from enum import StrEnum
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class Intent(StrEnum):
    MEMBER_CONTEXT_KG = "MEMBER_CONTEXT_KG"
    WORKOUT_LOG = "WORKOUT_LOG"
    FALLBACK = "FALLBACK"
    WORKOUT_GENERATE_KG = "WORKOUT_GENERATE_KG"

class RouteDecision(BaseModel):
    """Structured output from the router node. Used with with_structured_output()."""

    intent: Intent = Field(
        description=(
            "The most likely intent of the user message. "
            "MEMBER_CONTEXT_KG for fitness questions, advice, and education (not workout generation). "
            "WORKOUT_LOG to record a completed workout. "
            "WORKOUT_GENERATE_KG to build, create, plan, generate, OR recommend a personalized, injury-aware list of exercises for this user — "
            "including questions like 'what exercises suit my injuries?' whose best answer is a tailored exercise list. "
            "FALLBACK when the message is unclear or off-topic."
        )
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score between 0.0 and 1.0. "
            "Use < 0.6 only when the intent is genuinely ambiguous."
        ),
    )
    reasoning: str = Field(
        description="One sentence explaining why this intent was chosen."
    )


class AgentState(TypedDict):
    """Shared state flowing through the hub StateGraph and all sub-agent graphs."""

    # Conversation history — LangGraph accumulates messages with add_messages reducer
    messages: Annotated[list[Any], add_messages]

    # Set by the router node after classification
    route_decision: RouteDecision | None

    # User identity — populated by the FastAPI layer before graph invocation
    user_id: str | None
    user_email: str | None

    # Audit fields — populated as the graph executes
    session_id: str | None
    audit_log: list[dict[str, Any]]

    # Knowledge graph result — populated by GENERATE_KG_node (WORKOUT_GENERATE_KG route only)
    kg_result: dict[str, Any] | None
