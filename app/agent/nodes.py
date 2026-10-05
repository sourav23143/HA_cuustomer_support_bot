"""
LangGraph node functions.

Each function is a node in the state machine — takes AgentState,
returns a partial state update.
"""

import json
from datetime import datetime, timezone
import structlog

from app.config import Settings, get_settings
from app.agent.state import AgentState, TraceEvent
from app.classification.intent import IntentClassifier
from app.classification.schemas import IntentResult, INTENT_TAXONOMY
from app.context.builder import ContextBuilder
from app.rag.retriever import RAGRetriever
from app.safety.routing import SafetyRouter
from app.services.llm import LLMService
from app.services.ticket_service import TicketService
from app.models.ticket import TicketCreate
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)

# ── Dispute intents requiring human judgment ──
DISPUTE_INTENTS = {"refund_request", "refund_status", "payment_consultation_failure"}


def _trace(step: str, status: str, detail: str) -> TraceEvent:
    """Create a trace event."""
    return {"step": step, "status": status, "detail": detail}


# ────────────────────────────────────────────────────────────
# Node: classify_intent
# ────────────────────────────────────────────────────────────

async def classify_intent_node(state: AgentState) -> dict:
    """Classify the user's intent and extract entities."""
    settings = get_settings()
    llm = LLMService(settings)
    classifier = IntentClassifier(llm)

    traces = list(state.get("trace_events", []))

    try:
        result = await classifier.classify(
            state["user_message"],
            state.get("message_history"),
        )
        traces.append(_trace(
            "Intent detected",
            "success",
            f"{result.primary_intent} (confidence: {result.confidence:.2f})",
        ))

        # Add entity traces
        entities = result.entities
        for field in ["consultation_id", "payment_id", "amount", "doctor_name"]:
            val = getattr(entities, field, None)
            if val is not None:
                traces.append(_trace("Entity extracted", "success", f"{field} = {val}"))

        return {
            "intent_result": result,
            "trace_events": traces,
        }

    except Exception as e:
        logger.error("classify_intent_error", error=str(e))
        fallback = IntentResult(
            primary_intent="unknown",
            secondary_intents=[],
            confidence=0.2,
            priority="medium",
        )
        traces.append(_trace("Intent detected", "failed", f"Error: {str(e)[:100]}"))
        return {"intent_result": fallback, "trace_events": traces}


# ────────────────────────────────────────────────────────────
# Node: safety_check
# ────────────────────────────────────────────────────────────

async def safety_check_node(state: AgentState) -> dict:
    """Check if the intent requires safety routing."""
    intent_result = state["intent_result"]
    classification = SafetyRouter.classify(intent_result)

    traces = list(state.get("trace_events", []))
    traces.append(_trace(
        "Safety check",
        "success",
        f"Classification: {classification}",
    ))

    return {
        "safety_classification": classification,
        "trace_events": traces,
    }


# ────────────────────────────────────────────────────────────
# Node: build_context
# ────────────────────────────────────────────────────────────

async def build_context_node(state: AgentState) -> dict:
    """Retrieve relevant MongoDB context based on intent."""
    settings = get_settings()
    builder = ContextBuilder(settings)
    traces = list(state.get("trace_events", []))

    try:
        context = await builder.build_context(
            state["user_id"],
            state["intent_result"],
        )

        # Add traces for each tool used
        for tool_name in context.get("tools_used", []):
            traces.append(_trace(
                "MongoDB context retrieved",
                "success",
                tool_name,
            ))

        # Build platform_context dict
        platform_context = {}
        if context.get("consultation"):
            platform_context["consultation"] = context["consultation"]
        if context.get("payment"):
            platform_context["payment"] = context["payment"]
        if context.get("activities"):
            platform_context["activities"] = context["activities"]

        return {
            "user_context": context.get("user"),
            "mongodb_context": platform_context,
            "trace_events": traces,
        }

    except Exception as e:
        logger.error("build_context_error", error=str(e))
        traces.append(_trace("MongoDB context", "failed", str(e)[:100]))
        return {
            "user_context": None,
            "mongodb_context": {},
            "trace_events": traces,
        }


# ────────────────────────────────────────────────────────────
# Node: retrieve_knowledge
# ────────────────────────────────────────────────────────────

async def retrieve_knowledge_node(state: AgentState) -> dict:
    """Retrieve relevant knowledge from Qdrant."""
    settings = get_settings()
    retriever = RAGRetriever(settings)
    traces = list(state.get("trace_events", []))

    intent_result = state["intent_result"]
    category = INTENT_TAXONOMY.get(intent_result.primary_intent)
    category_str = category.value if category else None

    try:
        results = await retriever.retrieve(
            query=state["user_message"],
            category=category_str,
        )

        relevant_count = sum(
            1 for r in results if r.score >= settings.RAG_RELEVANCE_THRESHOLD
        )

        # If category-filtered search returns no highly relevant results, try unfiltered
        if relevant_count == 0 and category_str:
            results = await retriever.retrieve(query=state["user_message"])
            relevant_count = sum(
                1 for r in results if r.score >= settings.RAG_RELEVANCE_THRESHOLD
            )

        rag_text = retriever.format_results_for_prompt(results)

        traces.append(_trace(
            "Qdrant retrieval",
            "success",
            f"{relevant_count} relevant chunks (of {len(results)} retrieved)",
        ))

        return {
            "rag_results": results,
            "rag_text": rag_text,
            "trace_events": traces,
        }

    except Exception as e:
        logger.error("retrieve_knowledge_error", error=str(e))
        traces.append(_trace("Qdrant retrieval", "failed", str(e)[:100]))
        return {
            "rag_results": [],
            "rag_text": "Knowledge retrieval is temporarily unavailable.",
            "trace_events": traces,
        }


# ────────────────────────────────────────────────────────────
# Node: generate_response
# ────────────────────────────────────────────────────────────

async def generate_response_node(state: AgentState) -> dict:
    """Generate the LLM response using all context."""
    settings = get_settings()
    llm = LLMService(settings)
    traces = list(state.get("trace_events", []))

    try:
        response = await llm.generate_response(
            user_message=state["user_message"],
            intent_result=state["intent_result"],
            user_context=state.get("user_context") or {},
            platform_context=state.get("mongodb_context") or {},
            retrieved_knowledge=state.get("rag_text", ""),
            conversation_history=state.get("message_history"),
        )

        traces.append(_trace("Response generated", "success", f"{len(response)} chars"))

        return {"response": response, "trace_events": traces}

    except Exception as e:
        logger.error("generate_response_error", error=str(e))
        fallback = (
            "I apologize, but I'm experiencing a temporary issue. "
            "Please try again, or I can connect you with a human support agent."
        )
        traces.append(_trace("Response generated", "failed", str(e)[:100]))
        return {"response": fallback, "trace_events": traces}


# ────────────────────────────────────────────────────────────
# Node: resolution_decision
# ────────────────────────────────────────────────────────────

async def resolution_decision_node(state: AgentState) -> dict:
    """Determine whether to answer the user or escalate."""
    settings = get_settings()
    intent_result = state["intent_result"]
    rag_results = state.get("rag_results", [])
    traces = list(state.get("trace_events", []))

    should_escalate = False
    reason = None

    # Rule 1: Emergency
    if intent_result.primary_intent == "emergency_signal":
        should_escalate = True
        reason = "Emergency signal detected — requires immediate human attention"

    # Rule 2: Adverse event
    elif intent_result.primary_intent == "potential_adverse_event":
        should_escalate = True
        reason = "Potential adverse event — requires clinical review"

    # Rule 3: Human support request
    elif intent_result.primary_intent == "human_support_request":
        should_escalate = True
        reason = "User explicitly requested human support"

    # Rule 4: Low confidence
    elif intent_result.confidence < settings.INTENT_CONFIDENCE_THRESHOLD:
        should_escalate = True
        reason = f"Intent confidence {intent_result.confidence:.2f} below threshold {settings.INTENT_CONFIDENCE_THRESHOLD}"

    # Rule 5: No relevant knowledge
    elif rag_results and all(
        r.score < settings.RAG_RELEVANCE_THRESHOLD for r in rag_results
    ):
        # Only escalate if this is a knowledge-dependent intent
        knowledge_intents = {"platform_question", "pricing_question", "policy_question"}
        if intent_result.primary_intent in knowledge_intents:
            should_escalate = True
            reason = "No relevant knowledge found to safely answer"

    # Rule 6: Dispute/compensation
    elif intent_result.primary_intent == "unknown":
        should_escalate = True
        reason = "Intent outside normal support scope"

    # Rule 7: Payment + failed consultation → complex issue
    elif intent_result.primary_intent == "payment_consultation_failure":
        should_escalate = True
        reason = "Payment + consultation failure requires human review"

    # Rule 8: Doctor not joining with payment → escalate
    elif intent_result.primary_intent == "doctor_not_joining":
        ctx = state.get("mongodb_context", {})
        payment = ctx.get("payment")
        if payment and payment.get("status") == "success":
            should_escalate = True
            reason = "Doctor did not join paid consultation — requires refund/rebooking review"

    if should_escalate:
        traces.append(_trace("Decision", "success", f"Escalate: {reason}"))
    else:
        traces.append(_trace("Decision", "success", "Answer user directly"))

    return {
        "should_escalate": should_escalate,
        "escalation_reason": reason,
        "trace_events": traces,
    }


# ────────────────────────────────────────────────────────────
# Node: escalate (create ticket)
# ────────────────────────────────────────────────────────────

async def escalate_node(state: AgentState) -> dict:
    """Create a support ticket for escalation."""
    settings = get_settings()
    llm = LLMService(settings)
    ticket_service = TicketService(settings)
    traces = list(state.get("trace_events", []))

    intent_result = state["intent_result"]
    user_context = state.get("user_context") or {}
    mongodb_context = state.get("mongodb_context") or {}

    try:
        # Generate ticket summary
        summary = await llm.generate_ticket_summary(
            user_message=state["user_message"],
            intent_result=intent_result,
            user_context=user_context,
            platform_context=mongodb_context,
            escalation_reason=state.get("escalation_reason", "Requires human review"),
        )

        # Build ticket subject
        intent_display = intent_result.primary_intent.replace("_", " ").title()
        subject = f"{intent_display} — {user_context.get('name', 'Patient')}"

        # Build idempotency key
        idempotency_key = f"{state['conversation_id']}:{intent_result.primary_intent}"

        consultation = mongodb_context.get("consultation")
        payment = mongodb_context.get("payment")

        ticket_data = TicketCreate(
            user_id=state["user_id"],
            conversation_id=state["conversation_id"],
            category=intent_result.category,
            intent=intent_result.primary_intent,
            priority=intent_result.priority,
            subject=subject,
            summary=summary,
            reason_for_escalation=state.get("escalation_reason", "Requires human review"),
            consultation_id=consultation.get("consultation_id") if consultation else None,
            payment_id=payment.get("payment_id") if payment else None,
            idempotency_key=idempotency_key,
        )

        result = await ticket_service.create_ticket(ticket_data)

        traces.append(_trace("Ticket created", "success", result.ticket_id))

        # Append ticket info to response
        ticket_note = (
            f"\n\n📋 **Support Ticket Created: {result.ticket_id}**\n"
            f"A human support agent will review your case. "
            f"You can reference this ticket ID for follow-up."
        )

        return {
            "ticket_id": result.ticket_id,
            "ticket_created": True,
            "response": state.get("response", "") + ticket_note,
            "trace_events": traces,
        }

    except Exception as e:
        logger.error("escalation_error", error=str(e))
        traces.append(_trace("Ticket creation", "failed", str(e)[:100]))
        return {
            "ticket_id": None,
            "ticket_created": False,
            "trace_events": traces,
        }


# ────────────────────────────────────────────────────────────
# Node: handle_emergency
# ────────────────────────────────────────────────────────────

async def handle_emergency_node(state: AgentState) -> dict:
    """Handle emergency signals — bypass normal RAG flow."""
    settings = get_settings()
    llm = LLMService(settings)
    traces = list(state.get("trace_events", []))

    response = await llm.generate_emergency_response(state["user_message"])

    traces.append(_trace("Emergency pathway", "success", "Urgent safety response generated"))

    return {
        "response": response,
        "should_escalate": True,
        "escalation_reason": "Emergency signal detected — immediate human/clinical escalation",
        "rag_results": [],
        "rag_text": "",
        "mongodb_context": state.get("mongodb_context", {}),
        "trace_events": traces,
    }


# ────────────────────────────────────────────────────────────
# Node: handle_medical_advice
# ────────────────────────────────────────────────────────────

async def handle_medical_advice_node(state: AgentState) -> dict:
    """Handle medical advice requests — refusal pathway."""
    settings = get_settings()
    llm = LLMService(settings)
    traces = list(state.get("trace_events", []))

    response = await llm.generate_medical_refusal(state["user_message"])

    traces.append(_trace("Medical refusal", "success", "Cannot provide medical advice"))

    return {
        "response": response,
        "should_escalate": False,
        "escalation_reason": None,
        "rag_results": [],
        "rag_text": "",
        "trace_events": traces,
    }


# ────────────────────────────────────────────────────────────
# Node: store_message
# ────────────────────────────────────────────────────────────

async def store_message_node(state: AgentState) -> dict:
    """Store the AI response in the conversation history."""
    settings = get_settings()
    db = get_database(settings)

    try:
        now = datetime.now(timezone.utc)

        # Update conversation
        await db["support_conversations"].update_one(
            {"_id": state["conversation_id"]},
            {
                "$set": {
                    "updated_at": now,
                    "last_intent": state["intent_result"].primary_intent if state.get("intent_result") else None,
                    "status": "escalated" if state.get("should_escalate") else "active",
                }
            },
        )

        # Store assistant message
        import uuid
        await db["support_messages"].insert_one({
            "_id": f"MSG-{uuid.uuid4().hex[:12]}",
            "conversation_id": state["conversation_id"],
            "role": "assistant",
            "content": state.get("response", ""),
            "timestamp": now,
        })

    except Exception as e:
        logger.error("store_message_error", error=str(e))

    return {}
