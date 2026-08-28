from fastapi import APIRouter, HTTPException, Query

from ..ai_client import ai_client, generate_cloze_session
from ..anki_client import get_card_pool
from ..models import ClozeItem, ClozeSession
from ..services import build_items

router = APIRouter()


@router.get("/api/cloze-session", response_model=ClozeSession)
async def get_cloze_session(n: int = Query(default=5, ge=1, le=10)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    try:
        parsed_cards = await get_card_pool(n)

        raw_exercises = await generate_cloze_session(parsed_cards, n)

        exercises = build_items(ClozeItem, raw_exercises, parsed_cards)

        if not exercises:
            raise HTTPException(status_code=500, detail="Nenhum exercício cloze gerado com sucesso.")

        return ClozeSession(exercises=exercises, total=len(exercises))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
