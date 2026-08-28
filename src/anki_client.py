import random
import re

import httpx
from fastapi import HTTPException

from .config import ANKI_CONNECT_URL, DECK_NAME, POOL_MULTIPLIER

http_client: httpx.AsyncClient | None = None


async def startup():
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)


async def shutdown():
    if http_client:
        await http_client.aclose()


def strip_html(text: str) -> str:
    """Remove tags HTML e referências [sound:...] do texto de um card do Anki."""
    text = re.sub(r"\[sound:[^\]]+\]", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def anki_invoke(action: str, params: dict = None):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    try:
        response = await http_client.post(ANKI_CONNECT_URL, json=payload)
    except httpx.ConnectError:
        raise Exception("Não foi possível conectar ao AnkiConnect. Verifique se o Anki está aberto.")
    response.raise_for_status()
    result = response.json()
    if "error" not in result or "result" not in result:
        raise Exception("Resposta inválida do AnkiConnect")
    if result["error"] is not None:
        raise Exception(result["error"])
    return result["result"]


async def get_card_ids() -> list[int]:
    return await anki_invoke("findCards", {"query": f'"deck:{DECK_NAME}"'})


async def get_card_pool(n: int) -> list[tuple[str, str]]:
    """Fetches a random pool of cards from the deck and parses Front/Back fields.

    Raises HTTPException with an actionable message when the deck is empty
    or when cards don't have the expected 'Front'/'Back' field names.
    """
    card_ids = await get_card_ids()
    if not card_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nenhum card encontrado no deck '{DECK_NAME}'. "
                "Verifique se o Anki está aberto e se o nome do deck está correto "
                "(configure a variável ANKI_DECK_NAME no .env caso seu deck tenha outro nome)."
            ),
        )

    pool_size = min(n * POOL_MULTIPLIER, len(card_ids))
    pool_size = max(pool_size, n)  # at least n cards
    selected_ids = random.sample(card_ids, pool_size)

    cards_info = await anki_invoke("cardsInfo", {"cards": selected_ids})

    parsed_cards: list[tuple[str, str]] = []
    for info in cards_info:
        fields = info.get("fields", {})
        front = strip_html(fields.get("Front", {}).get("value", ""))
        back = strip_html(fields.get("Back", {}).get("value", ""))
        if front:
            parsed_cards.append((front, back))

    if not parsed_cards:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Nenhum card do deck '{DECK_NAME}' tem os campos esperados. "
                "Os cards precisam ter campos chamados 'Front' e 'Back' no note type do Anki."
            ),
        )

    if len(parsed_cards) < n:
        raise HTTPException(status_code=500, detail="Cards válidos insuficientes no pool.")

    return parsed_cards
