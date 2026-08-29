from fastapi import APIRouter

from ..ai_client import provider_ready
from ..anki_client import get_card_ids
from ..config import DECK_NAME
from ..providers import get_provider

router = APIRouter()


@router.get("/api/status")
async def get_status():
    """Reports whether the app is actually usable right now, so the frontend
    can warn the user before they try to start a session."""
    ai_ready, ai_reason = provider_ready()
    try:
        provider = get_provider()
        provider_label = provider.label
    except Exception:
        provider_label = "?"

    anki_connected = False
    card_count = 0
    try:
        card_ids = await get_card_ids()
        anki_connected = True
        card_count = len(card_ids)
    except Exception:
        pass

    return {
        "anki_connected": anki_connected,
        "deck_name": DECK_NAME,
        "deck_found": card_count > 0,
        "card_count": card_count,
        "ai_ready": ai_ready,
        "ai_provider": provider_label,
        "ai_detail": ai_reason,
        # Mantido para não quebrar o frontend atual, que ainda lê esta chave.
        "gemini_configured": ai_ready,
    }
