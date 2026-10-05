"""
Ticket API endpoints.
"""

from fastapi import APIRouter, HTTPException
import structlog

from app.config import get_settings
from app.models.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import TicketService
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["tickets"])


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(ticket_data: TicketCreate):
    """Create a support ticket."""
    settings = get_settings()
    service = TicketService(settings)

    try:
        return await service.create_ticket(ticket_data)
    except Exception as e:
        logger.error("ticket_api_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create ticket")


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get ticket details."""
    settings = get_settings()
    service = TicketService(settings)

    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details with messages."""
    settings = get_settings()
    db = get_database(settings)

    conversation = await db["support_conversations"].find_one(
        {"_id": conversation_id}
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages_cursor = (
        db["support_messages"]
        .find({"conversation_id": conversation_id})
        .sort("timestamp", 1)
    )
    messages = []
    async for msg in messages_cursor:
        messages.append({
            "message_id": msg["_id"],
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": str(msg["timestamp"]),
        })

    return {
        "conversation_id": conversation["_id"],
        "user_id": conversation["user_id"],
        "status": conversation["status"],
        "last_intent": conversation.get("last_intent"),
        "created_at": str(conversation.get("created_at")),
        "messages": messages,
    }
