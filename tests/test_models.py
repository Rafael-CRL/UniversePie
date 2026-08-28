import pytest
from pydantic import ValidationError

from src.models import ClozeItem, QuizItem, SourceCard

VALID_QUIZ_KWARGS = dict(
    quiz_type="discrimination",
    concept="settle into vs settle for",
    question="Which fits: I need to ___ a new routine.",
    options=["settle into", "settle for", "settle down", "settle up"],
    answer_index=0,
    explanation="'Settle into' means to become comfortable in a new situation.",
    source_cards=[SourceCard(front="settle into", back="to become comfortable in a new situation")],
)

VALID_CLOZE_KWARGS = dict(
    concept="give up on",
    sentence="She decided to _____ the project after months of frustration.",
    target_expression="give up on",
    acceptable_alternatives=["abandon"],
    hint="A phrasal verb meaning to stop trying",
    commonality="common",
    context_note="",
    explanation="'Give up on' means to stop trying to achieve something.",
    source_cards=[SourceCard(front="give up on", back="to stop trying")],
)


def test_quiz_item_accepts_valid_data():
    QuizItem(**VALID_QUIZ_KWARGS)


def test_quiz_item_rejects_invalid_quiz_type():
    with pytest.raises(ValidationError):
        QuizItem(**{**VALID_QUIZ_KWARGS, "quiz_type": "not_a_type"})


def test_quiz_item_rejects_wrong_option_count():
    with pytest.raises(ValidationError):
        QuizItem(**{**VALID_QUIZ_KWARGS, "options": ["a", "b"]})


def test_quiz_item_rejects_out_of_range_answer_index():
    with pytest.raises(ValidationError):
        QuizItem(**{**VALID_QUIZ_KWARGS, "answer_index": 4})


def test_cloze_item_accepts_valid_data():
    ClozeItem(**VALID_CLOZE_KWARGS)


def test_cloze_item_rejects_invalid_commonality():
    with pytest.raises(ValidationError):
        ClozeItem(**{**VALID_CLOZE_KWARGS, "commonality": "rare"})
