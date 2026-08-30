# 0002 — Rotação obrigatória de 5 estratégias no quiz

**Status:** aceita, **com revisão pendente** · **Data:** 2026 (Alpha v3)
**Fonte:** `historico/changelog.md`

## Contexto

Mesma origem da [0001](0001-pool-em-lote.md): o quiz da v2 produzia reconhecimento
passivo. Além do pool em lote, foi imposta rotatividade entre cinco estratégias de
avaliação — `discrimination`, `production`, `interference`, `polysemy`,
`contextual` — para forçar o exercício a sair do reconhecimento.

## Decisão

O prompt exige variar a estratégia ao longo da sessão e proíbe tipos iguais
consecutivos (`prompts.py:52`, regra 7).

## Consequências

**A intenção original é válida e deve ser preservada:** sem ela o quiz regride
para flashcard disfarçado, que é um defeito real e já observado.

**Mas a execução atual dilui a premissa do projeto.** Das cinco estratégias, duas
apresentam variação de algo conhecido (`polysemy`, `discrimination`) e ambas são
condicionais ao sorteio — o prompt diz *"Use when the pool contains…"*. As
estratégias `production` e `interference` testam o sentido que o usuário já
conhece: são "n", não "n+1". Ao obrigar a rotação, o sistema **garante** que parte
da sessão não apresente variação nenhuma.

A auditoria de 2026-08-29 mediu cobertura 5/5 em todos os modelos e registrou isso
como saúde. É saúde contra o flashcard disfarçado e diluição contra a premissa —
as duas coisas ao mesmo tempo.

**Revisão pendente:** separar as duas intenções. Manter o antídoto contra
reconhecimento passivo, remover a garantia de que a variação seja diluída. É a
quarta correção de prompt registrada em `debito-tecnico.md`.

`skills/prompt-review.md` verificava a presença das cinco estratégias como critério
de qualidade — corrigido na mesma sessão, senão a revisão desfaz a correção.
