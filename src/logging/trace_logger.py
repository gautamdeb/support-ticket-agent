from __future__ import annotations

import time
from typing import Any

class TraceLogger:
    """Collects ordered (step, detail) events for a single ticket run."""

    def __init__(self, ticket_id: str) -> None:
        self.ticket_id = ticket_id
        self.events: list[dict[str, Any]] = []
        self._t0 = time.time()

    def log(self, node: str, action: str, detail: Any = None) -> None:
        self.events.append(
            {
                "t_ms": round((time.time() - self._t0) * 1000, 1),
                "node": node,
                "action": action,
                "detail": detail,
            }
        )

    def as_list(self) -> list[dict[str, Any]]:
        return list(self.events)

    def pretty(self) -> str:
        lines = [f"TRACE for {self.ticket_id}:"]
        for e in self.events:
            detail = "" if e["detail"] is None else f" :: {e['detail']}"
            lines.append(f"  [{e['t_ms']:>7} ms] {e['node']} -> {e['action']}{detail}")
        return "\n".join(lines)
