from fastapi import APIRouter, Query

from ..ai_client import generate_cloze_session
from ..models import ClozeItem, ClozeSession
from ..services import run_session

router = APIRouter()


@router.get("/api/cloze-session", response_model=ClozeSession)
async def get_cloze_session(n: int = Query(default=5, ge=1, le=10)):
    return await run_session(
        item_cls=ClozeItem,
        session_cls=ClozeSession,
        field_name="exercises",
        generate_fn=generate_cloze_session,
        n=n,
        empty_error="Nenhum exercício cloze gerado com sucesso.",
    )
