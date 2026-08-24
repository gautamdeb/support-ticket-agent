from __future__ import annotations

TEMPLATES = {
    "abusive_content": (
        "Thank you for reaching out. We want to help, but we're not able to "
        "continue while the message contains abusive language. Please resubmit "
        "your request describing the issue respectfully, and a member of our "
        "team will be glad to assist you."
    ),
    "refund_abuse": (
        "Thanks for getting in touch about your refund. Our records show "
        "repeated refund requests on this account, and our policy requires "
        "these to be reviewed by a specialist rather than processed "
        "automatically. We've flagged this for review and someone will follow "
        "up with you directly."
    ),
    "generic_refuse": (
        "Thank you for contacting support. We're unable to action this "
        "particular request through automated support. A member of our team "
        "will review it and get back to you."
    ),
}

def get_refusal(template_key: str) -> str:
    return TEMPLATES.get(template_key, TEMPLATES["generic_refuse"])
