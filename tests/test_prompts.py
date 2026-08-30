import json
import re

import pytest

from src.prompts import _answer_positions, build_cloze_prompt, build_quiz_prompt

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


@pytest.mark.parametrize("builder", [build_quiz_prompt, build_cloze_prompt])
def test_output_format_example_is_valid_json(builder):
    """Regression test: the illustrative JSON block in '## Output Format'
    must use single braces (an f-string double-brace escape), not quadruple
    braces - the cloze prompt used to render it doubled ('{{ ... }}'),
    which isn't valid JSON.
    """
    prompt = builder(CARDS, n=1)
    example = re.search(r"Return a JSON object:\n(.*?)\n\n## Card Pool", prompt, re.S).group(1)

    json.loads(example)  # raises json.JSONDecodeError if malformed


# --- item 9: distribuicao da posicao da resposta -------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 10])
def test_answer_positions_is_balanced(n):
    """A atribuicao tem que ser uma permutacao de `[i % 4]`: quando n >= 4 as
    quatro posicoes aparecem, e nenhuma se repete mais que ceil(n/4). E a
    posicao 3 - a que nunca saiu em 122 quizzes medidos - entra no sorteio.
    """
    positions = _answer_positions(n)

    assert len(positions) == n
    assert sorted(positions) == sorted(i % 4 for i in range(n))
    if n >= 4:
        assert set(positions) == {0, 1, 2, 3}


def test_quiz_prompt_assigns_one_answer_position_per_quiz():
    prompt = build_quiz_prompt(CARDS, n=5)

    assignment = re.search(r"\n   (quiz 1 -> \d(?:, quiz \d+ -> \d)*)\n", prompt).group(1)
    pairs = re.findall(r"quiz (\d+) -> (\d)", assignment)

    assert [int(q) for q, _ in pairs] == [1, 2, 3, 4, 5]
    assert sorted(int(p) for _, p in pairs) == [0, 0, 1, 2, 3]


def test_quiz_prompt_puts_answer_index_before_options():
    """O modelo escreve o JSON em ordem. Se `options` vem antes, ele escolhe a
    posicao depois de ja ter posto a resposta em algum lugar - que e o mecanismo
    do vies do item 9. O exemplo do Output Format tem que comprometer o indice
    primeiro.
    """
    prompt = build_quiz_prompt(CARDS, n=3)
    example = re.search(r"Return a JSON object:\n(.*?)\n\n## Card Pool", prompt, re.S).group(1)

    assert example.index('"answer_index"') < example.index('"options"')


# --- item 10: a numeracao do pool vazando para o texto que o aluno le ----------


def test_quiz_prompt_forbids_referring_to_the_pool_in_visible_text():
    """Item 10: 6 em 60 quizzes do pool congelado citavam "Card N" ou "the pool"
    dentro da explicacao, 3 deles no Gemini. A numeracao precisa continuar
    existindo - `used_cards` depende dela -, entao a correcao proibe a citacao,
    nao remove o numero.

    A primeira versao da regra listava as strings proibidas entre aspas,
    incluindo "Card 1". Medida em 2026-08-30 (`v2-item10-gemini`), ela PIOROU o
    defeito: 4 vazamentos contra 3 da linha de base, todos no formato
    `(Card N)`. Instrucao negativa com exemplo literal prima o proprio formato
    que proibe. Por isso o teste guarda a ausencia do literal, nao a presenca.
    """
    prompt = build_quiz_prompt(CARDS, n=3)

    assert "The pool is internal." in prompt
    assert "identify an expression ONLY by quoting the expression itself" in prompt
    assert "## Card Pool (internal" in prompt

    rule = prompt.split("10. The pool is internal.")[1].split("\n\n")[0]
    assert '"Card 1"' not in rule, "a regra volta a primar o formato que proibe"
    assert "Card" not in rule, "nenhum rotulo do bloco do pool pode aparecer na regra"


# --- item 12: o prompt se autocitando -----------------------------------------


def test_quiz_prompt_marks_strategy_examples_as_illustration_only():
    """Item 12: 18 achados de ancoragem em modelo local, 0 em API. A causa
    medida e o proprio prompt se autocitando - o modelo pequeno copia 'sound' e
    'loop in the whole team' das descricoes de estrategia em vez de trabalhar o
    pool, e depois cita `used_cards` para parecer ancorado.

    Os exemplos ficam: sao eles que ensinam a forma de cada estrategia. O que
    muda e que passam a ser declarados como forma, nao conteudo.
    """
    prompt = build_quiz_prompt(CARDS, n=3)

    assert "illustrate the SHAPE of each strategy, never its content" in prompt
    assert "Expressions that appear only in the examples are off limits." in prompt
    # os exemplos continuam la - remove-los custaria a clareza da estrategia
    assert '"sound" = healthy/safe vs noise vs to seem' in prompt
    assert "loop in the whole team" in prompt


# --- item 11: cloze sem resposta certa possivel -------------------------------


def test_cloze_prompt_requires_reading_the_filled_sentence_back():
    """Item 11: 5 exercicios em 56 nasceram sem resposta certa possivel - alvo
    em pessoa incompativel com a frase ('She ... take upon yourself'), e
    alternativa que duplica palavra vizinha a lacuna ('it ___ that' + 'it
    transpired' = 'it it transpired').

    A regra e procedimental de proposito. A primeira versao da regra 10 do quiz
    escrevia o defeito por extenso e o modelo passou a reproduzi-lo.
    """
    prompt = build_cloze_prompt(CARDS, n=3)

    assert "substitute target_expression into the blank and read the whole sentence back" in prompt
    assert "MUST agree with the subject of your sentence" in prompt
    assert "repeats a word already sitting next to the blank" in prompt
