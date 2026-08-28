from typing import TypeVar

from pydantic import BaseModel

from .models import SourceCard

T = TypeVar("T", bound=BaseModel)


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
            continue
    return items
