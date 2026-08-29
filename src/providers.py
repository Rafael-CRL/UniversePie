"""Camada de provedores de IA.

O app nasceu preso ao Gemini, e isso atrapalha de dois jeitos concretos: o
rate limit do tier gratuito trava qualquer sessão de auditoria mais longa, e
medir a qualidade do gerador com um único modelo não separa o que é problema
do prompt do que é limitação do modelo. Aqui todo provedor expõe a mesma
interface — recebe um prompt, devolve texto que se espera ser JSON — e a
escolha vira configuração (`AI_PROVIDER` / `AI_MODEL`), não código.

Provedores compatíveis com a API da OpenAI (Groq, DeepSeek, Kimi, Z.ai,
OpenRouter, servidores locais tipo vLLM ou llama.cpp) compartilham uma única
implementação. Gemini, Anthropic e Ollama têm formatos próprios.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import httpx

from .config import AI_BASE_URL, AI_MODEL, AI_PROVIDER, AI_TIMEOUT_S, OLLAMA_BASE_URL


class ProviderError(ValueError):
    """Erro já formatado para chegar ao usuário final.

    Herda de ValueError porque `services.run_session` converte qualquer
    exceção em HTTP 500 usando a mensagem — o texto precisa ser acionável.
    """


class Provider(ABC):
    name: str = ""
    default_model: str = ""
    api_key_env: str | None = None
    default_timeout_s: float = AI_TIMEOUT_S
    base_url: str = ""

    def __init__(self, model: str | None = None, timeout_s: float | None = None):
        self.model = (model or self.default_model).strip()
        self.timeout_s = timeout_s or self.default_timeout_s

    # -- identidade e configuração ----------------------------------------

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env, "").strip() if self.api_key_env else ""

    def ready(self) -> tuple[bool, str]:
        """(usável?, o que fazer se não estiver)."""
        if self.api_key_env and not self.api_key:
            return False, f"Provedor '{self.name}' selecionado, mas {self.api_key_env} não está definida no .env."
        return True, ""

    @property
    def label(self) -> str:
        return f"{self.name}/{self.model}"

    # -- geração ------------------------------------------------------------

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Devolve o texto cru da resposta. A extração do JSON é do ai_client."""

    async def _post(self, url: str, body: dict, headers: dict | None = None) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.post(url, json=body, headers=headers or {})
        except httpx.ConnectError as exc:
            raise ProviderError(self.connect_error_message()) from exc
        except httpx.TimeoutException as exc:
            raise ProviderError(
                f"{self.label} demorou demais para responder (limite de {self.timeout_s:.0f}s). "
                "Tente de novo, use um modelo menor ou aumente AI_TIMEOUT_S."
            ) from exc

        if response.status_code >= 400:
            raise ProviderError(self.http_error_message(response))
        return response

    def connect_error_message(self) -> str:
        return f"Não foi possível conectar ao provedor '{self.name}' ({self.base_url})."

    def http_error_message(self, response: httpx.Response) -> str:
        status = response.status_code
        detail = self._error_detail(response)

        if status in (401, 403):
            key = self.api_key_env or "a credencial"
            return f"{self.label} recusou a credencial (HTTP {status}). Verifique {key}. {detail}".strip()
        if status == 404:
            return f"{self.label}: modelo ou rota inexistente (HTTP 404). Confira o nome do modelo. {detail}".strip()
        if status == 429:
            return f"{self.label}: rate limit atingido (HTTP 429).{self._rate_limit_hint(response)} {detail}".strip()
        return f"{self.label} respondeu HTTP {status}. {detail}".strip()

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except Exception:
            return (response.text or "")[:200]
        error = payload.get("error", payload)
        if not isinstance(error, dict):
            return str(error)[:300]

        detail = str(error.get("message", ""))[:300]
        # A Groq põe a causa real aqui e deixa `message` genérica ("Failed to
        # generate JSON. Please adjust your prompt.").
        failed = str(error.get("failed_generation", ""))
        if failed and len(failed) < 200:
            detail = f"{detail} [{failed}]".strip()
        return detail

    @staticmethod
    def _rate_limit_hint(response: httpx.Response) -> str:
        """Groq e afins devolvem quando a cota volta; sem isso a mensagem
        manda 'tentar mais tarde' sem dizer quando."""
        parts = []
        for header, label in (
            ("retry-after", "tente de novo em {}s"),
            ("x-ratelimit-reset-requests", "requisições liberam em {}"),
            ("x-ratelimit-reset-tokens", "tokens liberam em {}"),
        ):
            value = response.headers.get(header)
            if value:
                parts.append(label.format(value))
        return f" ({'; '.join(parts)})" if parts else ""


# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------

class GeminiProvider(Provider):
    name = "gemini"
    default_model = "gemini-2.5-flash"
    api_key_env = "GEMINI_API_KEY"

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            from google import genai

            try:
                cls._client = genai.Client()
            except Exception as exc:
                raise ProviderError(
                    "Falha ao inicializar o cliente do Gemini. Verifique se GEMINI_API_KEY está configurada."
                ) from exc
        return cls._client

    async def generate(self, prompt: str) -> str:
        from google.genai import types

        client = self._get_client()
        try:
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    http_options=types.HttpOptions(timeout=int(self.timeout_s * 1000)),
                ),
            )
        except httpx.TimeoutException as exc:
            raise ProviderError("O Gemini demorou demais para responder. Tente novamente.") from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"{self.label}: {exc}") from exc

        if response.text is None:
            # Acontece quando os filtros de segurança bloqueiam em vez de responder.
            raise ProviderError(
                "O Gemini não retornou conteúdo (possivelmente bloqueado pelos filtros de segurança). "
                "Tente novamente."
            )
        return response.text


# --------------------------------------------------------------------------
# Compatíveis com a API da OpenAI
# --------------------------------------------------------------------------

class OpenAICompatProvider(Provider):
    """Um POST em /chat/completions serve Groq, DeepSeek, Kimi, Z.ai,
    OpenRouter e qualquer servidor local que fale o mesmo dialeto."""

    supports_json_mode = True
    # Teto de saída, equilibrando dois erros opostos medidos na Groq:
    # sem o campo, o padrão do provedor trunca uma sessão de 5 exercícios e o
    # modo JSON devolve 400 descartando tudo ("max completion tokens reached
    # before generating a valid document"); com 8192, o valor reservado conta
    # contra o limite de tokens por minuto e a requisição leva 413 antes de
    # sair ("Limit 8000, Requested 9721"). Uma sessão de 5 gasta ~1.100 tokens
    # de saída, então 4096 dá folga de três vezes sem estourar cota de tier
    # gratuito.
    max_tokens = 4096

    async def generate(self, prompt: str) -> str:
        try:
            return await self._chat(prompt, json_mode=self.supports_json_mode, max_tokens=self.max_tokens)
        except ProviderError as exc:
            message = str(exc).lower()
            # Servidores mais antigos rejeitam response_format; vale uma
            # segunda tentativa sem ele antes de desistir.
            if self.supports_json_mode and "response_format" in message:
                return await self._chat(prompt, json_mode=False, max_tokens=self.max_tokens)
            if "max_tokens" in message or "max_completion_tokens" in message:
                return await self._chat(prompt, json_mode=self.supports_json_mode, max_tokens=None)
            raise

    def extra_headers(self) -> dict:
        return {}

    async def _chat(self, prompt: str, json_mode: bool, max_tokens: int | None) -> str:
        body: dict = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if max_tokens:
            body["max_tokens"] = max_tokens

        headers = {"Content-Type": "application/json", **self.extra_headers()}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self._post(f"{self.base_url.rstrip('/')}/chat/completions", body, headers)
        payload = response.json()

        choices = payload.get("choices") or []
        if not choices:
            # Agregadores devolvem o erro do provedor de baixo dentro do corpo,
            # às vezes com HTTP 200 — tratar como resposta vazia esconderia o
            # motivo real (modelo indisponível, rate limit do upstream).
            raise ProviderError(self.body_error_message(payload))
        return choices[0].get("message", {}).get("content") or ""

    def body_error_message(self, payload: dict) -> str:
        error = payload.get("error")
        if not isinstance(error, dict):
            return f"{self.label} respondeu sem nenhuma escolha (resposta vazia)."

        metadata = error.get("metadata") or {}
        detail = str(metadata.get("raw") or error.get("message") or "")[:300]
        retry = metadata.get("retry_after_seconds")
        suffix = f" Tente de novo em {retry}s." if retry else ""
        return f"{self.label}: {detail} (código {error.get('code', '?')}).{suffix}"


class GroqProvider(OpenAICompatProvider):
    name = "groq"
    base_url = "https://api.groq.com/openai/v1"
    api_key_env = "GROQ_API_KEY"
    default_model = "openai/gpt-oss-20b"


class DeepSeekProvider(OpenAICompatProvider):
    name = "deepseek"
    base_url = "https://api.deepseek.com/v1"
    api_key_env = "DEEPSEEK_API_KEY"
    default_model = "deepseek-chat"


class KimiProvider(OpenAICompatProvider):
    name = "kimi"
    base_url = "https://api.moonshot.ai/v1"
    api_key_env = "MOONSHOT_API_KEY"
    default_model = "kimi-k2-0905-preview"


class ZAIProvider(OpenAICompatProvider):
    name = "zai"
    base_url = "https://api.z.ai/api/paas/v4"
    api_key_env = "ZAI_API_KEY"
    default_model = "glm-4.6"


class OpenRouterProvider(OpenAICompatProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    api_key_env = "OPENROUTER_API_KEY"
    # Modelos ':free' saem e entram do catálogo, e o pool é compartilhado entre
    # todos os usuários gratuitos — 429 vindo do provedor de baixo é rotina.
    # `--list-providers` mostra o padrão atual; a lista viva está em /api/v1/models.
    default_model = "minimax/minimax-m3:free"

    def extra_headers(self) -> dict:
        # Atribuição opcional do OpenRouter; identifica o app nos rankings.
        return {"X-Title": "UniversePie", "HTTP-Referer": "https://github.com/local/universepie"}


class CustomProvider(OpenAICompatProvider):
    """Qualquer endpoint compatível apontado por AI_BASE_URL — inclusive
    llama.cpp, vLLM ou LM Studio rodando na própria máquina."""

    name = "custom"
    api_key_env = "AI_API_KEY"
    default_model = "local-model"

    def __init__(self, model: str | None = None, timeout_s: float | None = None):
        super().__init__(model, timeout_s)
        self.base_url = AI_BASE_URL

    def ready(self) -> tuple[bool, str]:
        if not self.base_url:
            return False, "Provedor 'custom' selecionado, mas AI_BASE_URL não está definida no .env."
        return True, ""


# --------------------------------------------------------------------------
# Ollama (modelos locais)
# --------------------------------------------------------------------------

class OllamaProvider(Provider):
    name = "ollama"
    default_model = "qwen3:8b"
    api_key_env = None
    # Modelo local não tem rate limit, mas tem throughput: uma sessão de 5
    # exercícios pode passar de um minuto em hardware modesto.
    default_timeout_s = 900.0

    def __init__(self, model: str | None = None, timeout_s: float | None = None):
        super().__init__(model, timeout_s)
        self.base_url = OLLAMA_BASE_URL

    async def generate(self, prompt: str) -> str:
        try:
            return await self._chat(prompt, think=False)
        except ProviderError as exc:
            # Modelo sem suporte a raciocínio rejeita o campo em vez de ignorá-lo.
            if "think" in str(exc).lower():
                return await self._chat(prompt, think=None)
            raise

    async def _chat(self, prompt: str, think: bool | None) -> str:
        body: dict = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt}],
            # O pool inteiro num prompt só passa fácil de 4k tokens (o padrão
            # do Ollama): sem isso o começo do prompt é truncado em silêncio.
            "options": {"num_ctx": 8192},
        }
        if think is not None:
            # qwen3 e gemma4 raciocinam por padrão e gastam a maior parte do
            # tempo nisso — 96s para gerar 3 quizzes. A saída aqui é JSON com
            # esquema fixo, onde o ganho do raciocínio não compensa.
            body["think"] = think

        response = await self._post(f"{self.base_url.rstrip('/')}/api/chat", body)
        return response.json().get("message", {}).get("content") or ""

    def connect_error_message(self) -> str:
        return f"Ollama não respondeu em {self.base_url}. Rode 'ollama serve' e confira 'ollama list'."


# --------------------------------------------------------------------------
# Anthropic
# --------------------------------------------------------------------------

class AnthropicProvider(Provider):
    name = "anthropic"
    base_url = "https://api.anthropic.com/v1"
    api_key_env = "ANTHROPIC_API_KEY"
    default_model = "claude-sonnet-5"

    async def generate(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": [
                {"role": "user", "content": prompt},
                # Prefill: a API não tem modo JSON, então abrir o objeto pela
                # boca do modelo evita o "Here is the JSON:" na frente.
                {"role": "assistant", "content": "{"},
            ],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        response = await self._post(f"{self.base_url}/messages", body, headers)
        blocks = response.json().get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return "{" + text


# --------------------------------------------------------------------------
# Registro
# --------------------------------------------------------------------------

_REGISTRY: dict[str, type[Provider]] = {
    cls.name: cls
    for cls in (
        GeminiProvider,
        GroqProvider,
        OllamaProvider,
        AnthropicProvider,
        DeepSeekProvider,
        KimiProvider,
        ZAIProvider,
        OpenRouterProvider,
        CustomProvider,
    )
}


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


def get_provider(name: str | None = None, model: str | None = None, timeout_s: float | None = None) -> Provider:
    """Instancia o provedor pedido, ou o configurado em AI_PROVIDER."""
    resolved = (name or AI_PROVIDER or "gemini").strip().lower()
    if resolved not in _REGISTRY:
        raise ProviderError(
            f"Provedor desconhecido: '{resolved}'. Disponíveis: {', '.join(available_providers())}."
        )
    # AI_MODEL descreve o provedor configurado; aplicá-lo a outro provedor
    # passaria um nome de modelo que não existe lá.
    if not model and resolved == (AI_PROVIDER or "gemini").strip().lower():
        model = AI_MODEL or None
    return _REGISTRY[resolved](model=model, timeout_s=timeout_s)
