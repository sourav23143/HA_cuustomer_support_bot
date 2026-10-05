"""
Chat API endpoint.
"""

from pydantic import BaseModel, Field
from typing import Optional
from fastapi import APIRouter, HTTPException
import structlog

from app.config import get_settings
from app.agent.orchestrator import SupportAgentOrchestrator

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request body."""
    user_id: str
    message: str
    conversation_id: Optional[str] = None


class TraceEventResponse(BaseModel):
    """A trace event in the response."""
    step: str
    status: str
    detail: str


class ChatResponse(BaseModel):
    """Chat response body."""
    conversation_id: str
    response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    priority: Optional[str] = None
    ticket_id: Optional[str] = None
    escalated: bool = False
    trace: list[TraceEventResponse] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.

    Runs the full agent pipeline: intent detection → context → RAG → response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    settings = get_settings()
    orchestrator = SupportAgentOrchestrator(settings)

    try:
        result = await orchestrator.process_message(
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id,
        )

        trace_events = [
            TraceEventResponse(**t) for t in result.get("trace", [])
        ]

        return ChatResponse(
            conversation_id=result["conversation_id"],
            response=result["response"],
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            priority=result.get("priority"),
            ticket_id=result.get("ticket_id"),
            escalated=result.get("escalated", False),
            trace=trace_events,
        )

    except Exception as e:
        logger.error("chat_endpoint_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your request. Please try again.",
        )
