from src.prompts import build_cloze_prompt, build_quiz_prompt

CARDS = [
    ("settle into", "to become comfortable in a new situation"),
    ("settle for", "to accept something less than ideal"),
]


def test_build_quiz_prompt_includes_every_card_and_the_requested_count():
    prompt = build_quiz_prompt(CARDS, n=3)

    assert "Card 1:\n  Front: settle into\n  Back: to become comfortable in a new situation" in prompt
    assert "Card 2:\n  Front: settle for\n  Back: to accept something less than ideal" in prompt
    assert "exactly 3 quizzes" in prompt


def test_build_cloze_prompt_includes_every_card_and_the_requested_count():
    prompt = build_cloze_prompt(CARDS, n=4)

    assert "Card 1:\n  Front: settle into\n  Back: to become comfortable in a new situation" in prompt
    assert "Card 2:\n  Front: settle for\n  Back: to accept something less than ideal" in prompt
    assert "exactly 4 exercises" in prompt
