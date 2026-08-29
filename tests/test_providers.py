"""Testes da camada de provedores.

Nenhum deles vai à rede: httpx.MockTransport intercepta o POST e devolve a
resposta que o teste quiser, inclusive erros.
"""

import asyncio

import httpx
import pytest

from src import providers
from src.providers import (
    AnthropicProvider,
    OpenRouterProvider,
    CustomProvider,
    GroqProvider,
    OllamaProvider,
    ProviderError,
    available_providers,
    get_provider,
)


@pytest.fixture
def capture(monkeypatch):
    """Intercepta as requisições e devolve a lista do que foi enviado."""
    sent: list[httpx.Request] = []
    state = {"response": httpx.Response(200, json={})}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return state["response"]

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return type("Capture", (), {"sent": sent, "state": state})


def respond(capture, response):
    capture.state["response"] = response


# --- OpenAI-compatible (Groq e afins) --------------------------------------

def test_groq_sends_the_prompt_in_json_mode(capture):
    respond(capture, httpx.Response(200, json={"choices": [{"message": {"content": '{"quizzes": []}'}}]}))

    text = asyncio.run(GroqProvider(model="openai/gpt-oss-20b").generate("prompt aqui"))

    request = capture.sent[0]
    body = httpx.Response(200, content=request.content).json()
    assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
    assert body["response_format"] == {"type": "json_object"}
    assert body["messages"][0]["content"] == "prompt aqui"
    assert text == '{"quizzes": []}'


def test_openai_compatible_request_caps_the_output_length(capture):
    """Sem max_tokens a Groq trunca uma sessão de 5 exercícios e, no modo JSON,
    descarta a resposta inteira com 400."""
    respond(capture, httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]}))

    asyncio.run(GroqProvider().generate("prompt"))

    body = httpx.Response(200, content=capture.sent[0].content).json()
    assert body["max_tokens"] >= 4096


def test_retries_without_max_tokens_when_the_server_rejects_it(monkeypatch):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(400, json={"error": {"message": "max_tokens is too large"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: original(*a, **{**k, "transport": transport}))

    assert asyncio.run(GroqProvider().generate("prompt")) == "{}"
    assert calls["n"] == 2


def test_error_message_surfaces_the_real_cause_not_the_generic_one(capture):
    """A Groq deixa `message` genérica e põe a causa em `failed_generation`."""
    respond(
        capture,
        httpx.Response(
            400,
            json={
                "error": {
                    "message": "Failed to generate JSON. Please adjust your prompt.",
                    "failed_generation": "max completion tokens reached before generating a valid document",
                }
            },
        ),
    )

    with pytest.raises(ProviderError, match="max completion tokens reached"):
        asyncio.run(GroqProvider().generate("prompt"))


def test_rate_limit_message_says_when_the_quota_comes_back(capture):
    """Sem os headers a mensagem só diz 'tente mais tarde' — inútil para
    decidir entre esperar e trocar de provedor."""
    respond(
        capture,
        httpx.Response(
            429,
            json={"error": {"message": "Rate limit reached"}},
            headers={"x-ratelimit-reset-tokens": "7.66s", "retry-after": "8"},
        ),
    )

    with pytest.raises(ProviderError) as exc:
        asyncio.run(GroqProvider().generate("prompt"))

    assert "429" in str(exc.value)
    assert "8s" in str(exc.value)
    assert "7.66s" in str(exc.value)


def test_bad_credentials_name_the_env_var_to_fix(capture):
    respond(capture, httpx.Response(401, json={"error": {"message": "Invalid API Key"}}))

    with pytest.raises(ProviderError, match="GROQ_API_KEY"):
        asyncio.run(GroqProvider().generate("prompt"))


def test_falls_back_when_the_server_rejects_json_mode(monkeypatch):
    """Servidores compatíveis mais antigos não conhecem response_format;
    perder a sessão por causa disso seria desnecessário."""
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(400, json={"error": {"message": "response_format is not supported"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: original(*a, **{**k, "transport": transport}))

    assert asyncio.run(GroqProvider().generate("prompt")) == "{}"
    assert calls["n"] == 2


def test_upstream_error_inside_a_200_body_is_surfaced(capture):
    """O OpenRouter devolve o erro do provedor de baixo no corpo, às vezes com
    HTTP 200; reportar 'resposta vazia' esconderia o motivo real."""
    respond(
        capture,
        httpx.Response(
            200,
            json={
                "error": {
                    "message": "Provider returned error",
                    "code": 429,
                    "metadata": {
                        "raw": "z-ai/glm-5.2:free is temporarily rate-limited upstream.",
                        "retry_after_seconds": 5,
                    },
                }
            },
        ),
    )

    with pytest.raises(ProviderError) as exc:
        asyncio.run(OpenRouterProvider(model="z-ai/glm-5.2:free").generate("prompt"))

    assert "rate-limited upstream" in str(exc.value)
    assert "5s" in str(exc.value)


def test_openrouter_identifies_the_app(capture):
    respond(capture, httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]}))

    asyncio.run(OpenRouterProvider().generate("prompt"))

    assert capture.sent[0].headers["x-title"] == "UniversePie"


def test_empty_choices_is_reported_instead_of_indexing_error(capture):
    respond(capture, httpx.Response(200, json={"choices": []}))

    with pytest.raises(ProviderError, match="sem nenhuma escolha"):
        asyncio.run(GroqProvider().generate("prompt"))


# --- Ollama ----------------------------------------------------------------

def test_ollama_forces_json_and_widens_the_context(capture):
    """O pool inteiro passa de 4k tokens (padrão do Ollama); sem num_ctx o
    começo do prompt é truncado sem aviso."""
    respond(capture, httpx.Response(200, json={"message": {"content": '{"quizzes": []}'}}))

    asyncio.run(OllamaProvider(model="gemma4:e4b").generate("prompt"))

    body = httpx.Response(200, content=capture.sent[0].content).json()
    assert str(capture.sent[0].url).endswith("/api/chat")
    assert body["format"] == "json"
    assert body["stream"] is False
    assert body["options"]["num_ctx"] >= 8192


def test_ollama_turns_reasoning_off(capture):
    """qwen3 e gemma4 raciocinam por padrão e gastam quase todo o tempo nisso;
    a saída aqui é JSON de esquema fixo."""
    respond(capture, httpx.Response(200, json={"message": {"content": "{}"}}))

    asyncio.run(OllamaProvider(model="qwen3:8b").generate("prompt"))

    body = httpx.Response(200, content=capture.sent[0].content).json()
    assert body["think"] is False


def test_ollama_retries_without_the_think_field_when_the_model_rejects_it(monkeypatch):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(400, json={"error": "model does not support thinking"})
        return httpx.Response(200, json={"message": {"content": "{}"}})

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: original(*a, **{**k, "transport": transport}))

    assert asyncio.run(OllamaProvider().generate("prompt")) == "{}"
    assert calls["n"] == 2


def test_ollama_offline_says_how_to_start_it(monkeypatch):
    original = httpx.AsyncClient

    def failing(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(httpx.ConnectError("refused"))
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", failing)

    with pytest.raises(ProviderError, match="ollama serve"):
        asyncio.run(OllamaProvider().generate("prompt"))


def test_ollama_needs_no_api_key():
    ready, reason = OllamaProvider().ready()
    assert ready and reason == ""


# --- Anthropic -------------------------------------------------------------

def test_anthropic_prefills_the_opening_brace(capture):
    """A API não tem modo JSON: o prefill evita o 'Here is the JSON:'."""
    respond(capture, httpx.Response(200, json={"content": [{"type": "text", "text": '"quizzes": []}'}]}))

    text = asyncio.run(AnthropicProvider(model="claude-sonnet-5").generate("prompt"))

    body = httpx.Response(200, content=capture.sent[0].content).json()
    assert body["messages"][-1] == {"role": "assistant", "content": "{"}
    assert capture.sent[0].headers["anthropic-version"] == "2023-06-01"
    assert text == '{"quizzes": []}'


# --- registro --------------------------------------------------------------

def test_unknown_provider_lists_the_valid_ones():
    with pytest.raises(ProviderError) as exc:
        get_provider("gpt5-turbo-ultra")
    assert "ollama" in str(exc.value) and "groq" in str(exc.value)


def test_registry_covers_the_documented_providers():
    assert {"gemini", "groq", "ollama", "anthropic", "custom"} <= set(available_providers())


def test_ai_model_does_not_leak_across_providers(monkeypatch):
    """AI_MODEL descreve o provedor configurado; aplicá-lo a outro passaria
    um nome de modelo que não existe lá."""
    monkeypatch.setattr(providers, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(providers, "AI_MODEL", "gemini-2.5-flash")

    assert get_provider("gemini").model == "gemini-2.5-flash"
    assert get_provider("ollama").model == OllamaProvider.default_model
    assert get_provider("ollama", model="qwen3:8b").model == "qwen3:8b"


def test_custom_provider_requires_a_base_url(monkeypatch):
    monkeypatch.setattr(providers, "AI_BASE_URL", "")
    ready, reason = CustomProvider().ready()
    assert not ready and "AI_BASE_URL" in reason


def test_missing_key_is_reported_before_any_request():
    monkeypatched = GroqProvider()
    import os

    key = os.environ.pop("GROQ_API_KEY", None)
    try:
        ready, reason = monkeypatched.ready()
        assert not ready and "GROQ_API_KEY" in reason
    finally:
        if key is not None:
            os.environ["GROQ_API_KEY"] = key
