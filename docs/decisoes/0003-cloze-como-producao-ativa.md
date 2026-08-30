# 0003 — Cloze como exercício de produção ativa

**Status:** aceita · **Data:** 2026 (Alpha v3.1) · **Fonte:** `historico/changelog.md`

## Contexto

Mesmo com as cinco estratégias, o quiz continua sendo **reconhecimento**: o usuário
escolhe entre opções apresentadas. Reconhecimento é o nível mais raso de memória e
não cobre produção ativa, que é o que o projeto se propõe a testar.

Três candidatos foram avaliados:

1. **Scenario Writing** (escrita livre guiada) — descartado: depende de avaliação
   de texto livre pela IA, cuja confiabilidade era baixa no alpha. O risco de
   falso negativo — marcar resposta válida como errada — compromete a experiência.
2. **Register Shifting** (refatoração de diálogo) — descartado: conexão fraca com
   o deck. Funciona como exercício genérico de inglês, não ancorado nos dados reais.
3. **Cloze Production** (preenchimento sem opções) — escolhido.

## Decisão

Cloze: frase com lacuna, sem opções, o usuário digita. A restrição da resposta a
uma expressão — e não a um parágrafo — mantém o espaço de avaliação manejável.

## Consequências

- O cloze acabou sendo o mecanismo **mais fiel à premissa n+1** do que o quiz: o
  prompt exige que a frase crie *"a DIFFERENT context from the original card"*
  (`prompts.py:93`), que é literalmente o "+1".
- Trouxe a classificação `commonality` e o `context_note`.
- A avaliação ficou presa a string matching — ver [0004](0004-string-matching-no-cloze.md).
