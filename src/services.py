import logging
from typing import Awaitable, Callable, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

from .anki_client import get_card_pool
from .models import SourceCard

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
S = TypeVar("S", bound=BaseModel)


def build_items(item_cls: type[T], raw_items: list[dict], parsed_cards: list[tuple[str, str]]) -> list[T]:
    """Maps 1-based `used_cards` indices from a Gemini response back to SourceCard
    objects and validates each raw item against `item_cls`. Items that fail
    validation are skipped rather than failing the whole session.
    """
    items: list[T] = []
    for raw in raw_items:
        try:
            used_indices = raw.pop("used_cards", [])
            source_cards = [
                SourceCard(front=parsed_cards[idx - 1][0], back=parsed_cards[idx - 1][1])
                for idx in used_indices
                if 1 <= idx <= len(parsed_cards)
            ]
            if not source_cards:
                source_cards.append(SourceCard(front="(source unavailable)", back=""))
            raw["source_cards"] = source_cards
            items.append(item_cls(**raw))
        except Exception:
            logger.warning("Descartando item inválido do Gemini (%s): %r", item_cls.__name__, raw, exc_info=True)
    return items


async def run_session(
    item_cls: type[T],
    session_cls: type[S],
    field_name: str,
    generate_fn: Callable[[list[tuple[str, str]], int], Awaitable[list[dict]]],
    n: int,
    empty_error: str,
) -> S:
    """Shared orchestration for the quiz/cloze endpoints: fetch a card pool,
    call the given Gemini generator, validate the results, and wrap the
    session in the given Pydantic model. Converts any unexpected error into
    an HTTPException so routers don't have to repeat that try/except.
    """
    try:
        parsed_cards = await get_card_pool(n)
        raw_items = await generate_fn(parsed_cards, n)
        items = build_items(item_cls, raw_items, parsed_cards)

        if not items:
            raise HTTPException(status_code=500, detail=empty_error)

        return session_cls(**{field_name: items, "total": len(items)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Falha ao gerar sessão (%s)", generate_fn.__name__, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
