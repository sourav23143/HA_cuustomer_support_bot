"""
LangGraph agent state definition.
"""

from typing import TypedDict, Optional
from app.classification.schemas import IntentResult
from app.rag.retriever import RetrievalResult


class TraceEvent(TypedDict):
    """A single observable trace event."""
    step: str
    status: str   # success | failed | skipped
    detail: str


class AgentState(TypedDict, total=False):
    """State object passed through the LangGraph workflow."""

    # ── Input ─────────────────────────────────────
    user_id: str
    conversation_id: str
    user_message: str
    message_history: list[dict]

    # ── Intent & Entities ─────────────────────────
    intent_result: Optional[IntentResult]

    # ── Safety ────────────────────────────────────
    safety_classification: str  # safe | medical_advice | emergency | adverse_event

    # ── Context ───────────────────────────────────
    user_context: Optional[dict]
    mongodb_context: Optional[dict]
    rag_results: Optional[list[RetrievalResult]]
    rag_text: str

    # ── Response ──────────────────────────────────
    response: str
    should_escalate: bool
    escalation_reason: Optional[str]

    # ── Ticket ────────────────────────────────────
    ticket_id: Optional[str]
    ticket_created: bool

    # ── Trace ─────────────────────────────────────
    trace_events: list[TraceEvent]

    # ── Error ─────────────────────────────────────
    error: Optional[str]
