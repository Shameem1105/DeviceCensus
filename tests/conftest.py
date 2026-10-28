import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import Settings, get_settings  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    app.dependency_overrides[get_settings] = lambda: Settings(app_name="devicecensus", environment="test")
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
