# 0012 — Memória em SQLite local

**Status:** aceita · **Data:** 2026-08-30

## Contexto

A [0006](0006-medida-nasce-na-ferramenta.md) exige persistir evidência. O que
precisa ser gravado está definido pela [0011](0011-origem-da-evidencia.md).

Alternativas consideradas: SQLite, JSONL append-only (como o `audit/history.jsonl`
que o auditor já usa), e gravar de volta no Anki em tags ou campos.

## Decisão

SQLite local.

## Consequências

- As perguntas que a trilha exige — *"como está o past perfect ao longo do
  tempo"* — são agregação em dois eixos no tempo. Isso é consulta, e é onde o
  JSONL apodrece: cada pergunta vira varredura do arquivo inteiro.
- **Gravar no Anki foi descartado por dois motivos independentes:** o `CLAUDE.md`
  já proíbe modificar o deck, e acoplar o histórico de estudo a um deck que o
  usuário sincroniza transforma qualquer defeito nosso em estrago nos dados dele.
- Corrige o item de backlog que descrevia SQLite como "persistência de cards,
  exemplos, tags". O propósito é **histórico de evidência**, não espelhar o Anki.
