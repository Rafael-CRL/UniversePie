import re
import random
import json
import asyncio
import httpx
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator
import uvicorn
from google import genai
from google.genai import types

ANKI_CONNECT_URL = "http://localhost:8765"
DECK_NAME = "English_Series"

STATIC_DIR = Path(__file__).parent / "static"

# Pool multiplier: how many cards to fetch relative to the requested quiz count.
# A larger pool gives the AI more material to find relationships and clusters.
POOL_MULTIPLIER = 3

_card_ids_cache: list[int] = []
http_client: httpx.AsyncClient = None

try:
    ai_client = genai.Client()
except Exception:
    ai_client = None
    print("Aviso: Falha ao inicializar o cliente genai. Verifique se GEMINI_API_KEY está configurada.")


@asynccontextmanager
async def lifespan(app):
    global http_client
    http_client = httpx.AsyncClient(timeout=30.0)
    yield
    await http_client.aclose()


app = FastAPI(lifespan=lifespan)


class SourceCard(BaseModel):
    front: str
    back: str


class QuizItem(BaseModel):
    quiz_type: str
    concept: str
    question: str
    options: list[str]
    answer_index: int
    explanation: str
    source_cards: list[SourceCard]

    @field_validator("quiz_type")
    @classmethod
    def valid_quiz_type(cls, v):
        allowed = {"discrimination", "production", "interference", "polysemy", "contextual"}
        if v not in allowed:
            raise ValueError(f"quiz_type deve ser um de {allowed}, recebeu '{v}'")
        return v

    @field_validator("options")
    @classmethod
    def exactly_four_options(cls, v):
        if len(v) != 4:
            raise ValueError(f"Esperado 4 opções, recebeu {len(v)}")
        return v

    @field_validator("answer_index")
    @classmethod
    def valid_answer_index(cls, v):
        if v not in (0, 1, 2, 3):
            raise ValueError(f"answer_index deve ser 0-3, recebeu {v}")
        return v


class QuizSession(BaseModel):
    quizzes: list[QuizItem]
    total: int


class ClozeItem(BaseModel):
    concept: str
    sentence: str
    target_expression: str
    acceptable_alternatives: list[str]
    hint: str
    commonality: str
    context_note: str
    explanation: str
    source_cards: list[SourceCard]

    @field_validator("commonality")
    @classmethod
    def valid_commonality(cls, v):
        allowed = {"common", "moderate", "niche"}
        if v not in allowed:
            raise ValueError(f"commonality deve ser um de {allowed}, recebeu '{v}'")
        return v


class ClozeSession(BaseModel):
    exercises: list[ClozeItem]
    total: int


def strip_html(text: str) -> str:
    """Remove tags HTML e referências [sound:...] do texto de um card do Anki."""
    text = re.sub(r"\[sound:[^\]]+\]", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def anki_invoke(action: str, params: dict = None):
    payload = {"action": action, "version": 6}
    if params:
        payload["params"] = params
    try:
        response = await http_client.post(ANKI_CONNECT_URL, json=payload)
    except httpx.ConnectError:
        raise Exception("Não foi possível conectar ao AnkiConnect. Verifique se o Anki está aberto.")
    response.raise_for_status()
    result = response.json()
    if "error" not in result or "result" not in result:
        raise Exception("Resposta inválida do AnkiConnect")
    if result["error"] is not None:
        raise Exception(result["error"])
    return result["result"]


async def get_card_ids() -> list[int]:
    global _card_ids_cache
    if not _card_ids_cache:
        _card_ids_cache = await anki_invoke("findCards", {"query": f'"deck:{DECK_NAME}"'})
    return _card_ids_cache


def build_quiz_prompt(cards: list[tuple[str, str]], n: int) -> str:
    """Builds the prompt that sends a pool of cards and requests n quizzes."""
    cards_block = ""
    for i, (front, back) in enumerate(cards):
        cards_block += f"Card {i + 1}:\n  Front: {front}\n  Back: {back}\n\n"

    return f"""You are a quiz designer for intermediate-to-advanced English learners whose native language is Brazilian Portuguese.

You will receive a pool of {len(cards)} flashcards from the learner's Anki deck. Your job is to generate exactly {n} quiz questions that test DEEP understanding — not surface recognition.

## Quiz Strategy Types

You MUST vary the strategy across the session. Use as many different types as possible. Each quiz must declare its type.

### discrimination
Use when the pool contains cards that share a root word, similar structure, or related concept (e.g., "settle into" vs "settle for" vs "settle on"; or "get off" vs "get on" vs "get over").
Present a context and force the learner to pick the correct variant.
The wrong options MUST be real expressions from other cards in the pool when possible.

### production
Describe a situation, a communicative intent, or a meaning — then ask which expression fits.
Do NOT give the expression and ask for the meaning. That is passive recognition and forbidden in this type.
Example: "You want to tell someone to stop insisting on a topic. Which expression fits?" → Drop it

### interference
Design a question that exploits a common error a Brazilian Portuguese speaker would make.
One of the wrong options MUST be the literal Portuguese translation trap — the answer the learner's L1 brain wants to pick.
Example: "'She walked down the street' means:" with a trap option "She descended the street".

### polysemy
Use when a word in the pool has multiple distinct meanings (e.g., "sound" = healthy/safe vs noise vs to seem).
Present 2-3 short sentences using the same word and ask in which sentence it carries a specific meaning.

### contextual
Present a realistic conversational or written scenario and ask what a speaker means, what would be the appropriate response, or what the pragmatic implication is.
This tests reading between the lines, tone, register, and pragmatic competence.
Example: "Your boss emails: 'Going forward, let's loop in the whole team.' What is the pragmatic implication?"

## Rules

1. Each quiz MUST have exactly 4 options.
2. answer_index is the 0-based index of the correct option.
3. Wrong options must be PLAUSIBLE. They must represent real confusions, not absurd fillers. Whenever possible, derive distractors from other cards in the pool.
4. All questions must be written in English.
5. Explanations must be concise, useful, and teach something the learner can retain. If relevant, mention the Portuguese interference or the common mistake.
6. Each quiz must include a "used_cards" field: an array of 1-based card indices from the pool that were used to build that quiz. This lets the system trace the source.
7. Vary quiz types. Do not use the same type for consecutive quizzes.
8. You may combine concepts from multiple cards in a single quiz.
9. Prioritize concepts that have nuances, polysemy, or structural patterns over simple vocabulary.

## Output Format

Return a JSON object:
{{
  "quizzes": [
    {{
      "quiz_type": "discrimination | production | interference | polysemy | contextual",
      "concept": "Brief label of the concept being tested",
      "question": "The question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer_index": 0,
      "explanation": "Why the answer is correct. Mention traps or common errors if applicable.",
      "used_cards": [1, 3]
    }}
  ]
}}

## Card Pool

{cards_block}

Generate exactly {n} quizzes. Output ONLY valid JSON, no markdown fences."""


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


def build_cloze_prompt(cards: list[tuple[str, str]], n: int) -> str:
    """Builds the prompt for cloze (fill-in-the-blank) exercises."""
    cards_block = ""
    for i, (front, back) in enumerate(cards):
        cards_block += f"Card {i + 1}:\n  Front: {front}\n  Back: {back}\n\n"

    return f"""You are generating fill-in-the-blank exercises for an intermediate-to-advanced English learner whose native language is Brazilian Portuguese.

You will receive a pool of {len(cards)} flashcards from the learner's Anki deck. These cards were mined from varied sources — movies, TV series, articles, books, conversations. Because of this, some expressions may be highly context-specific, archaic, or uncommon in everyday English.

Your job is to generate exactly {n} cloze exercises. Each exercise presents a sentence with one blank (marked as _____) that the learner must fill in by producing the correct expression from memory — without any options to choose from.

## For each exercise:

1. Pick a concept from the card pool (phrasal verb, idiom, collocation, or structurally interesting expression).
2. Write a sentence that uses that concept naturally, replacing it with _____. The sentence must create a DIFFERENT context from the original card — do not reuse the same scenario.
3. Provide the target_expression: the exact expected answer.
4. List 1-3 acceptable_alternatives: genuinely valid substitutions in this specific sentence context, not loose synonyms.
5. Write a hint that nudges toward the answer without giving it away (e.g., "Think of a phrasal verb meaning 'to accommodate oneself'" — NOT "starts with 's'").
6. Rate the commonality of the target expression:
   - "common": used regularly in everyday spoken/written English
   - "moderate": recognized and used, but not frequent in casual conversation
   - "niche": context-specific, literary, regional, slang, or specialized usage
7. Write a context_note: If the expression is moderate or niche, briefly explain WHY (e.g., "This usage of 'camp' appears mainly in political/media contexts" or "Common in legal English but rare in casual speech"). Leave empty for common expressions.
8. Write an explanation that teaches something about the expression — its nuance, common mistakes by Portuguese speakers, or why the alternatives also work.
9. Include used_cards: array of 1-based card indices from the pool that were used.

## Rules:
- The blank must target a SINGLE meaningful expression — not a generic word like "the" or "very".
- Sentences must sound natural, not contrived to force the expression in.
- Acceptable alternatives must be genuinely interchangeable in the given sentence without changing the core meaning significantly.
- Be HONEST in commonality ratings. Do not inflate niche expressions to "common". The learner mines content from TV series and movies — some of that material is colloquial, character-specific, or stylized. Flag it.
- context_note must be genuinely informative when the expression is not "common".
- The hint should be useful but not a giveaway.
- Prioritize expressions that have nuance, structural patterns, or are prone to Portuguese interference.

## Output Format

Return a JSON object:
{{{{
  "exercises": [
    {{{{
      "concept": "Brief label of the concept",
      "sentence": "She decided to _____ the project after months of frustration.",
      "target_expression": "give up on",
      "acceptable_alternatives": ["abandon", "walk away from"],
      "hint": "A common phrasal verb meaning to stop trying",
      "commonality": "common",
      "context_note": "",
      "explanation": "'Give up on' means to stop trying to achieve or improve something...",
      "used_cards": [2, 5]
    }}}}
  ]
}}}}

## Card Pool

{cards_block}

Generate exactly {n} exercises. Output ONLY valid JSON, no markdown fences."""


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


@app.get("/api/quiz-session", response_model=QuizSession)
async def get_quiz_session(n: int = Query(default=5, ge=1, le=10)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    try:
        card_ids = await get_card_ids()
        if not card_ids:
            raise HTTPException(status_code=404, detail=f"Nenhum card encontrado no deck '{DECK_NAME}'")

        # Select a larger pool to give the AI more material to work with
        pool_size = min(n * POOL_MULTIPLIER, len(card_ids))
        pool_size = max(pool_size, n)  # at least n cards
        selected_ids = random.sample(card_ids, pool_size)

        # Fetch all card info in a single batch call
        cards_info = await anki_invoke("cardsInfo", {"cards": selected_ids})

        parsed_cards: list[tuple[str, str]] = []
        for info in cards_info:
            fields = info.get("fields", {})
            front = strip_html(fields.get("Front", {}).get("value", ""))
            back = strip_html(fields.get("Back", {}).get("value", ""))
            if front:
                parsed_cards.append((front, back))

        if len(parsed_cards) < n:
            raise HTTPException(status_code=500, detail="Cards válidos insuficientes no pool.")

        # Single Gemini call with the full pool
        raw_quizzes = await generate_quiz_session(parsed_cards, n)

        quizzes = []
        for raw in raw_quizzes:
            try:
                # Map used_cards indices back to actual card content
                used_indices = raw.pop("used_cards", [])
                source_cards = []
                for idx in used_indices:
                    # used_cards is 1-based
                    if 1 <= idx <= len(parsed_cards):
                        f, b = parsed_cards[idx - 1]
                        source_cards.append(SourceCard(front=f, back=b))

                # Fallback: if the AI didn't provide used_cards, we can't trace
                if not source_cards:
                    source_cards.append(SourceCard(front="(source unavailable)", back=""))

                raw["source_cards"] = source_cards
                quizzes.append(QuizItem(**raw))
            except Exception:
                continue

        if not quizzes:
            raise HTTPException(status_code=500, detail="Nenhum quiz gerado com sucesso.")

        return QuizSession(quizzes=quizzes, total=len(quizzes))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cloze-session", response_model=ClozeSession)
async def get_cloze_session(n: int = Query(default=5, ge=1, le=10)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Cliente Gemini não inicializado. Configure GEMINI_API_KEY.")

    try:
        card_ids = await get_card_ids()
        if not card_ids:
            raise HTTPException(status_code=404, detail=f"Nenhum card encontrado no deck '{DECK_NAME}'")

        pool_size = min(n * POOL_MULTIPLIER, len(card_ids))
        pool_size = max(pool_size, n)
        selected_ids = random.sample(card_ids, pool_size)

        cards_info = await anki_invoke("cardsInfo", {"cards": selected_ids})

        parsed_cards: list[tuple[str, str]] = []
        for info in cards_info:
            fields = info.get("fields", {})
            front = strip_html(fields.get("Front", {}).get("value", ""))
            back = strip_html(fields.get("Back", {}).get("value", ""))
            if front:
                parsed_cards.append((front, back))

        if len(parsed_cards) < n:
            raise HTTPException(status_code=500, detail="Cards válidos insuficientes no pool.")

        raw_exercises = await generate_cloze_session(parsed_cards, n)

        exercises = []
        for raw in raw_exercises:
            try:
                used_indices = raw.pop("used_cards", [])
                source_cards = []
                for idx in used_indices:
                    if 1 <= idx <= len(parsed_cards):
                        f, b = parsed_cards[idx - 1]
                        source_cards.append(SourceCard(front=f, back=b))
                if not source_cards:
                    source_cards.append(SourceCard(front="(source unavailable)", back=""))
                raw["source_cards"] = source_cards
                exercises.append(ClozeItem(**raw))
            except Exception:
                continue

        if not exercises:
            raise HTTPException(status_code=500, detail="Nenhum exercício cloze gerado com sucesso.")

        return ClozeSession(exercises=exercises, total=len(exercises))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open(STATIC_DIR / "index.html", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=14567, reload=True)
