import json

from google import genai
from google.genai import types

from .prompts import build_cloze_prompt, build_quiz_prompt

try:
    ai_client = genai.Client()
except Exception:
    ai_client = None
    print("Aviso: Falha ao inicializar o cliente genai. Verifique se GEMINI_API_KEY está configurada.")


async def generate_quiz_session(cards: list[tuple[str, str]], n: int) -> list[dict]:
    """Sends the full card pool to Gemini in a single request and gets n quizzes back."""
    prompt = build_quiz_prompt(cards, n)

    response = await ai_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text)

    # Handle both {"quizzes": [...]} and direct [...] formats
    if isinstance(data, dict) and "quizzes" in data:
        return data["quizzes"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Formato inesperado do Gemini: {type(data)}")


async def generate_cloze_session(cards: list[tuple[str, str]], n: int) -> list[dict]:
    """Sends the full card pool to Gemini and gets n cloze exercises back."""
    prompt = build_cloze_prompt(cards, n)

    response = await ai_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text)

    if isinstance(data, dict) and "exercises" in data:
        return data["exercises"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Formato inesperado do Gemini: {type(data)}")
