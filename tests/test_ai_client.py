import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from src import ai_client

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ai_client_loads_env_independently_of_import_order(tmp_path):
    """Regression test: importing src.ai_client directly (without src.config
    having run first) must still find GEMINI_API_KEY from a .env file.
    """
    (tmp_path / ".env").write_text("GEMINI_API_KEY=test-key-not-real\n")

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    env.pop("GEMINI_API_KEY", None)
    env.pop("GOOGLE_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "-c", "from src.ai_client import ai_client; assert ai_client is not None"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    async def generate_content(self, **kwargs):
        if self._exception:
            raise self._exception
        return self._response


class _FakeClient:
    def __init__(self, models):
        self.aio = type("_FakeAio", (), {"models": models})()


def test_generate_session_raises_friendly_error_on_timeout(monkeypatch):
    """Regression test: a Gemini call that times out must surface a
    user-facing message, not hang forever (no timeout was set before) or
    leak a raw httpx exception.
    """
    fake_client = _FakeClient(_FakeModels(exception=httpx.ReadTimeout("timed out")))
    monkeypatch.setattr(ai_client, "ai_client", fake_client)

    with pytest.raises(ValueError, match="demorou demais"):
        asyncio.run(ai_client._generate_session("prompt", "quizzes"))


def test_generate_session_raises_friendly_error_when_text_is_none(monkeypatch):
    """Regression test: response.text can be None when Gemini's safety
    filters block the output; that must not surface as a raw TypeError from
    json.loads(None).
    """
    fake_client = _FakeClient(_FakeModels(response=_FakeResponse(text=None)))
    monkeypatch.setattr(ai_client, "ai_client", fake_client)

    with pytest.raises(ValueError, match="filtros de segurança"):
        asyncio.run(ai_client._generate_session("prompt", "quizzes"))


def test_generate_session_extracts_items_by_response_key(monkeypatch):
    fake_client = _FakeClient(
        _FakeModels(response=_FakeResponse(text=json.dumps({"quizzes": [{"a": 1}]})))
    )
    monkeypatch.setattr(ai_client, "ai_client", fake_client)

    result = asyncio.run(ai_client._generate_session("prompt", "quizzes"))

    assert result == [{"a": 1}]
