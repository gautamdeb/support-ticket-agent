"""Load Markdown knowledge-base documents."""
from __future__ import annotations

from pathlib import Path

from ..utils.helpers import app_config, project_path

def kb_dir() -> Path:
    return project_path(app_config()["paths"]["knowledge_base"])

def load_documents() -> list[dict]:
    """Return [{'source': filename, 'text': markdown}] for every KB .md file."""
    docs: list[dict] = []
    for md in sorted(kb_dir().glob("*.md")):
        docs.append({"source": md.name, "text": md.read_text(encoding="utf-8")})
    return docs
