"""
Ticket creation service.

Handles ticket creation with Pydantic validation, ID generation,
idempotency, and MongoDB insertion.
"""

from datetime import datetime, timezone
import structlog

from app.config import Settings
from app.db.mongodb import get_database
from app.models.ticket import TicketCreate, TicketResponse

logger = structlog.get_logger(__name__)

# Auto-incrementing ticket counter (seeded from DB on first call)
_ticket_counter: int | None = None


async def _get_next_ticket_id(settings: Settings) -> str:
    """Generate the next ticket ID (TKT-XXXXX)."""
    global _ticket_counter
    db = get_database(settings)

    if _ticket_counter is None:
        # Find the highest existing ticket number
        last = await db["support_tickets"].find_one(
            sort=[("_id", -1)]
        )
        if last and last["_id"].startswith("TKT-"):
            try:
                _ticket_counter = int(last["_id"].split("-")[1])
            except ValueError:
                _ticket_counter = 10000
        else:
            _ticket_counter = 10000

    _ticket_counter += 1
    return f"TKT-{_ticket_counter}"


class TicketService:
    """Creates and manages support tickets in MongoDB."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def create_ticket(self, ticket_data: TicketCreate) -> TicketResponse:
        """
        Create a support ticket.

        Uses idempotency_key to prevent duplicates for the same
        escalation event within a conversation.
        """
        db = get_database(self.settings)
        collection = db["support_tickets"]

        # Check idempotency — don't create duplicate for same event
        existing = await collection.find_one(
            {"idempotency_key": ticket_data.idempotency_key}
        )
        if existing:
            logger.info(
                "ticket_duplicate_prevented",
                idempotency_key=ticket_data.idempotency_key,
                existing_ticket=existing["_id"],
            )
            return TicketResponse(
                ticket_id=existing["_id"],
                status=existing["status"],
                created_at=existing["created_at"],
                message="Ticket already exists for this escalation event.",
            )

        # Generate ticket ID
        ticket_id = await _get_next_ticket_id(self.settings)
        now = datetime.now(timezone.utc)

        # Build ticket document
        ticket_doc = {
            "_id": ticket_id,
            "user_id": ticket_data.user_id,
            "conversation_id": ticket_data.conversation_id,
            "category": ticket_data.category,
            "intent": ticket_data.intent,
            "priority": ticket_data.priority,
            "subject": ticket_data.subject,
            "summary": ticket_data.summary,
            "reason_for_escalation": ticket_data.reason_for_escalation,
            "consultation_id": ticket_data.consultation_id,
            "payment_id": ticket_data.payment_id,
            "status": "open",
            "source": "ai_support_agent",
            "idempotency_key": ticket_data.idempotency_key,
            "created_at": now,
            "updated_at": now,
        }

        try:
            await collection.insert_one(ticket_doc)
            logger.info(
                "ticket_created",
                ticket_id=ticket_id,
                category=ticket_data.category,
                priority=ticket_data.priority,
            )
            return TicketResponse(
                ticket_id=ticket_id,
                status="open",
                created_at=now,
                message="Support ticket created successfully. A human agent will review your case.",
            )

        except Exception as e:
            logger.error("ticket_creation_failed", error=str(e))
            raise RuntimeError(f"Failed to create support ticket: {e}")

    async def get_ticket(self, ticket_id: str) -> dict | None:
        """Retrieve a ticket by ID."""
        db = get_database(self.settings)
        ticket = await db["support_tickets"].find_one({"_id": ticket_id})
        if ticket:
            ticket["ticket_id"] = ticket.pop("_id")
        return ticket
