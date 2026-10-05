"""
LLM service — wraps Groq via LangChain ChatGroq.

Provides intent classification and response generation using LangChain PromptTemplates.
"""

import json
import structlog

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import Settings
from app.classification.schemas import IntentResult, ExtractedEntities
from app.agent.prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    RESPONSE_PROMPT,
    MEDICAL_REFUSAL_PROMPT,
    EMERGENCY_RESPONSE_PROMPT,
    TICKET_SUMMARY_PROMPT,
)

logger = structlog.get_logger(__name__)


class LLMService:
    """Groq LLM service for classification and response generation."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        logger.info("llm_service_initialized", model=settings.LLM_MODEL)

    async def classify_intent(
        self, message: str, history: list[dict] | None = None
    ) -> IntentResult:
        """
        Classify user intent using structured JSON output from Groq.

        Returns a validated IntentResult.
        """
        history_text = ""
        if history:
            recent = history[-6:]  # Last 3 exchanges
            history_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in recent
            )

        user_prompt = f"## Conversation History\n{history_text}\n\n## Current Message\n{message}"

        # Invoke the LangChain ChatPromptTemplate
        prompt_value = INTENT_CLASSIFICATION_PROMPT.invoke({"user_message": user_prompt})

        try:
            response = await self.llm.ainvoke(prompt_value)
            raw = response.content.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            data = json.loads(raw)

            # Parse entities
            entities_data = data.get("entities", {})
            entities = ExtractedEntities(**entities_data)

            result = IntentResult(
                primary_intent=data.get("primary_intent", "unknown"),
                secondary_intents=data.get("secondary_intents", []),
                confidence=float(data.get("confidence", 0.5)),
                entities=entities,
                priority=data.get("priority", "medium"),
            )

            logger.info(
                "intent_classified",
                intent=result.primary_intent,
                confidence=result.confidence,
                priority=result.priority,
            )
            return result

        except json.JSONDecodeError as e:
            logger.error("intent_json_parse_error", error=str(e), raw=raw[:200])
            # Fallback: return unknown with low confidence
            return IntentResult(
                primary_intent="unknown",
                secondary_intents=[],
                confidence=0.3,
                entities=ExtractedEntities(),
                priority="medium",
            )
        except Exception as e:
            logger.error("intent_classification_error", error=str(e))
            return IntentResult(
                primary_intent="unknown",
                secondary_intents=[],
                confidence=0.2,
                entities=ExtractedEntities(),
                priority="medium",
            )

    async def generate_response(
        self,
        user_message: str,
        intent_result: IntentResult,
        user_context: dict,
        platform_context: dict,
        retrieved_knowledge: str,
        conversation_history: list[dict] | None = None,
    ) -> str:
        """Generate a grounded support response."""
        history_text = ""
        if conversation_history:
            recent = conversation_history[-8:]
            history_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in recent
            )

        # Invoke the LangChain ChatPromptTemplate
        prompt_value = RESPONSE_PROMPT.invoke({
            "user_message": user_message,
            "primary_intent": intent_result.primary_intent,
            "confidence": intent_result.confidence,
            "priority": intent_result.priority,
            "user_context": json.dumps(user_context, indent=2, default=str),
            "platform_context": json.dumps(platform_context, indent=2, default=str),
            "retrieved_knowledge": retrieved_knowledge or "No relevant documentation found.",
            "conversation_history": history_text or "No previous messages.",
        })

        try:
            response = await self.llm.ainvoke(prompt_value)
            logger.info("response_generated", length=len(response.content))
            return response.content.strip()
        except Exception as e:
            logger.error("response_generation_error", error=str(e))
            return (
                "I apologize, but I'm experiencing a temporary issue. "
                "Please try again in a moment, or I can connect you with "
                "a human support agent."
            )

    async def generate_medical_refusal(self, user_message: str) -> str:
        """Generate a medical advice refusal response."""
        prompt_value = MEDICAL_REFUSAL_PROMPT.invoke({"user_message": user_message})
        
        try:
            response = await self.llm.ainvoke(prompt_value)
            return response.content.strip()
        except Exception as e:
            logger.error("medical_refusal_error", error=str(e))
            return (
                "I understand you have a medical concern. As a support assistant, "
                "I'm not qualified to provide medical advice. Please book a consultation "
                "with a doctor on HealthAssist for professional medical guidance."
            )

    async def generate_emergency_response(self, user_message: str) -> str:
        """Generate an emergency response with urgent safety info."""
        prompt_value = EMERGENCY_RESPONSE_PROMPT.invoke({"user_message": user_message})
        
        try:
            response = await self.llm.ainvoke(prompt_value)
            return response.content.strip()
        except Exception as e:
            logger.error("emergency_response_error", error=str(e))
            return (
                "⚠️ URGENT: If you are experiencing a medical emergency, "
                "please call 112 (Emergency) or 108 (Ambulance) immediately. "
                "Go to the nearest hospital emergency department. "
                "Do NOT rely on this platform for emergency medical care."
            )

    async def generate_ticket_summary(
        self,
        user_message: str,
        intent_result: IntentResult,
        user_context: dict,
        platform_context: dict,
        escalation_reason: str,
    ) -> str:
        """Generate a structured ticket summary for escalation."""
        prompt_value = TICKET_SUMMARY_PROMPT.invoke({
            "user_message": user_message,
            "intent": intent_result.primary_intent,
            "confidence": intent_result.confidence,
            "user_context": json.dumps(user_context, indent=2, default=str),
            "platform_context": json.dumps(platform_context, indent=2, default=str),
            "escalation_reason": escalation_reason,
        })

        try:
            response = await self.llm.ainvoke(prompt_value)
            return response.content.strip()
        except Exception as e:
            logger.error("ticket_summary_error", error=str(e))
            return f"User reported: {user_message[:200]}. Escalation reason: {escalation_reason}"
