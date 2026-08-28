import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .prompts import build_cloze_prompt, build_quiz_prompt

# Loaded here (not just in config.py) so genai.Client() below sees
# GEMINI_API_KEY regardless of which module gets imported first.
load_dotenv()

try:
    ai_client = genai.Client()
except Exception:
    ai_client = None
    print("Aviso: Falha ao inicializar o cliente genai. Verifique se GEMINI_API_KEY está configurada.")


async def _generate_session(prompt: str, response_key: str) -> list[dict]:
    """Sends a prompt to Gemini and extracts the list of items from its JSON
    response. Handles both {"<response_key>": [...]} and direct [...] formats.
    """
    response = await ai_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text)

    if isinstance(data, dict) and response_key in data:
        return data[response_key]
    if isinstance(data, list):
        return data
    raise ValueError(f"Formato inesperado do Gemini: {type(data)}")


async def generate_quiz_session(cards: list[tuple[str, str]], n: int) -> list[dict]:
    """Sends the full card pool to Gemini in a single request and gets n quizzes back."""
    return await _generate_session(build_quiz_prompt(cards, n), "quizzes")


async def generate_cloze_session(cards: list[tuple[str, str]], n: int) -> list[dict]:
    """Sends the full card pool to Gemini and gets n cloze exercises back."""
    return await _generate_session(build_cloze_prompt(cards, n), "exercises")
