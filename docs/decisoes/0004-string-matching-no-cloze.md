# 0004 — Avaliação do cloze por string matching

**Status:** aceita · **Data:** 2026 (Alpha v3.1) · **Fonte:** `historico/changelog.md`

## Contexto

Decorrência da [0003](0003-cloze-como-producao-ativa.md). Avaliar texto livre com
IA foi considerado prematuro para o alpha: falso negativo é o erro mais caro numa
ferramenta de produção ativa, porque ensina ao usuário que a resposta certa está
errada.

## Decisão

Avaliação client-side por comparação normalizada (lowercase, trim, colapso de
espaços) contra `target_expression` e `acceptable_alternatives`. Sem chamada extra
à API.

## Consequências

- Resposta semanticamente correta mas lexicamente diferente das alternativas
  pré-geradas é marcada como errada. Aceito no alpha.
- **Defeito medido:** a normalização não trata conjugação. "gave up on" contra alvo
  "give up on" é marcado como erro. Ver `debito-tecnico.md` item 5 — é bloqueador
  de qualquer exercício de família de palavras.
- **Escopo:** esta decisão congela *avaliação de texto livre pela IA*. Melhorar a
  normalização continua sendo string matching e não conflita com ela.
- Um LLM atuando como **juiz de qualidade do exercício gerado** é coisa diferente
  de IA avaliando a resposta do aluno, e também não conflita.
