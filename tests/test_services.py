from src.models import QuizItem
from src.services import build_items

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
