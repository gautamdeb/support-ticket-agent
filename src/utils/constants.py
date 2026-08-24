from __future__ import annotations

from enum import Enum

class Route(str, Enum):
    """The four actions the agent may decide on."""

    AUTO_RESOLVE = "AUTO_RESOLVE"
    ESCALATE = "ESCALATE"
    REFUSE = "REFUSE"
    ASK_MORE_INFO = "ASK_MORE_INFO"

    @classmethod
    def values(cls) -> list[str]:
        return [r.value for r in cls]

class Category(str, Enum):
    """Ticket categories."""

    REFUND_REQUEST = "refund_request"
    SUBSCRIPTION_CANCELLATION = "subscription_cancellation"
    LOGIN_ACCOUNT_ACCESS = "login_account_access"
    PRODUCT_TROUBLESHOOTING = "product_troubleshooting"
    ABUSIVE_MESSAGE = "abusive_message"
    UNKNOWN = "unknown"

class ReviewerAction(str, Enum):
    """Human-in-the-loop reviewer actions."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    EDIT = "EDIT"
    REQUEST_REGENERATION = "REQUEST_REGENERATION"
    ESCALATE = "ESCALATE"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ABUSIVE = "abusive"

CATEGORY_TO_POLICY_FILES: dict[str, list[str]] = {
    Category.REFUND_REQUEST.value: ["refund_policy.md"],
    Category.SUBSCRIPTION_CANCELLATION.value: ["subscription_policy.md"],
    Category.LOGIN_ACCOUNT_ACCESS.value: ["account_access_faq.md"],
    Category.PRODUCT_TROUBLESHOOTING.value: ["troubleshooting_faq.md"],
    Category.ABUSIVE_MESSAGE.value: ["abusive_content_policy.md"],
}

AUTO_SEND_ALLOWED = False
