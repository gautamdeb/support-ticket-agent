from __future__ import annotations

import re

from ..utils.constants import Category
from ..utils.schemas import Ticket

_WEEKS_MONTHS = re.compile(r"\b(\d+\s*)?(week|weeks|month|months)\b", re.IGNORECASE)
_N_DAYS = re.compile(r"\b(\d+)\s*days?\b", re.IGNORECASE)
_LONG_AGO = re.compile(r"\b(last month|a month ago|months ago|weeks ago|long time ago)\b", re.IGNORECASE)

_LOGIN_ESCALATION = [
    "2fa", "two-factor", "two factor", "authenticator", "lost my phone",
    "new phone", "identity", "change my email", "change the email",
    "change it to my new email", "old work email", "no longer access",
    "can no longer access", "can't access my email", "cant access my email",
]

def _refund_outside_window(text: str) -> bool:
    if _LONG_AGO.search(text) or _WEEKS_MONTHS.search(text):
        return True
    m = _N_DAYS.search(text)
    if m and int(m.group(1)) > 7:
        return True
    return False

def requires_human(category: str, ticket: Ticket) -> tuple[bool, str]:
    """Return (requires_escalation, reason) from documented policy triggers."""
    text = f"{ticket.subject} {ticket.message}".lower()

    if category == Category.REFUND_REQUEST.value and _refund_outside_window(text):
        return True, "Refund requested outside the 7-day window (refund_policy.md)."

    if category == Category.LOGIN_ACCOUNT_ACCESS.value:
        for kw in _LOGIN_ESCALATION:
            if kw in text:
                return True, "Requires identity verification (account_access_faq.md)."

    return False, ""
