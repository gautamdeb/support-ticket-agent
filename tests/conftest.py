import os
import sys
from pathlib import Path

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDINGS_PROVIDER", "mock")
os.environ.setdefault("VECTOR_STORE", "memory")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from src.utils.helpers import app_config, project_path, read_json
from src.utils.schemas import Ticket

@pytest.fixture(scope="session")
def tickets():
    return [Ticket(**t) for t in read_json(project_path(app_config()["paths"]["tickets"]))]

@pytest.fixture(scope="session")
def expected_routes():
    return read_json(project_path(app_config()["paths"]["expected_routes"]))

@pytest.fixture(scope="session")
def pipeline_results(tickets):
    from src.main import run_pipeline
    return run_pipeline(tickets, review_mode="auto", verbose=False)
