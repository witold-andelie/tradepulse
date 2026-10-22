import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    def _read(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")
    return _read


@pytest.fixture
def fixture_json(fixture_text):
    def _read(name: str) -> dict:
        return json.loads(fixture_text(name))
    return _read
