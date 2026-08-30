# UniversePie — Regras de Geração de Conteúdo

**Última revisão:** 2026-08-30

Este arquivo governa qualquer prompt enviado ao provedor de IA, seja ele qual for.
Leia antes de modificar prompts existentes ou criar novos. O *porquê* das regras
está em `premissas.md`.

---

## Princípios

- A IA opera sobre o banco de dados do usuário — não gera conteúdo genérico
- **Apresentar variação é o objetivo, não efeito colateral.** O exercício reforça
  o que o usuário já sabe *e* mostra outra possibilidade de uso daquilo: outro
  sentido, outra forma, outra partícula, outro registro. É a premissa n+1 — ver
  `premissas.md`. Um exercício que só testa o sentido já conhecido é "n", e o
  prompt não deve produzir só isso
- Âncora no conhecimento existente: o que o usuário já domina é base, não barreira
- Nuances são condicionais: só aparecem quando genuinamente existem. Não forçar nuances onde não há
- Reconhecimento passivo é insuficiente: exercícios devem testar produção ativa
- Transparência sobre fontes: classificar expressões como `common`, `moderate` ou `niche` — não tratar tudo como igualmente relevante

---

## Regras de geração de conteúdo

**Tradução**
Fiel ao tom, sem eufemismos, natural em português. Tom emocional e sensorial deve ser capturado — *itching* não é apenas "ansioso", carrega urgência física.

**Idioma do back**
Preferir inglês quando o significado é direto. Português é reservado para expressões idiomáticas, falsos cognatos, interferências do idioma nativo ou termos genuinamente opacos.

**Sem redundância**
Se o significado é óbvio pelo contexto ou tradução direta, cortar a explicação extra.

**Exemplos paralelos**
1 a 2 exemplos em contextos diferentes para estruturas de uso comum.

**Família de palavras**
Exemplos cobrem formas derivadas e variações temporais: *settle, settled, settling, settlement*.

Esta regra vale para **conteúdo de card**. Como exercício — pedir que o usuário
produza a forma correta dentro de uma frase — ela está **bloqueada** pelo item 5
do `debito-tecnico.md`: a avaliação do cloze marca conjugação correta como erro.
Adicionar o exercício antes de corrigir o matching cria a pior combinação
possível, um exercício que testa exatamente a dimensão que o avaliador não sabe
avaliar. Ordem: corrigir o matching, depois o exercício.

**Registro**
Identificar claramente: informal, vulgar, técnico, sarcástico.

**Phrasal verbs e expressões idiomáticas**
Destacar explicitamente quando o significado não é composicional — a soma das palavras não deduz o significado (*out of the blue*, *get off*, *come Monday*).

**Falsos cognatos e interferências do português**
Sinalizar quando a tradução literal induz erro estrutural: *down the street* ≠ descendo a rua.

**Nuance entre aparentes sinônimos**
Diferenciar expressões que parecem sinônimos em português mas têm usos distintos em inglês: *come on* ≠ *let's go*.

**Etimologia**
Mencionar apenas quando for genuinamente útil para fixar contexto ou significado (*top-shelf*, *gold standard*).

---

## Estratégias de quiz (5 rotativas)

| Estratégia | O que testa |
|---|---|
| `discrimination` | Escolha forçada entre termos próximos (*settle into* vs *settle for*) |
| `production` | Intenção comunicacional — saída ativa, não leitura passiva |
| `interference` | Distratores baseados em traduções literais do português (L1) |
| `polysemy` | Discernimento contextual de múltiplos significados da mesma raiz |
| `contextual` | Implicações pragmáticas e de registro (sarcasmo, formalidade, intenção) |

Nem todas apresentam variação. `polysemy` e `discrimination` apresentam — e são
condicionais ao pool conter o material necessário. `production` e `interference`
testam o sentido já conhecido. A rotação obrigatória entre as cinco, por isso,
garante que parte da sessão não seja n+1: ver
[0002](decisoes/0002-rotacao-de-estrategias.md), com revisão pendente.

---

## Restrições do cloze

- `commonality` restrito a `{"common", "moderate", "niche"}`
- `context_note` obrigatório quando `commonality` != `common`
- Avaliação é por string matching normalizado — o prompt deve gerar `acceptable_alternatives` suficientes para cobrir variações legítimas
