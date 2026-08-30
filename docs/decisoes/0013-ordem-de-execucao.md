# 0013 — Ordem: documentar, corrigir prompts, então o núcleo

**Status:** aceita · **Data:** 2026-08-30

## Contexto

Três frentes competiam: documentar as premissas, corrigir os prompts com defeito
já evidenciado, e construir o núcleo n+1 (classificação, lista de conceitos,
registro de evidência).

## Decisão

1. **Documentar.** Motivo do autor: havia dúvidas e inconsistências sobre o
   entendimento do projeto, e isso estava prejudicando a qualidade do
   desenvolvimento e dos testes.
2. **Corrigir os prompts e remedir** contra a linha de base de 2026-08-29. São
   quatro correções, todas com evidência — ver `debito-tecnico.md`.
3. **Núcleo n+1.**

## Consequências

A ordem entre 2 e 3 não é arbitrária. Corrigir os prompts **antes** do núcleo dá
uma medida limpa contra a linha de base existente. Depois, nunca mais se separa
"melhorou porque o prompt foi corrigido" de "melhorou porque o n+1 entrou".

O núcleo é grande e tem pendências de desenho registradas
([0010](0010-lista-de-conceitos.md), e o loop de precisão em `premissas.md`).
Merece sessão de planejamento própria, não o resto de uma sessão.
