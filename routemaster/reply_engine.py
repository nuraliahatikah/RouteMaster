from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from routemaster.knowledge import detect_topics, load_knowledge, relevant_facts

NEGATIVE_SIGNALS = (
    "bad",
    "terrible",
    "awful",
    "disappointed",
    "disappointing",
    "unhappy",
    "frustrat",
    "angry",
    "rude",
    "dirty",
    "smell",
    "noisy",
    "leak",
    "mess",
    "problem",
    "issue",
    "horrible",
    "poor",
    "worst",
)

POSITIVE_SIGNALS = (
    "great",
    "excellent",
    "wonderful",
    "amazing",
    "lovely",
    "perfect",
    "recommend",
    "thank",
    "enjoyed",
    "comfortable",
    "clean",
    "beautiful",
)


@dataclass
class EvaluationResult:
    review_text: str
    sentiment: str
    is_negative: bool
    topics: list[str]
    cited_facts: list[str]
    draft_reply: str


def _extract_rating(review_text: str) -> int | None:
    lowered = review_text.lower()
    for pattern in (r"\b([1-5])\s*/\s*5\b", r"\b([1-5])\s*out of\s*5\b", r"\b([1-5])\s*star"):
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return None


def classify_sentiment(review_text: str) -> tuple[str, bool]:
    lowered = review_text.lower()
    rating = _extract_rating(review_text)

    if rating is not None:
        if rating <= 2:
            return "negative", True
        if rating == 3:
            return "mixed", True
        return "positive", False

    negative_hits = sum(1 for signal in NEGATIVE_SIGNALS if signal in lowered)
    positive_hits = sum(1 for signal in POSITIVE_SIGNALS if signal in lowered)

    if negative_hits > positive_hits and negative_hits > 0:
        return "negative", True
    if negative_hits > 0 and positive_hits > 0:
        return "mixed", True
    if positive_hits > 0:
        return "positive", False
    return "neutral", False


def _opening_for_sentiment(sentiment: str) -> str:
    if sentiment == "negative":
        return (
            "Dear Guest,\n\nThank you for sharing your experience at Mini Homestay Bak. "
            "We are sorry that your stay did not meet your expectations."
        )
    if sentiment == "mixed":
        return (
            "Dear Guest,\n\nThank you for your honest feedback about Mini Homestay Bak. "
            "We appreciate you letting us know what went well and what did not."
        )
    return (
        "Dear Guest,\n\nThank you so much for your kind words about Mini Homestay Bak. "
        "We are delighted you enjoyed your stay in Pontian."
    )


def _facts_to_bullets(facts: list[str]) -> str:
    if not facts:
        return ""
    lines = []
    for fact in facts:
        detail = fact.split(":", 1)[1].strip() if ":" in fact else fact
        lines.append(f"• {detail}")
    return "To clarify our house guidelines:\n" + "\n".join(lines)


def draft_grounded_reply(
    review_text: str,
    sentiment: str,
    cited_facts: list[str],
) -> str:
    parts = [_opening_for_sentiment(sentiment)]
    bullet_block = _facts_to_bullets(cited_facts)
    if bullet_block:
        parts.append(bullet_block)

    if sentiment in {"negative", "mixed"}:
        parts.append(
            "If anything was unclear before your arrival, we will improve how we "
            "communicate these details in future welcome messages."
        )
    else:
        parts.append("We hope to welcome you back whenever your travels bring you to Johor.")

    parts.append("Warm regards,\nMini Homestay Bak Team")
    return "\n\n".join(parts)


def evaluate_review(review_text: str, knowledge_base_path: str) -> EvaluationResult:
    path = Path(knowledge_base_path)
    knowledge_raw = load_knowledge(path) if path.is_file() else ""

    sentiment, is_negative = classify_sentiment(review_text)
    topics = detect_topics(review_text)
    cited_facts = relevant_facts(review_text, knowledge_raw) if knowledge_raw else []
    draft_reply = draft_grounded_reply(review_text, sentiment, cited_facts)

    return EvaluationResult(
        review_text=review_text,
        sentiment=sentiment,
        is_negative=is_negative,
        topics=topics,
        cited_facts=cited_facts,
        draft_reply=draft_reply,
    )
