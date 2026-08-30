# 0001 — Pool de cards em lote, não um por vez

**Status:** aceita · **Data:** 2026 (Alpha v3) · **Fonte:** `historico/changelog.md`

## Contexto

Na Alpha v2 o fluxo era 1 card → 1 quiz. O resultado foi diagnosticado no próprio
changelog como **"flashcards disfarçados"**: reconhecimento passivo puro, sem nada
que o card já não fizesse. Um card isolado não dá superfície para o modelo
relacionar conceitos.

## Decisão

Enviar um pool de `n * 3` cards em uma única chamada ao provedor, para dar área de
superfície a correlações: agrupar família de palavras, discriminar entre termos
próximos e derivar distratores de cards reais do deck.

## Consequências

- Habilita as estratégias `discrimination` e `polysemy`, que dependem do pool
  conter cards relacionados — e, por isso mesmo, tornam-nas dependentes do sorteio.
- Torna o consumo por exercício previsível e mensurável (`tokens_per_item`).
- Um exercício pode citar múltiplos cards-fonte, o que exige o mapeamento
  `used_cards` → `source_cards`.
- **Efeito colateral medido:** exercícios que combinam 4 cards vazam a numeração
  interna do pool para o texto do aluno em 73% dos casos, contra 5% em exercícios
  de card único. Ver `debito-tecnico.md`.

Reafirmada em `CLAUDE.md` como decisão consolidada. Não voltar para 1-para-1.
