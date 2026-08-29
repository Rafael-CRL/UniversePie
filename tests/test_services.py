import asyncio
import logging

import pytest
from fastapi import HTTPException

from src import services
from src.models import QuizItem, QuizSession
from src.services import build_items, run_session

PARSED_CARDS = [
    ("settle into", "to become comfortable in a new situation"),
    ("settle for", "to accept something less than ideal"),
]

RAW_QUIZ = {
    "quiz_type": "discrimination",
    "concept": "settle into vs settle for",
    "question": "Which fits: I need to ___ a new routine.",
    "options": ["settle into", "settle for", "settle down", "settle up"],
    "answer_index": 0,
    "explanation": "...",
    "used_cards": [1, 2],
}


def test_build_items_maps_used_cards_to_source_cards():
    items = build_items(QuizItem, [dict(RAW_QUIZ)], PARSED_CARDS)

    assert len(items) == 1
    assert [c.front for c in items[0].source_cards] == ["settle into", "settle for"]


def test_build_items_falls_back_when_no_used_cards():
    raw = {**RAW_QUIZ, "used_cards": []}

    items = build_items(QuizItem, [raw], PARSED_CARDS)

    assert items[0].source_cards[0].front == "(source unavailable)"


def test_build_items_skips_invalid_items_without_failing_the_batch():
    valid = dict(RAW_QUIZ)
    invalid = {**RAW_QUIZ, "quiz_type": "not_a_type"}

    items = build_items(QuizItem, [invalid, valid], PARSED_CARDS)

    assert len(items) == 1


def test_build_items_logs_a_warning_for_each_skipped_item(caplog):
    invalid = {**RAW_QUIZ, "quiz_type": "not_a_type"}

    with caplog.at_level(logging.WARNING, logger="src.services"):
        build_items(QuizItem, [invalid], PARSED_CARDS)

    assert "QuizItem" in caplog.text


async def _fake_get_card_pool(n):
    return PARSED_CARDS


async def _fake_generate_fn(cards, n):
    return [dict(RAW_QUIZ) for _ in range(n)]


async def _fake_generate_fn_empty(cards, n):
    return []


def test_run_session_builds_the_session_on_success(monkeypatch):
    monkeypatch.setattr("src.services.get_card_pool", _fake_get_card_pool)

    session = asyncio.run(
        run_session(
            item_cls=QuizItem,
            session_cls=QuizSession,
            field_name="quizzes",
            generate_fn=_fake_generate_fn,
            n=2,
            empty_error="Nenhum quiz gerado com sucesso.",
        )
    )

    assert isinstance(session, QuizSession)
    assert session.total == 2
    assert len(session.quizzes) == 2


def test_run_session_raises_http_exception_when_nothing_was_generated(monkeypatch):
    monkeypatch.setattr("src.services.get_card_pool", _fake_get_card_pool)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            run_session(
                item_cls=QuizItem,
                session_cls=QuizSession,
                field_name="quizzes",
                generate_fn=_fake_generate_fn_empty,
                n=2,
                empty_error="Nenhum quiz gerado com sucesso.",
            )
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Nenhum quiz gerado com sucesso."


def test_run_session_wraps_unexpected_errors_as_500(monkeypatch):
    monkeypatch.setattr("src.services.get_card_pool", _fake_get_card_pool)

    async def _boom(cards, n):
        raise ValueError("Gemini explodiu")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            run_session(
                item_cls=QuizItem,
                session_cls=QuizSession,
                field_name="quizzes",
                generate_fn=_boom,
                n=2,
                empty_error="Nenhum quiz gerado com sucesso.",
            )
        )

    assert exc_info.value.status_code == 500
    assert "Gemini explodiu" in exc_info.value.detail


def test_run_session_logs_unexpected_errors_with_stacktrace(monkeypatch, caplog):
    """Regression test: an unexpected failure must leave a server-side trace,
    not just the HTTPException shown to the user.
    """
    monkeypatch.setattr("src.services.get_card_pool", _fake_get_card_pool)

    async def _boom(cards, n):
        raise ValueError("Gemini explodiu")

    with caplog.at_level(logging.ERROR, logger="src.services"):
        with pytest.raises(HTTPException):
            asyncio.run(
                run_session(
                    item_cls=QuizItem,
                    session_cls=QuizSession,
                    field_name="quizzes",
                    generate_fn=_boom,
                    n=2,
                    empty_error="Nenhum quiz gerado com sucesso.",
                )
            )

    assert "Falha ao gerar sessão" in caplog.text
    assert any(r.exc_info for r in caplog.records)


def test_run_session_raises_when_no_provider_is_configured(monkeypatch):
    """Regression test: this guard used to be duplicated in each router;
    it now lives once in run_session and must still fail fast, before
    touching Anki, when the selected provider isn't usable — and the reason
    the provider gave has to reach the user.
    """
    monkeypatch.setattr(services, "provider_ready", lambda: (False, "Defina GROQ_API_KEY no .env."))

    async def _should_not_be_called(n):
        raise AssertionError("get_card_pool não deve rodar sem provedor configurado")

    monkeypatch.setattr(services, "get_card_pool", _should_not_be_called)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            run_session(
                item_cls=QuizItem,
                session_cls=QuizSession,
                field_name="quizzes",
                generate_fn=_fake_generate_fn,
                n=2,
                empty_error="Nenhum quiz gerado com sucesso.",
            )
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Defina GROQ_API_KEY no .env."
