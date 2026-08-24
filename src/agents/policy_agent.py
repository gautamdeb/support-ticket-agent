from __future__ import annotations

from ..safety.policy_checker import run_policy_check
from ..utils.schemas import PolicyCheckResult, RetrievedChunk, Ticket

def check_policy(category: str, ticket: Ticket,
                 retrieved: list[RetrievedChunk]) -> PolicyCheckResult:
    return run_policy_check(category, ticket, retrieved)
