"""
LangGraph agent orchestrator.

Defines the StateGraph workflow with conditional edges.
"""

import uuid
from datetime import datetime, timezone
import structlog

from langgraph.graph import StateGraph, END

from app.config import Settings, get_settings
from app.agent.state import AgentState
from app.agent.nodes import (
    classify_intent_node,
    safety_check_node,
    build_context_node,
    retrieve_knowledge_node,
    generate_response_node,
    resolution_decision_node,
    escalate_node,
    handle_emergency_node,
    handle_medical_advice_node,
    store_message_node,
)
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)


# ── Conditional edge functions ───────────────────────────────

def safety_router(state: AgentState) -> str:
    """Route based on safety classification."""
    classification = state.get("safety_classification", "safe")

    if classification == "emergency":
        return "handle_emergency"
    elif classification in ("medical_advice",):
        return "handle_medical_advice"
    elif classification == "adverse_event":
        return "handle_emergency"  # Adverse events also get urgent pathway
    else:
        return "build_context"


def escalation_router(state: AgentState) -> str:
    """Route based on escalation decision."""
    if state.get("should_escalate", False):
        return "escalate"
    else:
        return "store_message"


def post_emergency_router(state: AgentState) -> str:
    """After emergency/medical handling, decide if ticket needed."""
    if state.get("should_escalate", False):
        return "escalate"
    else:
        return "store_message"


# ── Build the graph ──────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph workflow.

    Flow:
        classify_intent → safety_check
        safety_check → [emergency | medical | build_context]
        build_context → retrieve_knowledge → generate_response → resolution_decision
        resolution_decision → [escalate | store_message]
        escalate → store_message
        handle_emergency → [escalate | store_message]
        handle_medical_advice → store_message
        store_message → END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("safety_check", safety_check_node)
    graph.add_node("build_context", build_context_node)
    graph.add_node("retrieve_knowledge", retrieve_knowledge_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("resolution_decision", resolution_decision_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("handle_emergency", handle_emergency_node)
    graph.add_node("handle_medical_advice", handle_medical_advice_node)
    graph.add_node("store_message", store_message_node)

    # Set entry point
    graph.set_entry_point("classify_intent")

    # Add edges
    graph.add_edge("classify_intent", "safety_check")

    graph.add_conditional_edges(
        "safety_check",
        safety_router,
        {
            "handle_emergency": "handle_emergency",
            "handle_medical_advice": "handle_medical_advice",
            "build_context": "build_context",
        },
    )

    graph.add_edge("build_context", "retrieve_knowledge")
    graph.add_edge("retrieve_knowledge", "generate_response")
    graph.add_edge("generate_response", "resolution_decision")

    graph.add_conditional_edges(
        "resolution_decision",
        escalation_router,
        {
            "escalate": "escalate",
            "store_message": "store_message",
        },
    )

    graph.add_edge("escalate", "store_message")

    graph.add_conditional_edges(
        "handle_emergency",
        post_emergency_router,
        {
            "escalate": "escalate",
            "store_message": "store_message",
        },
    )

    graph.add_edge("handle_medical_advice", "store_message")
    graph.add_edge("store_message", END)

    return graph


# Compile the graph
_compiled_graph = None


def get_compiled_graph():
    """Get or compile the LangGraph workflow."""
    global _compiled_graph
    if _compiled_graph is None:
        graph = build_agent_graph()
        _compiled_graph = graph.compile()
        logger.info("langgraph_compiled")
    return _compiled_graph


# ── Orchestrator class ───────────────────────────────────────

class SupportAgentOrchestrator:
    """
    Runs the LangGraph agent workflow for a user support message.
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
    ) -> dict:
        """
        Process a user support message through the full agent pipeline.

        Returns dict with: conversation_id, response, intent, confidence,
        ticket_id, escalated, trace.
        """
        db = get_database(self.settings)
        now = datetime.now(timezone.utc)

        # Create or get conversation
        if not conversation_id:
            conversation_id = f"CONV-{uuid.uuid4().hex[:8]}"
            await db["support_conversations"].insert_one({
                "_id": conversation_id,
                "user_id": user_id,
                "status": "active",
                "created_at": now,
                "updated_at": now,
                "last_intent": None,
            })

        # Store user message
        await db["support_messages"].insert_one({
            "_id": f"MSG-{uuid.uuid4().hex[:12]}",
            "conversation_id": conversation_id,
            "role": "user",
            "content": message,
            "timestamp": now,
        })

        # Fetch conversation history
        history_cursor = (
            db["support_messages"]
            .find({"conversation_id": conversation_id})
            .sort("timestamp", 1)
            .limit(20)
        )
        history = []
        async for msg in history_cursor:
            history.append({
                "role": msg["role"],
                "content": msg["content"],
            })

        # Build initial state
        initial_state: AgentState = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "user_message": message,
            "message_history": history[:-1],  # Exclude current message
            "intent_result": None,
            "safety_classification": "safe",
            "user_context": None,
            "mongodb_context": {},
            "rag_results": [],
            "rag_text": "",
            "response": "",
            "should_escalate": False,
            "escalation_reason": None,
            "ticket_id": None,
            "ticket_created": False,
            "trace_events": [],
            "error": None,
        }

        # Run the LangGraph workflow
        compiled = get_compiled_graph()

        try:
            final_state = await compiled.ainvoke(initial_state)
        except Exception as e:
            logger.error("orchestrator_error", error=str(e))
            final_state = {
                **initial_state,
                "response": (
                    "I apologize, but I'm experiencing a temporary issue processing your request. "
                    "Please try again, or type 'human support' to connect with a support agent."
                ),
                "trace_events": [{"step": "Orchestrator", "status": "failed", "detail": str(e)[:200]}],
            }

        # Build result
        intent_result = final_state.get("intent_result")

        return {
            "conversation_id": conversation_id,
            "response": final_state.get("response", ""),
            "intent": intent_result.primary_intent if intent_result else None,
            "confidence": intent_result.confidence if intent_result else None,
            "priority": intent_result.priority if intent_result else None,
            "ticket_id": final_state.get("ticket_id"),
            "escalated": final_state.get("should_escalate", False),
            "trace": final_state.get("trace_events", []),
        }
