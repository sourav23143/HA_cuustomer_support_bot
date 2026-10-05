"""
Ticket creation tool — the only write operation allowed.
"""

from app.config import Settings
from app.models.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import TicketService


async def create_support_ticket(
    ticket_data: TicketCreate, settings: Settings
) -> TicketResponse:
    """
    Create a support ticket in MongoDB.

    This is the ONLY write operation in the tools layer.
    The LLM never calls this directly — the orchestrator
    decides when escalation is needed and invokes this.
    """
    service = TicketService(settings)
    return await service.create_ticket(ticket_data)
