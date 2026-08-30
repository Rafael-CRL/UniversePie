"""Testes das checagens do auditor de exercícios.

O auditor é o que decide se uma mudança de prompt melhorou ou piorou a
qualidade — se as checagens estiverem erradas, a decisão vem errada junto.
"""

import json

import httpx
import pytest

from scripts.audit_exercises import (
    ERROR,
    append_history,
    export_sample,
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
        "source_expression": "settle into",
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


def test_flags_a_quiz_that_does_not_declare_its_anchor():
    """Sem `source_expression` não dá para saber, de forma exata, se o quiz nasceu
    de um card do usuário — sobra a sobreposição de palavras, que é estimativa.
    É o campo que o cloze sempre teve e o quiz não (item 12)."""
    findings = check_quiz_item(quiz(source_expression=""), "quiz", 1, 1)
    assert "empty_source_expression" in checks(findings, WARN)


def test_flags_an_anchor_that_is_not_in_the_source_card():
    """Âncora que não existe no card citado foi inventada pelo modelo, e aí o
    `used_cards` que vem junto não prova ancoragem nenhuma."""
    findings = check_quiz_item(quiz(source_expression="pull yourself together"), "quiz", 1, 1)
    assert "anchor_not_in_source_card" in checks(findings, ERROR)


def test_a_variation_of_the_anchor_is_not_penalised():
    """O quiz DEVE testar uma variação da âncora — outro sentido, forma derivada.
    A checagem é frouxa de propósito: exigir a expressão inteira no enunciado
    reprovaria exatamente o que a premissa n+1 pede."""
    findings = check_quiz_item(
        quiz(
            question="Which sentence uses 'settle' to mean accepting something less than ideal?",
            options=[
                "She settled for a smaller flat.",
                "The dust settled on the shelf.",
                "They settled the bill quickly.",
                "He settled down after the move.",
            ],
            answer_index=0,
        ),
        "quiz",
        1,
        1,
    )
    assert "anchor_absent_from_exercise" not in checks(findings)
    assert "anchor_not_in_source_card" not in checks(findings)


def test_flags_an_exercise_with_nothing_to_do_with_its_own_anchor():
    """Declarou 'settle into' e construiu um quiz sobre 'break the ice'."""
    findings = check_quiz_item(
        quiz(
            question="What does 'break the ice' mean in a first meeting?",
            options=["To start a conversation", "To damage something", "To cool a drink", "To end a meeting"],
            answer_index=0,
        ),
        "quiz",
        1,
        1,
    )
    assert "anchor_absent_from_exercise" in checks(findings, WARN)


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
    """Regra do docs/ai-rules.md que os validadores Pydantic não cobrem."""
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


def test_detects_alternative_that_does_not_fit_the_blank():
    """A avaliação é igualdade de string: uma alternativa que não encaixa marca
    de errado quem respondeu certo. 'it _____ that' + 'it transpired' vira
    'it it transpired that'."""
    findings = check_cloze_item(
        cloze(
            sentence="After weeks of investigation, it _____ that the documents were forged.",
            target_expression="turned out",
            acceptable_alternatives=["it transpired"],
        ),
        "cloze",
        1,
        1,
    )
    assert "does_not_fit_the_blank" in checks(findings, WARN)


def test_ignores_repetition_that_was_already_in_the_sentence():
    """A frase pode ter repetição legítima — 'had had' no mais-que-perfeito. Só
    conta a repetição que o candidato introduziu; cobrar a que já existia reprova
    exercício bom, e como a checagem é ERRO isso barra mudança de prompt boa."""
    findings = check_cloze_item(
        cloze(
            sentence="By the time we arrived, they had had lunch and were ready to _____.",
            target_expression="head out",
            acceptable_alternatives=["take off"],
        ),
        "cloze",
        1,
        1,
    )
    assert "does_not_fit_the_blank" not in checks(findings)


def test_still_flags_repetition_the_candidate_creates_in_a_sentence_that_repeats():
    """A frase tem 'had had' legítimo E o candidato duplica outra palavra. A
    repetição pré-existente não pode mascarar a que o candidato criou."""
    findings = check_cloze_item(
        cloze(
            sentence="They had had enough, and it _____ that nobody was listening.",
            target_expression="it turned out",
        ),
        "cloze",
        1,
        1,
    )
    assert "does_not_fit_the_blank" in checks(findings, ERROR)


def test_flags_repetition_created_across_the_blank():
    """A lacuna quase sempre fica ENTRE palavras. Medir a frase original trocando
    a lacuna por espaço encostava as vizinhas e inventava uma repetição que
    entrava na linha de base, mascarando a real — 'to ___ to' + 'talk to' passava
    limpo, que é exatamente a forma do defeito do item 11."""
    findings = check_cloze_item(
        cloze(
            sentence="She decided to _____ to her boss about the delay.",
            target_expression="talk to",
            acceptable_alternatives=[],
        ),
        "cloze",
        1,
        1,
    )
    assert "does_not_fit_the_blank" in checks(findings, ERROR)


def test_pre_existing_repetition_of_the_same_word_does_not_mask_a_new_one():
    """A contagem é por ocorrência, não por conjunto de palavras: a frase já tem
    'It it' e o candidato cria um segundo. Com conjunto, o pré-existente apagava
    o novo."""
    findings = check_cloze_item(
        cloze(
            sentence="It it was late. It _____ that nobody cared.",
            target_expression="it emerged",
            acceptable_alternatives=[],
        ),
        "cloze",
        1,
        1,
    )
    assert "does_not_fit_the_blank" in checks(findings, ERROR)


def test_detects_target_in_the_wrong_person():
    """'take upon yourself' numa frase sobre 'she' sai agramatical quando
    preenchida, e não existe resposta certa possível."""
    findings = check_cloze_item(
        cloze(
            sentence="She was hesitant to _____ the enormous task.",
            target_expression="take upon yourself",
            acceptable_alternatives=["shoulder"],
        ),
        "cloze",
        1,
        1,
    )
    assert "person_mismatch" in checks(findings, ERROR)


def test_imperative_sentences_have_an_implied_you():
    """'Please, don't _____ about the results; we don't have data' é imperativo:
    o 'we' da oração seguinte não governa o alvo."""
    findings = check_cloze_item(
        cloze(
            sentence="Please, don't _____ about the election results; we don't have enough data yet.",
            target_expression="get ahead of yourself",
            acceptable_alternatives=["jump to conclusions"],
        ),
        "cloze",
        1,
        1,
    )
    assert "person_mismatch" not in checks(findings)


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


def test_compare_reports_ignores_raw_files_matched_by_the_glob(tmp_path):
    """`--compare docs/audit/baseline-*.json` — a forma que a documentação
    recomenda — casa também os .raw.json, que só têm meta e records. Antes eles
    viravam linha de '0 itens · 0% limpos' com o nome de um run que aparecia
    logo acima com os números certos, sugerindo regressão que não houve."""
    a = _report(tmp_path, "groq", "groq/openai-gpt-oss-20b", 1.0, 0, [])
    raw = tmp_path / "groq.raw.json"
    raw.write_text(json.dumps({"meta": {"tag": "groq"}, "records": []}), encoding="utf-8")

    table = compare_reports([a, str(raw)])

    assert "| groq | groq/openai-gpt-oss-20b | 3 | 100% | 0 |" in table
    assert "| 0 | 0% |" not in table
    assert "Ignorados" in table and "groq.raw.json" in table


def test_compare_reports_says_so_when_nothing_comparable_was_passed(tmp_path):
    raw = tmp_path / "so-cru.raw.json"
    raw.write_text(json.dumps({"meta": {}, "records": []}), encoding="utf-8")
    assert "Nenhum relatório" in compare_reports([str(raw)])


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


# --- dados para comparação posterior ---------------------------------------

def test_cost_is_aggregated_per_run():
    """Latência sozinha não diz se um modelo rendeu mais por token."""
    result = analyze([
        {"mode": "quiz", "batch": 1, "requested": 2, "latency_s": 3.0,
         "usage": {"prompt_tokens": 1200, "completion_tokens": 2200, "total_tokens": 3400},
         "payload": {"quizzes": [quiz(), quiz()], "total": 2}},
    ])

    assert result["cost"]["total_tokens"] == 3400
    assert result["cost"]["tokens_per_item"] == 1700
    assert result["cost"]["seconds_per_item"] == 1.5


def test_history_accumulates_one_line_per_run(tmp_path):
    """Os relatórios são arquivos soltos; sem o histórico não dá para perguntar
    se algo melhorou entre um run e outro."""
    result = analyze([{"mode": "quiz", "batch": 1, "requested": 1, "payload": {"quizzes": [quiz()], "total": 1}}])

    for tag in ("antes", "depois"):
        append_history(tmp_path, {"tag": tag, "provider": "groq/x", "timestamp": "2026-08-29 18:00"}, result)

    lines = (tmp_path / "history.jsonl").read_text(encoding="utf-8").strip().split("\n")
    assert [json.loads(l)["tag"] for l in lines] == ["antes", "depois"]
    assert json.loads(lines[0])["summary"]["items_audited"] == 1


def test_sample_export_hides_which_model_produced_each_exercise(tmp_path):
    """Saber que o exercício veio de um modelo de 4B contamina a avaliação."""
    records = [
        {"mode": "quiz", "batch": 1, "provider": "ollama/gemma4:e4b",
         "payload": {"quizzes": [quiz(), quiz()], "total": 2}},
        {"mode": "quiz", "batch": 2, "provider": "gemini/gemini-2.5-flash",
         "payload": {"quizzes": [quiz()], "total": 1}},
    ]

    path = tmp_path / "amostra.json"
    assert export_sample(records, 10, path) == 3

    sample = json.loads(path.read_text(encoding="utf-8"))
    assert all("origem" not in entry and "provider" not in json.dumps(entry) for entry in sample)
    assert all(entry["sua_nota"] is None for entry in sample)

    gabarito = json.loads((tmp_path / "amostra-gabarito.json").read_text(encoding="utf-8"))
    assert sorted(gabarito) == ["1", "2", "3"]
    assert set(gabarito.values()) == {"ollama/gemma4:e4b", "gemini/gemini-2.5-flash"}


def test_both_modes_share_one_event_loop(tmp_path, monkeypatch):
    """`--mode both --source direct` roda os dois modos no mesmo event loop.

    Havia um `asyncio.run` por modo. `GeminiProvider._client` e cache de classe,
    entao o cliente `aio` ficava preso ao loop do quiz, fechado antes do cloze
    comecar, e toda rodada perdia uma tentativa com "Event loop is closed" na
    virada - medido em 2026-08-30 no run `v2-item9-gemini`.
    """
    import asyncio

    from scripts import audit_exercises as audit

    loops: list[asyncio.AbstractEventLoop] = []

    async def fake_collect_direct(mode, *args, **kwargs):
        loops.append(asyncio.get_running_loop())
        return [{"mode": mode, "batch": 1, "requested": 1, "provider": "fake/fake", "items": []}]

    monkeypatch.setattr(audit, "collect_direct", fake_collect_direct)

    cards = tmp_path / "pool.json"
    cards.write_text(json.dumps([["settle into", "acomodar-se"]]), encoding="utf-8")

    audit.main([
        "--mode", "both", "--provider", "fake", "--cards", str(cards),
        "--out-dir", str(tmp_path), "--tag", "loop-check",
        "--runs", "1", "--n", "1", "--cooldown", "0", "--fail-on", "never",
    ])

    assert len(loops) == 2, "os dois modos tem que ter chamado collect_direct"
    assert loops[0] is loops[1], "quiz e cloze rodaram em event loops diferentes"


def test_short_batch_at_the_token_ceiling_is_reported_as_truncation():
    """Receber menos itens que o pedido tem duas causas com correcoes opostas:
    item descartado pelo Pydantic, ou saida cortada no teto de tokens. A
    mensagem antiga culpava o backend nas duas.

    Medido em 2026-08-30, run `v2-item1112-groq`: os dois batches curtos bateram
    em `completion_tokens` 4096/4096 exatos; os outros quatro ficaram entre 2471
    e 3536.
    """
    findings = check_batch(
        "quiz", 1, [quiz(), quiz()], requested=5, total_field=2,
        usage={"completion_tokens": 4096}, max_completion_tokens=4096,
    )

    assert "output_truncated" in checks(findings)
    assert "count_mismatch" not in checks(findings)
    assert "4096" in next(f.message for f in findings if f.check == "output_truncated")


def test_short_batch_below_the_ceiling_still_blames_dropped_items():
    findings = check_batch(
        "quiz", 1, [quiz(), quiz()], requested=5, total_field=2,
        usage={"completion_tokens": 2471}, max_completion_tokens=4096,
    )

    assert "count_mismatch" in checks(findings)
    assert "output_truncated" not in checks(findings)


def test_short_batch_without_usage_falls_back_to_the_old_message():
    """Provedor que nao reporta usage, ou reanalise de um raw antigo que nao
    guardou o teto: sem os dois numeros nao da para afirmar truncamento.
    """
    findings = check_batch("quiz", 1, [quiz(), quiz()], requested=5, total_field=2)

    assert "count_mismatch" in checks(findings)
    assert "output_truncated" not in checks(findings)


@pytest.mark.parametrize(
    "target",
    ["quit while you're ahead", "you'd better believe it", "before you've settled in", "take upon yourself"],
)
def test_second_person_target_is_caught_through_the_contraction(target):
    """`you're` nao casava com `\\byour\\b`: o apostrofo fecha a borda de palavra
    antes do "r". Achado na saida ao vivo do servidor em 2026-08-30 - "many
    investors quit while you're ahead" passou batido.
    """
    findings = check_cloze_item(
        cloze(sentence="She was hesitant to _____ last year.", target_expression=target),
        "cloze", 1, 1,
    )

    assert "person_mismatch" in checks(findings, ERROR)


def test_imperative_with_a_contraction_target_is_still_allowed():
    """O imperativo tem 'you' implicito e continua excecao - a correcao da
    contracao nao pode transformar isso em falso positivo.
    """
    findings = check_cloze_item(
        cloze(sentence="Don't _____ before the deal closes.", target_expression="quit while you're ahead"),
        "cloze", 1, 1,
    )

    assert "person_mismatch" not in checks(findings)
