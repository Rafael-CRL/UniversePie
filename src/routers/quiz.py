from fastapi import APIRouter, HTTPException, Query

from ..ai_client import ai_client, generate_quiz_session
from ..models import QuizItem, QuizSession
from ..services import run_session

router = APIRouter()


@router.get("/api/quiz-session", response_model=QuizSession)
async def get_quiz_session(n: int = Query(default=5, ge=1, le=10)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    return await run_session(
        item_cls=QuizItem,
        session_cls=QuizSession,
        field_name="quizzes",
        generate_fn=generate_quiz_session,
        n=n,
        empty_error="Nenhum quiz gerado com sucesso.",
    )
