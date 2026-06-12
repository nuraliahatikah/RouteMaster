from __future__ import annotations
import os
import re
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    review_text: str
    sentiment: str
    is_negative: bool
    topics: list[str]
    cited_facts: list[str]
    draft_reply: str

NEGATIVE_SIGNALS = ("bad", "terrible", "awful", "disappointed", "disappointing", "unhappy", "frustrat", "angry", "rude", "dirty", "smell", "noisy", "leak", "mess", "park", "car", "spot")

def evaluate_review(review_text: str, knowledge_base_path: str) -> EvaluationResult:
    review_lower = review_text.lower()
    is_negative = any(signal in review_lower for signal in NEGATIVE_SIGNALS)
    sentiment = "negative" if is_negative else "positive"
    
    # Isolate topics dynamically
    topics = []
    if "park" in review_lower or "car" in review_lower:
        topics.append("parking")
    if "trash" in review_lower or "leak" in review_lower or "mess" in review_lower:
        topics.append("trash_disposal")
    if not topics:
        topics.append("general")

    # Load local ground-truth files
    cited_facts = []
    if os.path.exists(knowledge_base_path):
        with open(knowledge_base_path, "r", encoding="utf-8") as f:
            facts = f.readlines()
        for fact in facts:
            fact_clean = fact.strip()
            if not fact_clean or fact_clean.startswith("PROPERTY:"):
                continue
            if "parking" in topics[0] and "PARKING" in fact_clean:
                cited_facts.append(fact_clean)
            elif "trash" in topics[0] and "TRASH" in fact_clean:
                cited_facts.append(fact_clean)

    # Draft structured grounded replies
    if is_negative:
        facts_context = " ".join(cited_facts)
        draft_reply = (
            f"Dear Guest,\n\nThank you for sharing your feedback. We sincerely apologize for the inconvenience during your stay. "
            f"Regarding the layout issue noticed: {facts_context or 'We have updated our internal logs to inspect our operations.'} "
            f"We hope to have the chance to host you better in the future.\n\nWarm regards,\nManagement Team"
        )
    else:
        draft_reply = (
            "Dear Guest,\n\nThank you so much for the wonderful review! We are delighted to hear you had a fantastic stay at our homestay. "
            "We look forward to hosting you again!\n\nWarm regards,\nManagement Team"
        )

    return EvaluationResult(
        review_text=review_text,
        sentiment=sentiment,
        is_negative=is_negative,
        topics=topics,
        cited_facts=cited_facts,
        draft_reply=draft_reply
    )