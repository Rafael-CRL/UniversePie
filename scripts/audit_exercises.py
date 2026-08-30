#!/usr/bin/env python3
"""Auditoria de qualidade dos exercícios gerados pelo Gemini.

Coleta rodadas de `/api/quiz-session` e/ou `/api/cloze-session`, roda um
conjunto de checagens determinísticas sobre cada exercício e escreve três
arquivos:

  <prefixo>.md        relatório legível (com a resposta correta marcada)
  <prefixo>.json      findings + estatísticas, para comparar versões de prompt
  <prefixo>.raw.json  respostas cruas da API, para reanalisar sem gastar cota

Sai com código != 0 quando encontra findings de severidade ERRO, para servir
de portão ao mexer nos prompts (`skills/prompt-review.md`).

Roda contra o servidor (`--source http`) ou chamando a camada de geração
direto (`--source direct`), o que permite trocar de provedor de IA sem
reiniciar o uvicorn e auditar modelos locais sem gastar cota de API.

Uso:
    python scripts/audit_exercises.py                          # 3 rodadas de quiz, n=5, via HTTP
    python scripts/audit_exercises.py --provider ollama --model gemma4:e4b
    python scripts/audit_exercises.py --provider groq --tag groq-gptoss --mode both
    python scripts/audit_exercises.py --save-cards docs/audit/pool.json --runs 0
    python scripts/audit_exercises.py --provider ollama --cards docs/audit/pool.json
    python scripts/audit_exercises.py --compare docs/audit/gemini.json docs/audit/ollama.json
    python scripts/audit_exercises.py --from-raw docs/audit/run.raw.json
    python scripts/audit_exercises.py --list-providers
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import random
import json
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://localhost:14567"
ENDPOINTS = {
    "quiz": ("/api/quiz-session", "quizzes"),
    "cloze": ("/api/cloze-session", "exercises"),
}
QUIZ_TYPES = ("discrimination", "production", "interference", "polysemy", "contextual")
# services.build_items usa este placeholder quando `used_cards` não mapeia
# para nenhum card do pool — ou seja, o exercício não está ancorado no deck.
UNAVAILABLE_SOURCE = "(source unavailable)"

ERROR, WARN, INFO = "error", "warn", "info"
SEVERITY_ORDER = {INFO: 1, WARN: 2, ERROR: 3}
SEVERITY_LABEL = {ERROR: "ERRO", WARN: "ALERTA", INFO: "INFO"}


# --------------------------------------------------------------------------
# Normalização de texto
# --------------------------------------------------------------------------

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for",
    "with", "that", "this", "it", "is", "are", "was", "were", "be", "been",
    "you", "your", "he", "she", "they", "we", "i", "as", "by", "from", "not",
    "do", "does", "did", "has", "have", "had", "will", "would", "can", "could",
    "what", "which", "when", "who", "how", "why", "something", "someone",
}


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """lowercase, sem acentos, sem pontuação, espaços colapsados."""
    return re.sub(r"\s+", " ", _PUNCT.sub(" ", strip_accents(text or "").lower())).strip()


def content_tokens(text: str) -> set[str]:
    return {t for t in normalize(text).split() if len(t) > 2 and t not in _STOPWORDS}


def contains_phrase(haystack: str, needle: str) -> bool:
    """Substring com fronteira de palavra, sobre texto normalizado."""
    h, n = normalize(haystack), normalize(needle)
    if len(n) < 3:
        return False
    return f" {n} " in f" {h} "


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------

@dataclass
class Finding:
    check: str
    severity: str
    message: str
    mode: str = ""
    batch: int = 0
    item: int = 0

    @property
    def where(self) -> str:
        if not self.mode:
            return "sessão"
        if self.item:
            return f"rodada {self.batch} · item {self.item}"
        return f"rodada {self.batch}"


class Collector:
    """Acumula findings já carimbados com a localização do item."""

    def __init__(self, mode: str = "", batch: int = 0, item: int = 0):
        self.mode, self.batch, self.item = mode, batch, item
        self.findings: list[Finding] = []

    def add(self, check: str, severity: str, message: str) -> None:
        self.findings.append(Finding(check, severity, message, self.mode, self.batch, self.item))


# --------------------------------------------------------------------------
# Padrões de vazamento e de recognition passivo
# --------------------------------------------------------------------------

# O exercício não pode revelar a mecânica interna (pool, deck, numeração de
# cards): o aluno vê só a pergunta, e "Card 6" ou "from the cards" quebra a
# imersão e às vezes entrega a resposta.
META_LEAK_PATTERNS = [
    (r"\bcards?\s*\d+\b", "referência numerada a card"),
    (r"\bfrom the (cards?|pool|deck)\b", "referência explícita ao pool de cards"),
    (r"\bin the (pool|deck|card pool)\b", "referência explícita ao pool de cards"),
    (r"\b(flashcards?|anki)\b", "menção ao Anki/flashcard"),
    (r"\bthe learner\b", "fala sobre o aluno em terceira pessoa"),
    (r"\bused_cards\b", "vazamento de campo do JSON"),
]

# Contar antecipadamente que a questão é uma armadilha de L1 entrega a
# resposta: basta descartar a opção que "parece" tradução literal.
TELEGRAPH_PATTERNS = [
    (r"\b(brazilian|portuguese)\b[^.?!]{0,80}\b(speaker|learner|translat|mistak)", "antecipa a armadilha de L1"),
    (r"\bliteral translation\b", "antecipa a armadilha de L1"),
    (r"\bfalse (cognate|friend)\b", "antecipa a armadilha de L1"),
    (r"\bcommon (mistake|error)\b", "antecipa que a questão é uma pegadinha"),
]

# "O que X significa?" é reconhecimento passivo — proibido explicitamente no
# tipo `production`, e contra a filosofia do projeto nos demais. `interference`
# é a exceção: o próprio prompt usa esse formato como exemplo.
PASSIVE_PATTERN = re.compile(
    r"(what does\b[^?]{0,80}\bmean|the meaning of\b|\bactually mean|\bmeans\s*:)", re.IGNORECASE
)

HINT_GIVEAWAY = re.compile(r"\b(starts?|begins?) with\b|\bfirst letter\b", re.IGNORECASE)


def scan_patterns(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    hits = []
    for pattern, label in patterns:
        match = re.search(pattern, text or "", re.IGNORECASE)
        if match:
            hits.append(f"{label} — '{match.group(0).strip()}'")
    return hits


# --------------------------------------------------------------------------
# Checagens por item
# --------------------------------------------------------------------------

def source_text(item: dict) -> str:
    cards = item.get("source_cards") or []
    return " ".join(f"{c.get('front', '')} {c.get('back', '')}" for c in cards)


def check_grounding(col: Collector, item: dict, anchor: str) -> None:
    """A promessa do produto é gerar em cima do que o usuário já estudou.

    `anchor` é o texto que deveria vir do card (resposta correta / expressão-alvo).
    """
    cards = item.get("source_cards") or []
    if not cards or all(c.get("front") == UNAVAILABLE_SOURCE for c in cards):
        col.add("ungrounded", ERROR, "Sem card-fonte: `used_cards` veio vazio ou fora do range do pool.")
        return

    text = source_text(item)
    if not (content_tokens(anchor) & content_tokens(text)):
        col.add(
            "weak_grounding",
            WARN,
            f"Zero sobreposição léxica entre o que é testado ('{anchor[:60]}') e os cards-fonte.",
        )


def check_quiz_item(item: dict, mode: str, batch: int, index: int) -> list[Finding]:
    col = Collector(mode, batch, index)

    question = item.get("question", "") or ""
    options = item.get("options") or []
    explanation = item.get("explanation", "") or ""
    quiz_type = item.get("quiz_type", "") or ""
    answer_index = item.get("answer_index")
    answer = options[answer_index] if isinstance(answer_index, int) and 0 <= answer_index < len(options) else ""

    if not question.strip():
        col.add("empty_question", ERROR, "Pergunta vazia.")
    if len(options) != 4:
        col.add("option_count", ERROR, f"Esperado 4 opções, recebeu {len(options)}.")
    if any(not str(o).strip() for o in options):
        col.add("empty_option", ERROR, "Alguma opção veio vazia.")

    normalized = [normalize(str(o)) for o in options]
    duplicates = [o for o, c in collections.Counter(normalized).items() if c > 1 and o]
    if duplicates:
        col.add("duplicate_options", ERROR, f"Opções repetidas dentro do mesmo quiz: {duplicates}.")

    # A pergunta contendo a resposta literal transforma o quiz em leitura.
    if answer and contains_phrase(question, answer):
        col.add("answer_in_question", ERROR, f"A resposta ('{answer}') aparece no enunciado.")

    for hit in scan_patterns(question, META_LEAK_PATTERNS):
        col.add("meta_leak_question", ERROR, f"Vazamento no enunciado: {hit}.")
    for opt in options:
        for hit in scan_patterns(str(opt), META_LEAK_PATTERNS):
            col.add("meta_leak_option", ERROR, f"Vazamento numa opção: {hit}.")
    for hit in scan_patterns(explanation, META_LEAK_PATTERNS):
        col.add("meta_leak_explanation", WARN, f"Vazamento na explicação: {hit}.")

    for hit in scan_patterns(question, TELEGRAPH_PATTERNS):
        col.add("telegraphed_trap", WARN, f"Enunciado entrega a estratégia: {hit}.")

    if quiz_type != "interference" and PASSIVE_PATTERN.search(question):
        severity = ERROR if quiz_type == "production" else WARN
        detail = "proibido no tipo `production`" if quiz_type == "production" else "reconhecimento passivo"
        col.add("passive_recognition", severity, f"Enunciado pergunta o significado ({detail}).")

    if quiz_type and quiz_type not in QUIZ_TYPES:
        col.add("unknown_quiz_type", ERROR, f"quiz_type fora do enum: '{quiz_type}'.")

    if len(explanation.strip()) < 40:
        col.add("thin_explanation", INFO, "Explicação curta demais para ensinar algo.")

    # O enunciado entra na âncora: em quiz `contextual` a expressão do card
    # aparece na situação descrita, e a resposta certa é uma paráfrase.
    check_grounding(col, item, f"{item.get('concept', '')} {answer} {question}")
    return col.findings


def check_cloze_item(item: dict, mode: str, batch: int, index: int) -> list[Finding]:
    col = Collector(mode, batch, index)

    sentence = item.get("sentence", "") or ""
    target = item.get("target_expression", "") or ""
    alternatives = item.get("acceptable_alternatives") or []
    hint = item.get("hint", "") or ""
    commonality = item.get("commonality", "") or ""
    context_note = (item.get("context_note") or "").strip()
    explanation = item.get("explanation", "") or ""

    blanks = re.findall(r"_{2,}", sentence)
    if not blanks:
        col.add("missing_blank", ERROR, "A frase não tem lacuna (`_____`).")
    elif len(blanks) > 1:
        col.add("multiple_blanks", ERROR, f"A frase tem {len(blanks)} lacunas; o frontend espera uma.")

    if not target.strip():
        col.add("empty_target", ERROR, "target_expression vazio.")

    sentence_without_blank = re.sub(r"_{2,}", " ", sentence)
    if target and contains_phrase(sentence_without_blank, target):
        col.add("target_in_sentence", ERROR, f"A resposta ('{target}') aparece na própria frase.")
    if target and contains_phrase(hint, target):
        col.add("target_in_hint", ERROR, f"A dica entrega a resposta ('{target}').")
    # A avaliação é por igualdade de string: se a expressão não encaixa na frase
    # exatamente como está escrita, o exercício marca de errado quem acertou.
    for candidate, role, severity in (
        [(target, "target_expression", ERROR)]
        + [(str(a), "acceptable_alternatives", WARN) for a in alternatives]
    ):
        filled = re.sub(r"_{2,}", candidate, sentence, count=1)
        repeated = re.search(r"\b(\w+)\s+\1\b", filled, re.IGNORECASE)
        if repeated and candidate:
            col.add(
                "does_not_fit_the_blank",
                severity,
                f"'{candidate}' na lacuna repete uma palavra da frase "
                f"('{repeated.group(1)} {repeated.group(1)}'), em {role}.",
            )

    # 'take upon yourself' numa frase sobre 'she' produz "She was hesitant to
    # take upon yourself...". O imperativo é exceção: tem 'you' implícito.
    if re.search(r"\b(your|yourself|yourselves)\b", target, re.IGNORECASE) and not re.search(
        r"\byou(r|rs|rself|rselves)?\b", sentence, re.IGNORECASE
    ):
        # Só o trecho antes da lacuna: "Please, don't _____ ...; we don't have
        # data" é imperativo, e o 'we' da oração seguinte não governa o alvo.
        before_blank = re.split(r"_{2,}", sentence, maxsplit=1)[0]
        other_subject = re.search(
            r"\b(he|she|they|it|i|we|him|her|them|me|us|his|their|my|our)\b", before_blank, re.IGNORECASE
        )
        if other_subject:
            col.add(
                "person_mismatch",
                ERROR,
                f"A expressão-alvo está na 2ª pessoa ('{target}') mas a frase fala de "
                f"'{other_subject.group(0)}' — preenchida, sai agramatical.",
            )

    if HINT_GIVEAWAY.search(hint):
        col.add("hint_spells_answer", WARN, "Dica do tipo 'starts with' — o prompt pede dica semântica.")
    if not hint.strip():
        col.add("empty_hint", WARN, "Sem dica.")

    normalized_alts = [normalize(str(a)) for a in alternatives]
    if normalize(target) in normalized_alts:
        col.add("alternative_equals_target", WARN, "acceptable_alternatives repete o próprio target.")
    repeated = [a for a, c in collections.Counter(normalized_alts).items() if c > 1 and a]
    if repeated:
        col.add("duplicate_alternatives", WARN, f"Alternativas repetidas: {repeated}.")
    if not alternatives:
        # A avaliação é string matching: sem alternativas, sinônimo legítimo vira erro.
        col.add("no_alternatives", WARN, "Sem acceptable_alternatives — o prompt pede de 1 a 3.")
    elif len(alternatives) > 3:
        col.add("too_many_alternatives", INFO, f"{len(alternatives)} alternativas (o prompt pede até 3).")

    # Regra do docs/ai-rules.md que os modelos Pydantic não conseguem cobrir.
    if commonality and commonality != "common" and not context_note:
        col.add("missing_context_note", ERROR, f"commonality='{commonality}' exige context_note explicando o porquê.")
    if commonality == "common" and context_note:
        col.add("context_note_on_common", INFO, "context_note preenchido numa expressão 'common' (o prompt pede vazio).")

    for field_name, text, severity in (
        ("sentence", sentence, ERROR),
        ("hint", hint, ERROR),
        ("context_note", context_note, WARN),
        ("explanation", explanation, WARN),
    ):
        for hit in scan_patterns(text, META_LEAK_PATTERNS):
            col.add(f"meta_leak_{field_name}", severity, f"Vazamento em {field_name}: {hit}.")

    if len(explanation.strip()) < 40:
        col.add("thin_explanation", INFO, "Explicação curta demais para ensinar algo.")

    check_grounding(col, item, f"{item.get('concept', '')} {target} {sentence}")
    return col.findings


# --------------------------------------------------------------------------
# Checagens por lote e agregadas
# --------------------------------------------------------------------------

def check_batch(mode: str, batch: int, items: list[dict], requested: int, total_field) -> list[Finding]:
    col = Collector(mode, batch)

    if len(items) != requested:
        # services.build_items descarta silenciosamente itens que não passam no
        # Pydantic — receber menos que `n` é o único sintoma visível disso.
        col.add(
            "count_mismatch",
            WARN,
            f"Pedidos {requested} itens, recebidos {len(items)} (itens inválidos descartados pelo backend?).",
        )
    if isinstance(total_field, int) and total_field != len(items):
        col.add("total_mismatch", ERROR, f"Campo `total`={total_field} não bate com {len(items)} itens.")

    if mode == "quiz":
        types = [i.get("quiz_type", "") for i in items]
        for a, b in zip(types, types[1:]):
            if a and a == b:
                col.add("consecutive_same_type", WARN, f"Tipos consecutivos repetidos ('{a}') — o prompt proíbe.")
                break

        # Reaproveitar distratores do pool é intencional; o mesmo texto em 3+
        # quizzes do mesmo lote já vira preguiça de geração.
        seen = collections.Counter()
        for item in items:
            seen.update({normalize(str(o)) for o in (item.get("options") or [])})
        for opt, count in seen.items():
            if count >= 3 and opt:
                col.add("recycled_option", INFO, f"Opção '{opt}' reaparece em {count} quizzes deste lote.")

    return col.findings


def aggregate_quiz(items: list[dict]) -> tuple[dict, list[Finding]]:
    col = Collector()
    stats: dict = {}
    if not items:
        return stats, col.findings

    positions = collections.Counter(
        i.get("answer_index") for i in items if isinstance(i.get("answer_index"), int)
    )
    stats["answer_positions"] = {str(k): positions.get(k, 0) for k in range(4)}
    if positions:
        top_pos, top_count = positions.most_common(1)[0]
        share = top_count / len(items)
        stats["answer_position_top_share"] = round(share, 2)
        if len(items) >= 8 and share > 0.5:
            col.add(
                "answer_position_bias",
                WARN,
                f"{top_count}/{len(items)} respostas na posição {top_pos} (esperado ~25%).",
            )

    longest = 0
    measured = 0
    for item in items:
        options = [str(o) for o in (item.get("options") or [])]
        idx = item.get("answer_index")
        if len(options) < 2 or not isinstance(idx, int) or not 0 <= idx < len(options):
            continue
        measured += 1
        lengths = [len(o) for o in options]
        if lengths[idx] == max(lengths) and lengths.count(max(lengths)) == 1:
            longest += 1
    if measured:
        rate = longest / measured
        stats["longest_option_is_answer"] = round(rate, 2)
        if measured >= 4 and rate > 0.5:
            col.add(
                "longest_answer_bias",
                WARN,
                f"Em {longest}/{measured} quizzes a resposta é a opção mais longa (esperado ~25%) — "
                "dá para acertar por formato, sem saber inglês.",
            )

    type_counts = collections.Counter(i.get("quiz_type", "?") for i in items)
    stats["quiz_types"] = dict(type_counts)
    missing = [t for t in QUIZ_TYPES if t not in type_counts]
    stats["strategy_coverage"] = f"{len(QUIZ_TYPES) - len(missing)}/{len(QUIZ_TYPES)}"
    if missing and len(items) >= len(QUIZ_TYPES):
        col.add("strategy_coverage", INFO, f"Estratégias não exercitadas na sessão: {', '.join(missing)}.")

    return stats, col.findings


def aggregate_cloze(items: list[dict]) -> tuple[dict, list[Finding]]:
    col = Collector()
    stats: dict = {}
    if not items:
        return stats, col.findings

    counts = collections.Counter(i.get("commonality", "?") for i in items)
    stats["commonality"] = dict(counts)
    if len(items) >= 6 and len(counts) == 1 and "common" in counts:
        col.add(
            "commonality_uniform",
            INFO,
            "Todas as expressões vieram como 'common' — sinal de inflação da métrica (AI_RULES pede honestidade).",
        )

    alt_counts = [len(i.get("acceptable_alternatives") or []) for i in items]
    stats["alternatives_avg"] = round(sum(alt_counts) / len(alt_counts), 2)
    return stats, col.findings


def stratify_by_source_completeness(
    mode: str, located: list[tuple[int, int, dict]], flagged: set[tuple[str, int, int]]
) -> tuple[dict, list[Finding]]:
    """Compara a taxa de defeito entre exercícios construídos sobre cards sem
    back e os demais.

    38% do deck de teste não tem back, e o prompt não diz o que fazer nesse
    caso — o modelo recebe uma frase solta e decide sozinho. Sem separar os
    dois grupos, o efeito disso fica diluído na média e não dá para saber se
    vale escrever uma regra no prompt.
    """
    col = Collector(mode)
    with_gap: list[bool] = []
    without_gap: list[bool] = []

    for batch, index, item in located:
        cards = [c for c in (item.get("source_cards") or []) if c.get("front") != UNAVAILABLE_SOURCE]
        if not cards:
            # Item sem fonte real já é reportado por `ungrounded`; incluí-lo aqui
            # contaminaria o grupo "sem back" com um defeito de outra natureza.
            continue
        is_flagged = (mode, batch, index) in flagged
        (with_gap if any(not (c.get("back") or "").strip() for c in cards) else without_gap).append(is_flagged)

    if not with_gap or not without_gap:
        return {}, col.findings

    rate_with = sum(with_gap) / len(with_gap)
    rate_without = sum(without_gap) / len(without_gap)
    stats = {
        "items_using_card_without_back": len(with_gap),
        "defect_rate_with_gap": round(rate_with, 2),
        "defect_rate_without_gap": round(rate_without, 2),
    }

    gap = rate_with - rate_without
    severity = WARN if (gap > 0.2 and len(with_gap) >= 3) else INFO
    col.add(
        "source_without_back",
        severity,
        f"Exercícios que usaram card sem back falharam {rate_with:.0%} das vezes "
        f"({len(with_gap)} itens) contra {rate_without:.0%} dos demais ({len(without_gap)} itens).",
    )
    return stats, col.findings


def aggregate_repeats(mode: str, items: list[dict]) -> list[Finding]:
    """Conceitos repetidos entre rodadas medem a diversidade real do pool."""
    col = Collector(mode)
    concepts = collections.Counter(normalize(i.get("concept", "")) for i in items if i.get("concept"))
    for concept, count in concepts.most_common():
        if count > 1:
            col.add("repeated_concept", INFO, f"Conceito '{concept}' testado {count}x na mesma auditoria.")
    return col.findings


# --------------------------------------------------------------------------
# Coleta
# --------------------------------------------------------------------------

def describe_error(exc: Exception) -> str:
    """O `detail` do FastAPI é a parte útil ('Anki não está aberto', etc.);
    o texto padrão do httpx só repete o status code."""
    detail = ""
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = (exc.response.text or "")[:200]
        return f"HTTP {exc.response.status_code}: {detail or exc}"
    return f"{type(exc).__name__}: {exc}"


def load_cards(path: str | Path) -> list[tuple[str, str]]:
    """Pool congelado em arquivo: `[["front", "back"], ...]`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [tuple(c) if isinstance(c, list) else (c["front"], c["back"]) for c in data]


async def snapshot_cards(n: int, path: str | Path) -> list[tuple[str, str]]:
    """Congela um pool real do Anki em arquivo.

    Sem isso cada rodada sorteia cards diferentes, e a comparação entre
    provedores mistura a diferença de modelo com a diferença de material.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from src import anki_client

    await anki_client.startup()
    try:
        cards = await anki_client.get_card_pool(n)
    finally:
        await anki_client.shutdown()

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps([list(c) for c in cards], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pool de {len(cards)} cards salvo em {path}", flush=True)
    return cards


async def collect_direct(
    mode: str,
    runs: int,
    n: int,
    provider_name: str | None,
    model: str | None,
    timeout: float,
    cards_path: str | None,
    cooldown: int,
    retries: int,
) -> list[dict]:
    """Chama a geração no processo, sem passar pelo servidor.

    Usa as mesmas funções que os endpoints usam (`generate_*_session` e
    `build_items`), então o que é auditado continua sendo o que o usuário
    receberia — só que com o provedor escolhido por rodada.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from src import anki_client
    from src.ai_client import generate_cloze_session, generate_quiz_session
    from src.models import ClozeItem, QuizItem
    from src.providers import get_provider
    from src.services import build_items

    provider = get_provider(provider_name, model, timeout_s=timeout)
    ready, reason = provider.ready()
    if not ready:
        raise SystemExit(reason)

    generate_fn = generate_quiz_session if mode == "quiz" else generate_cloze_session
    item_cls = QuizItem if mode == "quiz" else ClozeItem
    key = ENDPOINTS[mode][1]

    fixed_cards = load_cards(cards_path) if cards_path else None
    if fixed_cards is None:
        await anki_client.startup()

    results: list[dict] = []
    try:
        for i in range(runs):
            print(f"[{mode}] rodada {i + 1}/{runs} via {provider.label}...", flush=True)
            record = {"mode": mode, "batch": i + 1, "requested": n, "provider": provider.label}

            for attempt in range(retries + 1):
                started = time.monotonic()
                try:
                    cards = fixed_cards or await anki_client.get_card_pool(n)
                    raw_items = await generate_fn(cards, n, provider)
                    items = build_items(item_cls, raw_items, cards)
                    record["latency_s"] = round(time.monotonic() - started, 2)
                    record["usage"] = provider.last_usage
                    # O pool inteiro, não só os cards citados: permite reanalisar
                    # depois perguntas que hoje não sabemos fazer (o modelo ignorou
                    # cards? preferiu os que têm back?).
                    record["pool"] = [list(c) for c in cards]
                    record["payload"] = {
                        key: [item.model_dump() for item in items],
                        "total": len(items),
                    }
                    record.pop("error", None)
                    print(f"  ok em {record['latency_s']}s ({len(items)} itens)", flush=True)
                    break
                except Exception as exc:
                    record["latency_s"] = round(time.monotonic() - started, 2)
                    record["error"] = describe_error(exc)
                    if attempt < retries:
                        backoff = max(cooldown, 5) * (attempt + 1)
                        print(f"  falhou ({record['error']}); nova tentativa em {backoff}s", flush=True)
                        time.sleep(backoff)
                    else:
                        print(f"  falhou definitivamente: {record['error']}", flush=True)

            results.append(record)
            if i < runs - 1 and "payload" in record and cooldown:
                print(f"  aguardando {cooldown}s (RPM)...", flush=True)
                time.sleep(cooldown)
    finally:
        if fixed_cards is None:
            await anki_client.shutdown()

    return results


def collect_http(base_url: str, mode: str, runs: int, n: int, cooldown: int, retries: int, timeout: float) -> list[dict]:
    path, _ = ENDPOINTS[mode]
    url = f"{base_url.rstrip('/')}{path}"
    results: list[dict] = []

    with httpx.Client(timeout=timeout) as client:
        for i in range(runs):
            print(f"[{mode}] rodada {i + 1}/{runs}...", flush=True)
            record = {"mode": mode, "batch": i + 1, "requested": n}
            for attempt in range(retries + 1):
                started = time.monotonic()
                try:
                    response = client.get(url, params={"n": n})
                    response.raise_for_status()
                    record["latency_s"] = round(time.monotonic() - started, 2)
                    record["payload"] = response.json()
                    print(f"  ok em {record['latency_s']}s", flush=True)
                    break
                except Exception as exc:  # rede, 5xx, timeout, JSON inválido
                    record["latency_s"] = round(time.monotonic() - started, 2)
                    record["error"] = describe_error(exc)
                    if attempt < retries:
                        backoff = cooldown * (attempt + 1)
                        print(f"  falhou ({record['error']}); nova tentativa em {backoff}s", flush=True)
                        time.sleep(backoff)
                    else:
                        print(f"  falhou definitivamente: {record['error']}", flush=True)
            results.append(record)

            # Sem espera depois do último lote: cooldown existe só por RPM.
            if i < runs - 1 and "payload" in record and cooldown:
                print(f"  aguardando {cooldown}s (RPM)...", flush=True)
                time.sleep(cooldown)

    return results


# --------------------------------------------------------------------------
# Análise
# --------------------------------------------------------------------------

def analyze(records: list[dict]) -> dict:
    findings: list[Finding] = []
    located_by_mode: dict[str, list[tuple[int, int, dict]]] = collections.defaultdict(list)
    batches: list[dict] = []
    failed = 0

    for record in records:
        mode = record["mode"]
        batch = record["batch"]
        if "payload" not in record:
            failed += 1
            findings.append(
                Finding("request_failed", ERROR, f"Requisição falhou: {record.get('error', '?')}", mode, batch)
            )
            batches.append({**{k: v for k, v in record.items() if k != "payload"}, "items": []})
            continue

        _, key = ENDPOINTS[mode]
        payload = record["payload"] or {}
        items = payload.get(key) or []
        checker = check_quiz_item if mode == "quiz" else check_cloze_item

        for idx, item in enumerate(items, start=1):
            findings.extend(checker(item, mode, batch, idx))
        findings.extend(check_batch(mode, batch, items, record.get("requested", len(items)), payload.get("total")))

        located_by_mode[mode].extend((batch, idx, item) for idx, item in enumerate(items, start=1))
        batches.append(
            {
                "mode": mode,
                "batch": batch,
                "requested": record.get("requested"),
                "latency_s": record.get("latency_s"),
                "items": items,
            }
        )

    # A estratificação precisa saber quais itens têm defeito, então o conjunto
    # de sinalizados é calculado antes das checagens agregadas (que não são
    # ligadas a item nenhum e portanto não mudam esse conjunto).
    flagged = {
        (f.mode, f.batch, f.item)
        for f in findings
        if f.item and SEVERITY_ORDER[f.severity] >= SEVERITY_ORDER[WARN]
    }

    stats: dict = {}
    for mode, located in located_by_mode.items():
        items = [item for _, _, item in located]
        mode_stats, mode_findings = (aggregate_quiz if mode == "quiz" else aggregate_cloze)(items)
        mode_stats["items"] = len(items)
        findings.extend(mode_findings)
        findings.extend(aggregate_repeats(mode, items))

        gap_stats, gap_findings = stratify_by_source_completeness(mode, located, flagged)
        mode_stats.update(gap_stats)
        findings.extend(gap_findings)
        stats[mode] = mode_stats

    total_items = sum(len(v) for v in located_by_mode.values())
    counts = collections.Counter(f.severity for f in findings)

    usages = [r["usage"] for r in records if r.get("usage")]
    latencies = [r["latency_s"] for r in records if r.get("latency_s") is not None]
    cost = {}
    if usages:
        def total(field):
            values = [u.get(field) for u in usages if u.get(field) is not None]
            return sum(values) if values else None

        cost = {
            "prompt_tokens": total("prompt_tokens"),
            "completion_tokens": total("completion_tokens"),
            "total_tokens": total("total_tokens"),
            "requests": len(usages),
        }
        if cost["total_tokens"] and total_items:
            cost["tokens_per_item"] = round(cost["total_tokens"] / total_items)
    if latencies:
        cost["latency_avg_s"] = round(sum(latencies) / len(latencies), 1)
        if total_items:
            cost["seconds_per_item"] = round(sum(latencies) / total_items, 1)

    return {
        "batches": batches,
        "findings": findings,
        "stats": stats,
        "cost": cost,
        "summary": {
            "batches_requested": len(records),
            "batches_failed": failed,
            "items_audited": total_items,
            "items_flagged": len(flagged),
            "clean_rate": round(1 - len(flagged) / total_items, 2) if total_items else 0.0,
            "errors": counts[ERROR],
            "warnings": counts[WARN],
            "infos": counts[INFO],
        },
    }


# --------------------------------------------------------------------------
# Relatórios
# --------------------------------------------------------------------------

def append_history(out_dir: Path, meta: dict, result: dict) -> Path:
    """Uma linha por run num .jsonl.

    Os relatórios são arquivos soltos: bons para ler um run, inúteis para
    perguntar "isto melhorou desde outubro?" ou "qual modelo rende mais por
    token?". O histórico existe para essas perguntas, e é o formato que um
    dashboard consome direto.
    """
    entry = {
        # Reanálise (`--from-raw`) do mesmo run gera uma linha nova de propósito:
        # o auditor muda e os números mudam junto. O que identifica o run é o
        # par (tag, run_timestamp); `analyzed_at` e `auditor_commit` dizem qual
        # versão do auditor produziu aqueles números. Quem for ler isso deve
        # ficar com a análise mais recente de cada run.
        "run_timestamp": meta.get("timestamp"),
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "auditor_commit": git_commit(),
        **{k: meta.get(k) for k in ("commit", "tag", "provider", "mode", "runs", "n", "source", "cards")},
        "summary": result["summary"],
        "cost": result.get("cost", {}),
        "stats": result["stats"],
        "findings_by_check": dict(collections.Counter(f.check for f in result["findings"])),
    }
    path = out_dir / "history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def export_sample(records: list[dict], size: int, path: Path) -> int:
    """Amostra cega para revisão humana.

    O auditor mede conformidade com regras, não valor pedagógico — e as duas
    coisas divergem: um modelo pontuou 93% produzindo distratores inventados
    ('depthness'), outro pontuou 73% produzindo a única armadilha de L1
    legítima da rodada. Só uma pessoa lendo sem saber quem gerou resolve isso,
    e o resultado vira o material de calibração de qualquer juiz automático
    futuro.
    """
    pool = []
    for record in records:
        if "payload" not in record:
            continue
        key = ENDPOINTS[record["mode"]][1]
        for item in record["payload"].get(key, []):
            pool.append({"origem": record.get("provider", "?"), "modo": record["mode"], "item": item})

    random.shuffle(pool)
    chosen = pool[:size]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            [
                {
                    "id": i + 1,
                    "modo": entry["modo"],
                    # A origem fica no gabarito, não aqui: saber que veio de um
                    # modelo de 4B contamina a avaliação.
                    "exercicio": entry["item"],
                    "sua_nota": None,
                    "comentario": "",
                }
                for i, entry in enumerate(chosen)
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    key_path = path.parent / f"{path.stem}-gabarito.json"
    key_path.write_text(
        json.dumps({str(i + 1): e["origem"] for i, e in enumerate(chosen)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(chosen)


def with_ext(prefix: Path, ext: str) -> Path:
    """`Path.with_suffix` comeria parte de uma tag com ponto (prompt-v4.1)."""
    return prefix.parent / f"{prefix.name}{ext}"


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "?"


def format_stat(value) -> str:
    """dicts viram '0: 3 · 1: 5' em vez do repr do Python."""
    if isinstance(value, dict):
        return " · ".join(f"{k}: {v}" for k, v in value.items()) or "—"
    return str(value)


def render_item(mode: str, index: int, item: dict, item_findings: list[Finding]) -> list[str]:
    out: list[str] = []
    concept = item.get("concept", "")

    if mode == "quiz":
        out.append(f"#### Item {index} · `{item.get('quiz_type', '?')}` — {concept}")
        out.append(f"**Q:** {item.get('question', '')}\n")
        answer_index = item.get("answer_index")
        for j, opt in enumerate(item.get("options") or []):
            marker = " ✅" if j == answer_index else ""
            out.append(f"{j + 1}. {opt}{marker}")
    else:
        out.append(f"#### Item {index} · `{item.get('commonality', '?')}` — {concept}")
        out.append(f"**Frase:** {item.get('sentence', '')}\n")
        out.append(f"- **Resposta:** {item.get('target_expression', '')}")
        out.append(f"- **Alternativas:** {', '.join(item.get('acceptable_alternatives') or []) or '—'}")
        out.append(f"- **Dica:** {item.get('hint', '')}")
        note = item.get("context_note") or "—"
        out.append(f"- **Context note:** {note}")

    out.append(f"\n**Explicação:** {item.get('explanation', '')}")
    sources = item.get("source_cards") or []
    rendered = " · ".join(f"{c.get('front', '')} → {c.get('back', '')}".strip(" →") for c in sources)
    out.append(f"**Cards-fonte:** {rendered or '—'}\n")

    if item_findings:
        for finding in sorted(item_findings, key=lambda f: -SEVERITY_ORDER[f.severity]):
            out.append(f"> [!{'CAUTION' if finding.severity == ERROR else 'WARNING'}]")
            out.append(f"> **{SEVERITY_LABEL[finding.severity]}** `{finding.check}` — {finding.message}\n")

    out.append("---\n")
    return out


def render_markdown(result: dict, meta: dict) -> str:
    summary = result["summary"]
    findings: list[Finding] = result["findings"]
    lines = [
        "# Auditoria de exercícios — UniversePie",
        "",
        f"_{meta.get('timestamp', '?')} · commit `{meta.get('commit', '?')}` · "
        f"modo `{meta.get('mode', '?')}` · {meta.get('runs', '?')} rodadas × n={meta.get('n', '?')}_"
        + (f" · provedor `{meta['provider']}`" if meta.get("provider") else "")
        + (f" · pool: {meta['cards']}" if meta.get("cards") else "")
        + (f" · tag `{meta['tag']}`" if meta.get("tag") else ""),
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Itens auditados | {summary['items_audited']} |",
        f"| Itens sem apontamento | {summary['items_audited'] - summary['items_flagged']} "
        f"({summary['clean_rate']:.0%}) |",
        f"| Erros | {summary['errors']} |",
        f"| Alertas | {summary['warnings']} |",
        f"| Infos | {summary['infos']} |",
        f"| Lotes que falharam | {summary['batches_failed']}/{summary['batches_requested']} |",
        "",
    ]

    by_check = collections.Counter((f.check, f.severity) for f in findings)
    if by_check:
        lines += ["### Apontamentos por checagem", "", "| Checagem | Severidade | Ocorrências |", "|---|---|---|"]
        for (check, severity), count in sorted(
            by_check.items(), key=lambda kv: (-SEVERITY_ORDER[kv[0][1]], -kv[1])
        ):
            lines.append(f"| `{check}` | {SEVERITY_LABEL[severity]} | {count} |")
        lines.append("")
    else:
        lines += ["Nenhum apontamento. 🎉", ""]

    if result.get("cost"):
        lines += ["### Consumo", "", "| Métrica | Valor |", "|---|---|"]
        for key, value in result["cost"].items():
            lines.append(f"| {key} | {format_stat(value)} |")
        lines.append("")

    for mode, stats in result["stats"].items():
        lines += [f"### Estatísticas — {mode}", "", "| Métrica | Valor |", "|---|---|"]
        for key, value in stats.items():
            lines.append(f"| {key} | {format_stat(value)} |")
        lines.append("")

    lines += ["## Detalhes", ""]
    per_item = collections.defaultdict(list)
    for finding in findings:
        if finding.item:
            per_item[(finding.mode, finding.batch, finding.item)].append(finding)

    for batch in result["batches"]:
        mode, index = batch["mode"], batch["batch"]
        latency = batch.get("latency_s")
        header = f"### Rodada {index} — {mode}"
        if latency is not None:
            header += f" ({latency}s)"
        lines += [header, ""]
        if not batch["items"]:
            lines += ["_Sem itens (requisição falhou ou veio vazia)._", ""]
            continue
        for i, item in enumerate(batch["items"], start=1):
            lines += render_item(mode, i, item, per_item.get((mode, index, i), []))

    session_level = [f for f in findings if not f.item]
    if session_level:
        lines += ["## Apontamentos de lote e de sessão", ""]
        for finding in sorted(session_level, key=lambda f: -SEVERITY_ORDER[f.severity]):
            lines.append(f"- **{SEVERITY_LABEL[finding.severity]}** `{finding.check}` ({finding.where}) — {finding.message}")
        lines.append("")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Comparação entre runs
# --------------------------------------------------------------------------

def run_label(report: dict, path: str) -> str:
    meta = report.get("meta", {})
    return meta.get("tag") or meta.get("provider") or Path(path).stem


def compare_reports(paths: list[str]) -> str:
    """Tabela lado a lado de vários .json — é assim que se decide se um
    provedor (ou um prompt) é melhor que o outro em vez de achar que é."""
    reports = [(path, json.loads(Path(path).read_text(encoding="utf-8"))) for path in paths]

    lines = ["# Comparação de runs", "", "| Run | Provedor | Itens | Limpos | Erros | Alertas | Infos |", "|---|---|---|---|---|---|---|"]
    for path, report in reports:
        summary = report.get("summary", {})
        meta = report.get("meta", {})
        lines.append(
            f"| {run_label(report, path)} | {meta.get('provider', '?')} | {summary.get('items_audited', 0)} | "
            f"{summary.get('clean_rate', 0):.0%} | {summary.get('errors', 0)} | "
            f"{summary.get('warnings', 0)} | {summary.get('infos', 0)} |"
        )

    metrics = ["strategy_coverage", "longest_option_is_answer", "answer_position_top_share", "alternatives_avg"]
    lines += ["", "## Estatísticas", "", "| Métrica | " + " | ".join(run_label(r, p) for p, r in reports) + " |",
              "|---" * (len(reports) + 1) + "|"]
    for metric in metrics:
        values = []
        for _, report in reports:
            found = [stats.get(metric) for stats in report.get("stats", {}).values() if metric in stats]
            values.append(format_stat(found[0]) if found else "—")
        if any(v != "—" for v in values):
            lines.append(f"| {metric} | " + " | ".join(values) + " |")

    checks = sorted({f["check"] for _, report in reports for f in report.get("findings", [])})
    if checks:
        lines += ["", "## Apontamentos por checagem", "",
                  "| Checagem | " + " | ".join(run_label(r, p) for p, r in reports) + " |",
                  "|---" * (len(reports) + 1) + "|"]
        for check in checks:
            counts = [
                sum(1 for f in report.get("findings", []) if f["check"] == check) for _, report in reports
            ]
            lines.append(f"| `{check}` | " + " | ".join(str(c) or "—" for c in counts) + " |")

    return "\n".join(lines) + "\n"


def describe_providers() -> str:
    sys.path.insert(0, str(REPO_ROOT))
    from src.config import AI_PROVIDER
    from src.providers import available_providers, get_provider

    lines = [f"Provedor configurado no .env: {AI_PROVIDER}", ""]
    for name in available_providers():
        provider = get_provider(name)
        ready, reason = provider.ready()
        mark = "ok " if ready else "-- "
        lines.append(f"{mark}{name:<12} modelo padrão: {provider.model:<34} {reason}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["quiz", "cloze", "both"], default="quiz")
    parser.add_argument("--runs", type=int, default=3, help="rodadas por modo (padrão: 3)")
    parser.add_argument("--n", type=int, default=5, help="exercícios por rodada (padrão: 5)")
    parser.add_argument("--url", default=DEFAULT_BASE_URL)
    parser.add_argument("--cooldown", type=int, default=25, help="segundos entre rodadas, por causa do RPM")
    parser.add_argument("--retries", type=int, default=2, help="novas tentativas por rodada que falhar")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--out-dir", default="docs/audit")
    parser.add_argument("--tag", default="", help="nome do run (ex: prompt-v4) — vira o nome dos arquivos")
    parser.add_argument("--from-raw", help="reanalisa um .raw.json existente, sem chamar a API")
    parser.add_argument(
        "--source",
        choices=["http", "direct"],
        help="http: audita o endpoint do servidor (padrão). direct: chama a geração no processo, "
        "o que permite escolher o provedor por rodada sem reiniciar o uvicorn",
    )
    parser.add_argument("--provider", help="gemini | groq | ollama | anthropic | deepseek | kimi | zai | openrouter | custom")
    parser.add_argument("--model", help="modelo dentro do provedor (ex: gemma4:e4b, openai/gpt-oss-120b)")
    parser.add_argument("--cards", help="pool congelado em JSON, para comparar provedores com o mesmo material")
    parser.add_argument("--save-cards", help="busca um pool no Anki, salva nesse arquivo e sai (use com --n)")
    parser.add_argument("--compare", nargs="+", metavar="REPORT.json", help="compara relatórios .json já gerados")
    parser.add_argument("--list-providers", action="store_true", help="mostra provedores, modelos padrão e o que falta configurar")
    parser.add_argument("--sample", type=int, metavar="N", help="exporta N exercícios embaralhados para revisão humana cega (+ gabarito à parte)")
    parser.add_argument(
        "--fail-on",
        choices=["error", "warn", "never"],
        default="error",
        help="severidade que faz o script sair com código != 0 (padrão: error)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.list_providers:
        print(describe_providers())
        return 0

    if args.compare:
        report = compare_reports(args.compare)
        print(report)
        return 0

    if args.save_cards:
        asyncio.run(snapshot_cards(args.n, args.save_cards))
        if args.runs == 0:
            return 0

    if args.from_raw:
        raw = json.loads(Path(args.from_raw).read_text(encoding="utf-8"))
        records = raw["records"]
        meta = raw["meta"] | {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "reanalyzed_from": args.from_raw}
        prefix = Path(args.from_raw.replace(".raw.json", ""))
    else:
        # Escolher provedor/modelo só faz sentido no modo direto: por HTTP quem
        # decide é o .env do servidor que já está rodando.
        source = args.source or ("direct" if (args.provider or args.model or args.cards) else "http")
        modes = ["quiz", "cloze"] if args.mode == "both" else [args.mode]

        records = []
        for mode in modes:
            if source == "direct":
                records += asyncio.run(
                    collect_direct(
                        mode, args.runs, args.n, args.provider, args.model,
                        args.timeout, args.cards or args.save_cards, args.cooldown, args.retries,
                    )
                )
            else:
                records += collect_http(args.url, mode, args.runs, args.n, args.cooldown, args.retries, args.timeout)

        providers_used = sorted({r["provider"] for r in records if r.get("provider")})
        meta = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "commit": git_commit(),
            "mode": args.mode,
            "runs": args.runs,
            "n": args.n,
            "source": source,
            "provider": ", ".join(providers_used) or f"servidor em {args.url}",
            "cards": args.cards or args.save_cards or "sorteados do Anki a cada rodada",
            "url": args.url,
            "tag": args.tag,
        }
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = out_dir / (args.tag or f"{args.mode}-{args.provider or 'http'}-{datetime.now().strftime('%Y%m%d-%H%M')}")
        with_ext(prefix, ".raw.json").write_text(
            json.dumps({"meta": meta, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    result = analyze(records)
    with_ext(prefix, ".md").write_text(render_markdown(result, meta), encoding="utf-8")
    with_ext(prefix, ".json").write_text(
        json.dumps(
            {
                "meta": meta,
                "summary": result["summary"],
                "stats": result["stats"],
                "findings": [asdict(f) for f in result["findings"]],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    history = append_history(with_ext(prefix, "").parent, meta, result)

    if args.sample:
        sample_path = with_ext(prefix, "-amostra.json")
        n_sample = export_sample(records, args.sample, sample_path)
        print(f"Amostra cega: {n_sample} exercícios em {sample_path} (gabarito à parte)")

    summary = result["summary"]
    print(
        f"\n{summary['items_audited']} itens auditados · "
        f"{summary['errors']} erros · {summary['warnings']} alertas · {summary['infos']} infos "
        f"· {summary['clean_rate']:.0%} limpos"
    )
    for (check, severity), count in collections.Counter(
        (f.check, f.severity) for f in result["findings"]
    ).most_common(10):
        print(f"  [{SEVERITY_LABEL[severity]}] {check}: {count}")
    cost = result.get("cost") or {}
    if cost:
        print(
            "Consumo: "
            + " · ".join(f"{k}={v}" for k, v in cost.items() if v is not None)
        )
    print(f"Relatórios: {with_ext(prefix, '.md')} · {with_ext(prefix, '.json')} · histórico em {history}")

    if args.fail_on == "never":
        return 0
    threshold = SEVERITY_ORDER[ERROR if args.fail_on == "error" else WARN]
    return 1 if any(SEVERITY_ORDER[f.severity] >= threshold for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
