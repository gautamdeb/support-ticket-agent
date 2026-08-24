from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..utils.helpers import app_config, project_path, read_json, write_json

def _store_path() -> Path:
    return project_path(app_config()["memory"]["store_file"])

class CustomerThreadStore:
    def __init__(self) -> None:
        self.path = _store_path()
        self._data: dict[str, list[dict[str, Any]]] = {}
        if self.path.exists():
            try:
                self._data = read_json(self.path)
            except Exception:
                self._data = {}

    def get_thread(self, customer_id: str) -> list[dict[str, Any]]:
        return self._data.get(customer_id, [])

    def record_interaction(self, customer_id: str, ticket_id: str,
                           category: str, summary: str) -> None:
        entry = {
            "ticket_id": ticket_id,
            "category": category,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        thread = self._data.setdefault(customer_id, [])
        for i, e in enumerate(thread):
            if e.get("ticket_id") == ticket_id:
                thread[i] = entry
                break
        else:
            thread.append(entry)
        self._persist()

    def count_recent_by_category(self, customer_id: str, category: str,
                                 within_days: int = 90) -> int:
        cutoff = datetime.now(timezone.utc).timestamp() - within_days * 86400
        n = 0
        for e in self._data.get(customer_id, []):
            if e.get("category") != category:
                continue
            try:
                ts = datetime.fromisoformat(e["timestamp"]).timestamp()
            except Exception:
                continue
            if ts >= cutoff:
                n += 1
        return n

    def _persist(self) -> None:
        write_json(self.path, self._data)
