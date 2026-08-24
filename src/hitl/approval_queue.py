from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ..utils.helpers import app_config, project_path, read_json, write_json
from ..utils.schemas import DraftReply

def _queue_path() -> Path:
    return project_path(app_config()["hitl"]["queue_file"])

class ApprovalQueue:
    def __init__(self) -> None:
        self.path = _queue_path()
        self._items: list[dict[str, Any]] = []
        if self.path.exists():
            try:
                self._items = read_json(self.path)
            except Exception:
                self._items = []

    def enqueue(self, draft: DraftReply) -> None:
        record = draft.model_dump()
        self._items = [i for i in self._items if i.get("ticket_id") != draft.ticket_id]
        self._items.append(record)
        self._persist()

    def list_pending(self) -> list[dict[str, Any]]:
        return [i for i in self._items if i.get("status") == "PENDING_REVIEW"]

    def all(self) -> list[dict[str, Any]]:
        return list(self._items)

    def get(self, ticket_id: str) -> Optional[dict[str, Any]]:
        for i in self._items:
            if i.get("ticket_id") == ticket_id:
                return i
        return None

    def update(self, record: dict[str, Any]) -> None:
        for idx, i in enumerate(self._items):
            if i.get("ticket_id") == record.get("ticket_id"):
                self._items[idx] = record
                break
        self._persist()

    def _persist(self) -> None:
        write_json(self.path, self._items)
