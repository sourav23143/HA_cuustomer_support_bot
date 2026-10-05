"""
LLM-based intent classifier.

Uses the LLM service for classification but provides a clean
interface that could later be swapped with a trained ML classifier.
"""

import structlog

from app.classification.schemas import IntentResult
from app.services.llm import LLMService

logger = structlog.get_logger(__name__)


class IntentClassifier:
    """
    Intent classifier using LLM structured output.

    Designed with a clean interface so this can be replaced
    with a trained ML classifier in the future.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def classify(
        self, message: str, history: list[dict] | None = None
    ) -> IntentResult:
        """
        Classify the intent of a user message.

        Args:
            message: The user's support message.
            history: Optional conversation history for context.

        Returns:
            IntentResult with primary intent, entities, confidence.
        """
        result = await self.llm_service.classify_intent(message, history)
        logger.info(
            "intent_classification_complete",
            intent=result.primary_intent,
            confidence=result.confidence,
            entities_found=bool(result.entities.consultation_id or result.entities.amount),
        )
        return result
