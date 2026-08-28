from fastapi import APIRouter

from ..ai_client import ai_client
from ..anki_client import get_card_ids
from ..config import DECK_NAME

router = APIRouter()


@router.get("/api/status")
async def get_status():
    """Reports whether the app is actually usable right now, so the frontend
    can warn the user before they try to start a session."""
    gemini_configured = ai_client is not None

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
        "gemini_configured": gemini_configured,
    }
