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


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=14567, reload=True)
