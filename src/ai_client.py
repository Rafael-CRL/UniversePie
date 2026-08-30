import json
import re

from dotenv import load_dotenv

from .prompts import build_cloze_prompt, build_quiz_prompt
from .providers import Provider, ProviderError, get_provider

# Carregado aqui (e não só no config.py) para que a escolha de provedor e as
# chaves existam independentemente de qual módulo for importado primeiro.
load_dotenv()

_FENCES = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def provider_ready() -> tuple[bool, str]:
    """(dá para gerar agora?, o que fazer se não der)."""
    try:
        return get_provider().ready()
    except ProviderError as exc:
        return False, str(exc)


def parse_json(text: str) -> object:
    """Converte a resposta do modelo em JSON, tolerando o que modelos menores
    fazem: cercar em ```json, narrar antes ("Here is the JSON:") ou depois.
    """
    cleaned = _FENCES.sub("", text or "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Tenta decodificar a partir de cada abertura de objeto/lista. Um regex
    # guloso ancorava no PRIMEIRO colchete da string, então narração com
    # colchete antes do JSON ("Here's the analysis [see below]: {...}") movia o
    # início da captura para dentro da prosa e a recuperação falhava — no caso
    # exato para o qual ela existe.
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(cleaned):
        if ch in "{[":
            try:
                return decoder.raw_decode(cleaned, idx)[0]
            except json.JSONDecodeError:
                continue

    raise ProviderError("O modelo retornou uma resposta em formato inválido. Tente novamente.")


def extract_items(data: object, response_key: str) -> list[dict]:
    """Encontra a lista de exercícios na resposta.

    O contrato pede {"quizzes": [...]}, mas modelos menores trocam o nome da
    chave ou devolvem um item solto — recuperar isso aqui é mais barato do
    que descartar a sessão inteira.
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if isinstance(data.get(response_key), list):
            return data[response_key]

        # Antes da heurística de lista: um item solto tem listas dentro dele
        # ("options", "acceptable_alternatives") que não são a lista buscada.
        if any(key in data for key in ("question", "sentence")):
            return [data]

        lists = [v for v in data.values() if isinstance(v, list) and v and all(isinstance(i, dict) for i in v)]
        if len(lists) == 1:
            return lists[0]

    raise ProviderError(f"Formato inesperado do modelo: {type(data).__name__}.")


async def _generate_session(prompt: str, response_key: str, provider: Provider | None = None) -> list[dict]:
    provider = provider or get_provider()
    text = await provider.generate(prompt)
    return extract_items(parse_json(text), response_key)


async def generate_quiz_session(
    cards: list[tuple[str, str]], n: int, provider: Provider | None = None
) -> list[dict]:
    """Manda o pool inteiro numa única requisição e recebe n quizzes."""
    return await _generate_session(build_quiz_prompt(cards, n), "quizzes", provider)


async def generate_cloze_session(
    cards: list[tuple[str, str]], n: int, provider: Provider | None = None
) -> list[dict]:
    """Manda o pool inteiro numa única requisição e recebe n exercícios cloze."""
    return await _generate_session(build_cloze_prompt(cards, n), "exercises", provider)
