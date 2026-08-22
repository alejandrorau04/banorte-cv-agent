import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def schema() -> dict:
    return json.loads((ROOT / "docs" / "contract" / "openapi.json").read_text())


@pytest.fixture(scope="session")
def facts():
    from app.core.corpus import load_facts
    return load_facts()


class FakeLLM:
    """Sustituye al proveedor. Los tests deben ser deterministas y no gastar cuota."""
    def __init__(self, text: str = "Respuesta [profile.headline]."):
        self.text = text
        self.calls = 0

    async def complete(self, system: str, user: str):
        from app.adapters.base import Completion
        self.calls += 1
        return Completion(text=self.text, model="fake",
                          usage={"input_tokens": 10, "output_tokens": 5,
                                 "reasoning_tokens": 0, "total_tokens": 15})


@pytest.fixture
def fake_llm():
    return FakeLLM
