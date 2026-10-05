"""
Context builder — assembles relevant context based on intent.

Retrieves only what's needed for each type of request.
"""

import structlog

from app.config import Settings
from app.classification.schemas import IntentResult, IntentCategory, INTENT_TAXONOMY
from app.tools.user import get_user_context
from app.tools.consultation import get_active_consultation, get_consultation_by_id
from app.tools.payment import get_payment_status, get_payments_for_user
from app.tools.activity import get_user_activity

logger = structlog.get_logger(__name__)

# Intents that need consultation context
CONSULTATION_INTENTS = {
    "doctor_not_joining", "consultation_failed", "consultation_cancelled",
    "call_problem", "doctor_replacement", "payment_consultation_failure",
}

# Intents that need payment context
PAYMENT_INTENTS = {
    "payment_failed", "payment_pending", "payment_success",
    "refund_request", "refund_status", "payment_consultation_failure",
}

# Intents that primarily use RAG (minimal MongoDB)
RAG_INTENTS = {
    "platform_question", "pricing_question", "policy_question",
}


class ContextBuilder:
    """Builds relevant context from MongoDB based on detected intent."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def build_context(
        self, user_id: str, intent_result: IntentResult
    ) -> dict:
        """
        Build context tailored to the intent.

        Returns dict with: user_context, consultation, payment, activities.
        Only fetches what's relevant for the detected intent.
        """
        context = {
            "user": None,
            "consultation": None,
            "payment": None,
            "activities": [],
            "tools_used": [],
        }

        intent = intent_result.primary_intent
        entities = intent_result.entities

        # Always get user context
        user = await get_user_context(user_id, self.settings)
        context["user"] = user
        context["tools_used"].append("get_user_context")

        # For RAG-only intents, skip heavy MongoDB lookups
        if intent in RAG_INTENTS:
            logger.info("context_built_rag_only", intent=intent)
            return context

        # Get consultation context for relevant intents
        if intent in CONSULTATION_INTENTS or intent in PAYMENT_INTENTS:
            # Use specific consultation_id from entities if available
            if entities.consultation_id:
                consultation = await get_consultation_by_id(
                    entities.consultation_id, self.settings
                )
            else:
                consultation = await get_active_consultation(user_id, self.settings)

            context["consultation"] = consultation
            context["tools_used"].append("get_active_consultation")

            # Get payment if we have a consultation
            if consultation and (intent in PAYMENT_INTENTS or intent in CONSULTATION_INTENTS):
                payment = await get_payment_status(
                    consultation["consultation_id"], self.settings
                )
                context["payment"] = payment
                context["tools_used"].append("get_payment_status")

        # Get activity for account and consultation issues
        if intent not in RAG_INTENTS:
            activities = await get_user_activity(user_id, self.settings, limit=5)
            context["activities"] = activities
            context["tools_used"].append("get_user_activity")

        logger.info(
            "context_built",
            intent=intent,
            has_user=bool(context["user"]),
            has_consultation=bool(context["consultation"]),
            has_payment=bool(context["payment"]),
            activity_count=len(context["activities"]),
            tools_used=context["tools_used"],
        )

        return context
