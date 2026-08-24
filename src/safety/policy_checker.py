from __future__ import annotations

import re

from ..retrieval.document_loader import kb_dir
from ..utils.constants import CATEGORY_TO_POLICY_FILES, Category
from ..utils.schemas import PolicyCheckResult, RetrievedChunk, Ticket

_TIME_HINTS = re.compile(
    r"\b(yesterday|today|hour|hours|day|days|week|weeks|month|months|ago|"
    r"just now|recently|renew|renewed|charged on|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)

def check_policy_support(category: str, retrieved: list[RetrievedChunk]) -> tuple[bool, list[str]]:
    """Is there a governing policy for this ticket in the KB?"""
    expected_files = CATEGORY_TO_POLICY_FILES.get(category)
    if not expected_files:
        return False, []
    existing = [f for f in expected_files if (kb_dir() / f).exists()]
    if not existing:
        return False, []
    retrieved_sources = {r.source for r in retrieved}
    matched = [f for f in existing if f in retrieved_sources] or existing
    return True, matched

def check_missing_info(category: str, ticket: Ticket) -> tuple[bool, list[str]]:
    msg = f"{ticket.subject} {ticket.message}".strip()
    body_words = re.findall(r"\w+", ticket.message)

    if len(body_words) <= 5 and category in {
        Category.PRODUCT_TROUBLESHOOTING.value, Category.UNKNOWN.value
    }:
        return True, [
            "What exactly is happening (the error message or the screen you see)?",
            "Which part of the product and which browser/device are you using?",
            "When did it start?",
        ]

    if category == Category.REFUND_REQUEST.value and not _TIME_HINTS.search(msg):
        return True, [
            "When were you billed (the date or how many days ago)?",
            "Which plan is this for?",
            "Have you used the product since that charge?",
        ]

    return False, []

def run_policy_check(category: str, ticket: Ticket,
                     retrieved: list[RetrievedChunk]) -> PolicyCheckResult:
    supported, matched = check_policy_support(category, retrieved)
    missing, prompts = check_missing_info(category, ticket)
    rationale_parts = []
    rationale_parts.append(
        f"Matched policy files: {matched}" if supported
        else "No supporting policy chunk found in the KB."
    )
    if missing:
        rationale_parts.append("Ticket is missing information required to act.")
    return PolicyCheckResult(
        policy_supported=supported,
        matched_policies=matched,
        missing_required_info=missing,
        missing_info_prompts=prompts,
        rationale=" ".join(rationale_parts),
    )
