"""
Evaluation script for the AI Support Agent.

Usage:
    python evals/evaluate.py
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.services.llm import LLMService
from app.classification.intent import IntentClassifier
from app.classification.schemas import INTENT_TAXONOMY


async def run_evaluation():
    """Run evaluation on support_cases.jsonl."""
    settings = get_settings()
    llm = LLMService(settings)
    classifier = IntentClassifier(llm)

    # Load eval cases
    eval_file = os.path.join(os.path.dirname(__file__), "support_cases.jsonl")
    cases = []
    with open(eval_file, "r") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    print("=" * 60)
    print("  AI Support Agent Evaluation")
    print(f"  Total cases: {len(cases)}")
    print("=" * 60)

    intent_correct = 0
    category_correct = 0
    escalation_correct = 0
    total = len(cases)

    for i, case in enumerate(cases, 1):
        query = case["query"]
        expected_intent = case["expected_intent"]
        expected_category = case["expected_category"]
        expected_escalation = case["expected_escalation"]

        try:
            result = await classifier.classify(query)

            # Check intent
            intent_match = result.primary_intent == expected_intent
            if intent_match:
                intent_correct += 1

            # Check category
            actual_category = INTENT_TAXONOMY.get(result.primary_intent)
            cat_match = (actual_category and actual_category.value == expected_category)
            if cat_match:
                category_correct += 1

            # Check escalation (approximate — based on priority and intent)
            would_escalate = (
                result.primary_intent in ("emergency_signal", "potential_adverse_event", "human_support_request", "unknown")
                or result.primary_intent == "payment_consultation_failure"
                or result.confidence < settings.INTENT_CONFIDENCE_THRESHOLD
            )

            # Also check for refund_request with high amounts (compensation demands)
            if result.primary_intent == "refund_request" and result.entities.amount and result.entities.amount > 10000:
                would_escalate = True
            elif result.primary_intent == "refund_request":
                would_escalate = True  # refund requests typically escalate

            esc_match = would_escalate == expected_escalation
            if esc_match:
                escalation_correct += 1

            status = "✓" if (intent_match and esc_match) else "✗"
            print(f"  {status} [{i:2d}] {query[:50]:50s} → {result.primary_intent:30s} (exp: {expected_intent})")

        except Exception as e:
            print(f"  ✗ [{i:2d}] {query[:50]:50s} → ERROR: {str(e)[:50]}")

    print()
    print("=" * 60)
    print(f"  Intent Accuracy:     {intent_correct}/{total} ({intent_correct/total*100:.1f}%)")
    print(f"  Category Accuracy:   {category_correct}/{total} ({category_correct/total*100:.1f}%)")
    print(f"  Escalation Accuracy: {escalation_correct}/{total} ({escalation_correct/total*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
