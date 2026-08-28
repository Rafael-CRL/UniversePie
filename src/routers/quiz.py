from fastapi import APIRouter, HTTPException, Query

from ..ai_client import ai_client, generate_quiz_session
from ..anki_client import get_card_pool
from ..models import QuizItem, QuizSession
from ..services import build_items

router = APIRouter()


@router.get("/api/quiz-session", response_model=QuizSession)
async def get_quiz_session(n: int = Query(default=5, ge=1, le=10)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    try:
        parsed_cards = await get_card_pool(n)

        # Single Gemini call with the full pool
        raw_quizzes = await generate_quiz_session(parsed_cards, n)

        quizzes = build_items(QuizItem, raw_quizzes, parsed_cards)

        if not quizzes:
            raise HTTPException(status_code=500, detail="Nenhum quiz gerado com sucesso.")

        return QuizSession(quizzes=quizzes, total=len(quizzes))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
