from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from . import anki_client
from .config import STATIC_DIR
from .routers import cloze, quiz, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    await anki_client.startup()
    yield
    await anki_client.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(quiz.router)
app.include_router(cloze.router)
app.include_router(status.router)

# Read once at import time instead of on every request: avoids a blocking
# disk read inside an async handler, and the content never changes at
# runtime anyway (uvicorn --reload restarts the module on edits).
INDEX_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return INDEX_HTML


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=14567, reload=True)
