"""Testes das checagens do auditor de exercícios.

O auditor é o que decide se uma mudança de prompt melhorou ou piorou a
qualidade — se as checagens estiverem erradas, a decisão vem errada junto.
"""

import json

import httpx
import pytest

from scripts.audit_exercises import (
    ERROR,
    compare_reports,
    load_cards,
    INFO,
    WARN,
    analyze,
    describe_error,
    check_batch,
    check_cloze_item,
    check_quiz_item,
    render_markdown,
)


def checks(findings, severity=None):
    return {f.check for f in findings if severity is None or f.severity == severity}


def quiz(**overrides):
    item = {
        "quiz_type": "discrimination",
        "concept": "settle into vs settle for",
        "question": "After the move, it took her weeks to _____ her new routine.",
        "options": ["settle into", "settle for", "settle on", "settle down"],
        "answer_index": 0,
        "explanation": "'Settle into' is about adapting to a new situation, while 'settle for' means accepting less.",
        "source_cards": [{"front": "settle into", "back": "to become comfortable in a new situation"}],
    }
    item.update(overrides)
    return item


def cloze(**overrides):
    item = {
        "concept": "give up on",
        "sentence": "She decided to _____ the project after months of frustration.",
        "target_expression": "give up on",
        "acceptable_alternatives": ["abandon"],
        "hint": "A phrasal verb about stopping the effort",
        "commonality": "common",
        "context_note": "",
        "explanation": "'Give up on' means to stop trying to achieve or improve something you cared about.",
        "source_cards": [{"front": "give up on", "back": "parar de tentar"}],
    }
    item.update(overrides)
    return item


# --- quiz ------------------------------------------------------------------

def test_clean_quiz_has_no_findings():
    assert check_quiz_item(quiz(), "quiz", 1, 1) == []


def test_detects_card_number_leak_in_the_question():
    findings = check_quiz_item(quiz(question="Which expression from Card 6 fits here?"), "quiz", 1, 1)
    assert "meta_leak_question" in checks(findings, ERROR)


def test_card_leak_in_the_explanation_is_only_a_warning():
    findings = check_quiz_item(quiz(explanation="'Settle into' (Card 3) is about adapting to a new place."), "quiz", 1, 1)
    assert "meta_leak_explanation" in checks(findings, WARN)


def test_detects_answer_repeated_inside_the_question():
    findings = check_quiz_item(
        quiz(question="Which one means to settle into a new place?"), "quiz", 1, 1
    )
    assert "answer_in_question" in checks(findings, ERROR)


def test_production_asking_for_meaning_is_an_error():
    findings = check_quiz_item(
        quiz(quiz_type="production", question="What does 'settle into' mean in this context?"), "quiz", 1, 1
    )
    assert "passive_recognition" in checks(findings, ERROR)


def test_interference_may_ask_for_meaning():
    """O próprio prompt usa esse formato como exemplo do tipo interference."""
    findings = check_quiz_item(
        quiz(quiz_type="interference", question="'She walked down the street' actually means:"), "quiz", 1, 1
    )
    assert "passive_recognition" not in checks(findings)


def test_detects_telegraphed_l1_trap():
    findings = check_quiz_item(
        quiz(question="A Brazilian Portuguese speaker might mistakenly translate this. What does it mean?"),
        "quiz",
        1,
        1,
    )
    assert "telegraphed_trap" in checks(findings, WARN)


def test_detects_duplicate_options():
    findings = check_quiz_item(quiz(options=["settle into", "Settle into.", "settle on", "settle for"]), "quiz", 1, 1)
    assert "duplicate_options" in checks(findings, ERROR)


def test_detects_item_without_source_cards():
    findings = check_quiz_item(quiz(source_cards=[{"front": "(source unavailable)", "back": ""}]), "quiz", 1, 1)
    assert "ungrounded" in checks(findings, ERROR)


def test_detects_exercise_disconnected_from_its_source_card():
    findings = check_quiz_item(
        quiz(source_cards=[{"front": "brace yourself", "back": "prepare para algo difícil"}]), "quiz", 1, 1
    )
    assert "weak_grounding" in checks(findings, WARN)


# --- cloze -----------------------------------------------------------------

def test_clean_cloze_has_no_findings():
    assert check_cloze_item(cloze(), "cloze", 1, 1) == []


def test_detects_missing_blank():
    findings = check_cloze_item(cloze(sentence="She decided to quit the project."), "cloze", 1, 1)
    assert "missing_blank" in checks(findings, ERROR)


def test_detects_multiple_blanks():
    findings = check_cloze_item(cloze(sentence="She _____ to _____ the project."), "cloze", 1, 1)
    assert "multiple_blanks" in checks(findings, ERROR)


def test_detects_answer_spelled_out_in_the_sentence():
    findings = check_cloze_item(
        cloze(sentence="She decided to give up on it, so she would _____ the project."), "cloze", 1, 1
    )
    assert "target_in_sentence" in checks(findings, ERROR)


def test_detects_hint_that_gives_the_answer_away():
    findings = check_cloze_item(cloze(hint="Use 'give up on' here"), "cloze", 1, 1)
    assert "target_in_hint" in checks(findings, ERROR)


def test_detects_hint_spelling_the_first_letter():
    findings = check_cloze_item(cloze(hint="It starts with 'g'"), "cloze", 1, 1)
    assert "hint_spells_answer" in checks(findings, WARN)


def test_non_common_expression_requires_a_context_note():
    """Regra do docs/AI_RULES.md que os validadores Pydantic não cobrem."""
    findings = check_cloze_item(cloze(commonality="niche", context_note=""), "cloze", 1, 1)
    assert "missing_context_note" in checks(findings, ERROR)

    ok = check_cloze_item(cloze(commonality="niche", context_note="Aparece sobretudo em contexto jurídico."), "cloze", 1, 1)
    assert "missing_context_note" not in checks(ok)


def test_detects_missing_alternatives():
    findings = check_cloze_item(cloze(acceptable_alternatives=[]), "cloze", 1, 1)
    assert "no_alternatives" in checks(findings, WARN)


def test_detects_alternative_that_repeats_the_target():
    findings = check_cloze_item(cloze(acceptable_alternatives=["Give up on"]), "cloze", 1, 1)
    assert "alternative_equals_target" in checks(findings, WARN)


# --- lote e agregados ------------------------------------------------------

def test_detects_items_dropped_by_the_backend():
    findings = check_batch("quiz", 1, [quiz(), quiz()], requested=5, total_field=2)
    assert "count_mismatch" in checks(findings, WARN)


def test_detects_total_field_out_of_sync():
    findings = check_batch("quiz", 1, [quiz(), quiz()], requested=2, total_field=5)
    assert "total_mismatch" in checks(findings, ERROR)


def test_detects_consecutive_repeated_quiz_types():
    findings = check_batch("quiz", 1, [quiz(), quiz()], requested=2, total_field=2)
    assert "consecutive_same_type" in checks(findings, WARN)


def test_detects_answer_position_bias():
    items = [quiz(quiz_type=t) for t in ("discrimination", "production") * 4]
    result = analyze([{"mode": "quiz", "batch": 1, "requested": 8, "payload": {"quizzes": items, "total": 8}}])
    assert "answer_position_bias" in checks(result["findings"], WARN)
    assert result["stats"]["quiz"]["answer_positions"]["0"] == 8


def test_detects_longest_option_bias():
    biased = quiz(
        options=["the correct answer, spelled out at length and in detail", "short", "brief", "tiny"],
        answer_index=0,
    )
    items = [biased for _ in range(4)]
    result = analyze([{"mode": "quiz", "batch": 1, "requested": 4, "payload": {"quizzes": items, "total": 4}}])
    assert "longest_answer_bias" in checks(result["findings"], WARN)


def test_failed_request_becomes_an_error_instead_of_crashing():
    result = analyze([{"mode": "quiz", "batch": 1, "requested": 5, "error": "ReadTimeout: timed out"}])
    assert "request_failed" in checks(result["findings"], ERROR)
    assert result["summary"]["batches_failed"] == 1


def test_summary_counts_flagged_items_once():
    dirty = quiz(question="Which expression from Card 6 means to settle into a new place?")
    result = analyze([{"mode": "quiz", "batch": 1, "requested": 2, "payload": {"quizzes": [dirty, quiz()], "total": 2}}])
    assert result["summary"]["items_audited"] == 2
    assert result["summary"]["items_flagged"] == 1
    assert result["summary"]["clean_rate"] == 0.5


def test_markdown_report_marks_the_correct_option():
    result = analyze([{"mode": "quiz", "batch": 1, "requested": 1, "payload": {"quizzes": [quiz()], "total": 1}}])
    md = render_markdown(result, {"timestamp": "2026-08-29 10:00", "commit": "abc123", "mode": "quiz", "runs": 1, "n": 1})
    assert "1. settle into ✅" in md
    assert "Cards-fonte:" in md


@pytest.mark.parametrize("mode,item", [("quiz", quiz()), ("cloze", cloze())])
def test_analyze_output_is_json_serializable(mode, item):
    key = "quizzes" if mode == "quiz" else "exercises"
    result = analyze([{"mode": mode, "batch": 1, "requested": 1, "payload": {key: [item], "total": 1}}])
    json.dumps(result["stats"])
    json.dumps(result["summary"])


def test_error_message_keeps_the_fastapi_detail():
    """Sem isso o relatório só diz '500 Internal Server Error' e o motivo real
    (Anki fechado, deck vazio, chave do Gemini) se perde."""
    request = httpx.Request("GET", "http://localhost:14567/api/quiz-session")
    response = httpx.Response(500, json={"detail": "Não foi possível conectar ao AnkiConnect."}, request=request)
    exc = httpx.HTTPStatusError("boom", request=request, response=response)

    assert describe_error(exc) == "HTTP 500: Não foi possível conectar ao AnkiConnect."
    assert describe_error(httpx.ReadTimeout("timed out")) == "ReadTimeout: timed out"


# --- pool congelado e comparação entre runs --------------------------------

def test_load_cards_accepts_both_shapes(tmp_path):
    pairs = tmp_path / "pairs.json"
    pairs.write_text(json.dumps([["drop it", "parar de insistir"]]), encoding="utf-8")
    objects = tmp_path / "objects.json"
    objects.write_text(json.dumps([{"front": "drop it", "back": "parar de insistir"}]), encoding="utf-8")

    assert load_cards(pairs) == [("drop it", "parar de insistir")]
    assert load_cards(objects) == [("drop it", "parar de insistir")]


def _report(tmp_path, name, provider, clean_rate, errors, checks):
    path = tmp_path / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "meta": {"tag": name, "provider": provider},
                "summary": {"items_audited": 3, "clean_rate": clean_rate, "errors": errors, "warnings": 0, "infos": 0},
                "stats": {"quiz": {"strategy_coverage": "3/5"}},
                "findings": [{"check": c, "severity": "error", "message": ""} for c in checks],
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_compare_reports_puts_the_runs_side_by_side(tmp_path):
    """Comparar dois provedores no mesmo pool é o que separa 'o prompt está
    ruim' de 'o modelo é fraco'."""
    a = _report(tmp_path, "groq", "groq/openai-gpt-oss-20b", 1.0, 0, [])
    b = _report(tmp_path, "gemma", "ollama/gemma4:e4b", 0.33, 2, ["ungrounded", "missing_blank"])

    table = compare_reports([a, b])

    assert "| groq | groq/openai-gpt-oss-20b | 3 | 100% | 0 |" in table
    assert "| gemma | ollama/gemma4:e4b | 3 | 33% | 2 |" in table
    assert "| `ungrounded` | 0 | 1 |" in table
    assert "| strategy_coverage | 3/5 | 3/5 |" in table


# --- estratificação por completude do card-fonte ---------------------------

def _session(items):
    return analyze([{"mode": "quiz", "batch": 1, "requested": len(items), "payload": {"quizzes": items, "total": len(items)}}])


def test_measures_defect_rate_separately_for_cards_without_back():
    """38% do deck real não tem back e o prompt não diz o que fazer nesse caso;
    sem separar os grupos o efeito fica diluído na média."""
    # Card sem back, mas do mesmo assunto da pergunta: é o formato mais comum
    # no deck real (frase minerada, sem definição escrita).
    no_back = quiz(source_cards=[{"front": "It took her weeks to settle into the new routine.", "back": ""}])
    broken_no_back = quiz(
        question="Which one means to settle into a new place?",  # answer_in_question
        source_cards=[{"front": "She had to settle into a new place.", "back": ""}],
    )

    result = _session([quiz(), quiz(), no_back, broken_no_back])
    stats = result["stats"]["quiz"]

    assert stats["items_using_card_without_back"] == 2
    assert stats["defect_rate_with_gap"] == 0.5
    assert stats["defect_rate_without_gap"] == 0.0
    assert "source_without_back" in checks(result["findings"])


def test_ungrounded_items_do_not_pollute_the_no_back_group():
    """`(source unavailable)` também tem back vazio, mas é outro defeito — já
    reportado por `ungrounded`."""
    ungrounded = quiz(source_cards=[{"front": "(source unavailable)", "back": ""}])

    result = _session([quiz(), ungrounded])
    stats = result["stats"]["quiz"]

    assert "items_using_card_without_back" not in stats
    assert "source_without_back" not in checks(result["findings"])


def test_no_comparison_when_every_card_has_a_back():
    result = _session([quiz(), quiz()])
    assert "defect_rate_with_gap" not in result["stats"]["quiz"]
