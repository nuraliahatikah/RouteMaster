from __future__ import annotations

from pathlib import Path

DEFAULT_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parent.parent / "property_data" / "local_knowledge.txt"
)

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "parking": (
        "parking",
        "park",
        "car",
        "cars",
        "vehicle",
        "driveway",
        "gate",
        "curb",
        "street",
    ),
    "trash": (
        "trash",
        "rubbish",
        "garbage",
        "waste",
        "bin",
        "smell",
        "leak",
        "kitchen",
        "bag",
        "seal",
    ),
    "checkout": (
        "checkout",
        "check out",
        "check-out",
        "leave",
        "departure",
        "late",
        "11",
        "morning",
    ),
    "checkin": (
        "check in",
        "check-in",
        "checkin",
        "arrival",
        "early",
        "3 pm",
        "15:00",
    ),
    "wifi": ("wifi", "wi-fi", "internet", "connection", "network"),
    "noise": ("noise", "quiet", "loud", "neighbor", "neighbour"),
}


def load_knowledge(path: Path | None = None) -> str:
    knowledge_path = path or DEFAULT_KNOWLEDGE_PATH
    return knowledge_path.read_text(encoding="utf-8")


def parse_sections(raw: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_key = "GENERAL"
    sections[current_key] = []

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current_key = stripped[1:-1]
            sections.setdefault(current_key, [])
            continue
        if not stripped or stripped.startswith("#"):
            continue
        sections.setdefault(current_key, []).append(stripped)

    return sections


def detect_topics(review_text: str) -> list[str]:
    lowered = review_text.lower()
    matched = [
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    return matched or ["general"]


def section_for_topic(topic: str) -> str | None:
    mapping = {
        "parking": "PARKING",
        "trash": "TRASH_DISPOSAL",
        "checkout": "CHECK_IN_CHECK_OUT",
        "checkin": "CHECK_IN_CHECK_OUT",
        "wifi": "AMENITIES",
        "noise": "HOUSE_RULES",
        "general": "COMMON_GUEST_CONCERNS",
    }
    return mapping.get(topic)


def relevant_facts(review_text: str, knowledge_raw: str) -> list[str]:
    sections = parse_sections(knowledge_raw)
    topics = detect_topics(review_text)
    facts: list[str] = []

    for topic in topics:
        section_key = section_for_topic(topic)
        if section_key and section_key in sections:
            facts.extend(sections[section_key])

    if not facts and "COMMON_GUEST_CONCERNS" in sections:
        facts.extend(sections["COMMON_GUEST_CONCERNS"])

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_facts: list[str] = []
    for fact in facts:
        if fact not in seen:
            seen.add(fact)
            unique_facts.append(fact)
    return unique_facts
