# 0009 — Unidade de conhecimento em dois eixos

**Status:** aceita · **Data:** 2026-08-30

## Contexto

Para afirmar "o usuário sabe X", o sistema precisa saber o que é X. Hoje o mais
próximo disso é o campo `concept` (`prompts.py:64`, *"Brief label of the concept
being tested"*): **texto livre, inventado pela IA a cada chamada, nunca
normalizado, nunca persistido.** Dois exercícios sobre o mesmo conceito geram
rótulos diferentes e o sistema não sabe que são a mesma coisa.

Consequência: a trilha da [0008](0008-trilha-e-espelho.md) é impossível com o
modelo atual, independente de banco de dados.

Há ainda um descompasso de natureza. O deck é de expressões mineradas
(*out of the blue*, *tell off*). Mas o autor quer também acompanhar features
gramaticais — "sou ruim em *I've…*" — que não são cards. A saída é que **sentença
minerada carrega gramática**: o eixo gramatical é inferível do material existente,
não é taxonomia que alguém precise preencher à mão. É o princípio de gramática
emergente, recuperado de `historico/planejamento-geral-2.md`.

## Decisão

Dois eixos:

1. **A expressão** — âncora, com id estável vindo do Anki.
2. **O tipo de variação** — vocabulário controlado: polissemia, troca de
   partícula, tempo/particípio e família de palavras, registro, colocação,
   interferência L1, e os conceitos gramaticais presentes na sentença.

O conceito gramatical é **inferido na ingestão**, uma vez por card, gravado, e
não recalculado a cada exercício.

## Consequências

- Torna "n+2, n+3" mensurável: o incremento vira *quantos tipos de variação desta
  expressão o usuário já viu e acertou*.
- Substitui `concept` como chave de agregação. O campo pode continuar existindo
  como rótulo legível; não serve como identidade.
- Inferir na ingestão permite auditar toda a classificação de uma vez. Inferir por
  exercício espalharia o ruído por todas as sessões futuras, sem ponto de controle.
- O vocabulário controlado é objeto da [0010](0010-lista-de-conceitos.md).
