import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from src import ai_client
from src.providers import Provider, ProviderError

REPO_ROOT = Path(__file__).resolve().parents[1]


class _FakeProvider(Provider):
    name = "fake"
    default_model = "fake-1"

    def __init__(self, text="", exception=None):
        super().__init__()
        self._text = text
        self._exception = exception

    async def generate(self, prompt):
        if self._exception:
            raise self._exception
        return self._text


def generate(text):
    return asyncio.run(ai_client._generate_session("prompt", "quizzes", _FakeProvider(text=text)))


def test_env_is_loaded_independently_of_import_order(tmp_path):
    """Regression test: importar src.ai_client direto (sem src.config ter
    rodado antes) precisa achar as chaves do .env mesmo assim.
    """
    (tmp_path / ".env").write_text("GEMINI_API_KEY=test-key-not-real\n")

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "AI_PROVIDER"):
        env.pop(key, None)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from src.ai_client import provider_ready; ready, reason = provider_ready(); assert ready, reason",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_generate_session_extracts_items_by_response_key():
    assert generate(json.dumps({"quizzes": [{"a": 1}]})) == [{"a": 1}]


def test_generate_session_accepts_a_bare_list():
    assert generate(json.dumps([{"a": 1}])) == [{"a": 1}]


def test_generate_session_raises_friendly_error_on_malformed_json():
    """Regression test: pedir JSON ao modelo não garante JSON bem formado;
    uma resposta truncada não pode vazar como json.JSONDecodeError."""
    with pytest.raises(ValueError, match="formato inválido"):
        generate("{not valid json")


def test_provider_errors_reach_the_caller_untouched():
    provider = _FakeProvider(exception=ProviderError("O gemini/x demorou demais para responder."))
    with pytest.raises(ValueError, match="demorou demais"):
        asyncio.run(ai_client._generate_session("prompt", "quizzes", provider))


# --- tolerância ao que modelos menores devolvem ----------------------------

def test_strips_markdown_fences():
    assert generate('```json\n{"quizzes": [{"a": 1}]}\n```') == [{"a": 1}]


def test_recovers_json_wrapped_in_prose():
    """gemma/qwen às vezes narram antes do JSON mesmo com format=json."""
    assert generate('Here is the JSON you asked for:\n{"quizzes": [{"a": 1}]}\nHope it helps!') == [{"a": 1}]


def test_recovers_when_the_model_renames_the_list_key():
    """Se só existe uma lista no objeto, ela é a resposta — melhor do que
    descartar a sessão inteira por causa do nome da chave."""
    assert generate(json.dumps({"quiz": [{"a": 1}]})) == [{"a": 1}]


def test_recovers_a_single_item_returned_outside_a_list():
    item = {"question": "Which one fits?", "options": ["a", "b", "c", "d"]}
    assert generate(json.dumps(item)) == [item]


def test_ambiguous_response_still_fails_loudly():
    with pytest.raises(ValueError, match="Formato inesperado"):
        generate(json.dumps({"quizzes": None, "extras": None}))


def test_two_lists_without_the_expected_key_is_not_guessed():
    with pytest.raises(ValueError, match="Formato inesperado"):
        generate(json.dumps({"a": [{"x": 1}], "b": [{"y": 2}]}))
