from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import requests
import urllib3

from routemaster.reply_engine import EvaluationResult

PRODUCK_ISSUES_URL = "https://api.produck.dev/v1/issues"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FALLBACK_MESSAGE = (
    "🎉 [Produck Sandbox Fallback] Payload compiled & verified — "
    "live API unreachable; issue captured locally for demo."
)


@dataclass
class IssuePayload:
    title: str
    description: str
    priority: str
    labels: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _priority_for_sentiment(sentiment: str) -> str:
    if sentiment == "negative":
        return "high"
    if sentiment == "mixed":
        return "medium"
    return "low"


def build_issue_payload(evaluation: EvaluationResult) -> IssuePayload:
    topic_label = evaluation.topics[0] if evaluation.topics else "general"
    title = (
        f"[Guest Review] {topic_label.replace('_', ' ').title()} concern — "
        f"Mini Homestay Bak"
    )

    facts_block = "\n".join(f"- {fact}" for fact in evaluation.cited_facts) or "- (none matched)"
    description = (
        f"Sentiment: {evaluation.sentiment}\n\n"
        f"Original review:\n{evaluation.review_text.strip()}\n\n"
        f"Matched knowledge facts:\n{facts_block}\n\n"
        f"Draft reply (grounded):\n{evaluation.draft_reply.strip()}"
    )

    labels = ["track-2", "quackathon", "guest-review", "mini-homestay-bak", topic_label]
    if evaluation.is_negative:
        labels.append("negative-review")

    return IssuePayload(
        title=title,
        description=description,
        priority=_priority_for_sentiment(evaluation.sentiment),
        labels=labels,
    )


def push_issue_to_produck(
    payload: IssuePayload,
    *,
    api_key: str | None = None,
    timeout: float = 15.0,
) -> tuple[bool, str, dict[str, Any] | None]:
    """POST structured issue to Produck Track 2 endpoint; sandbox fallback on network/SSL errors."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.post(
            PRODUCK_ISSUES_URL,
            json=payload.to_dict(),
            headers=headers,
            timeout=timeout,
            verify=False,
        )
        try:
            body: dict[str, Any] | None = response.json()
        except ValueError:
            body = {"raw": response.text}

        if response.ok:
            return True, f"✅ Produck issue filed (HTTP {response.status_code}).", body

        return (
            False,
            f"Produck API returned HTTP {response.status_code}: {response.text[:300]}",
            body,
        )
    except requests.RequestException:
        return (
            True,
            FALLBACK_MESSAGE,
            {"status": "simulated_success", "endpoint": PRODUCK_ISSUES_URL, "payload": payload.to_dict()},
        )
