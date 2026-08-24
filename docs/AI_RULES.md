# UniversePie — Regras de Geração de Conteúdo

Este arquivo governa qualquer prompt enviado ao Gemini. Leia antes de modificar prompts existentes ou criar novos.

---

## Princípios

- A IA opera sobre o banco de dados do usuário — não gera conteúdo genérico
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

---

## Restrições do cloze

- `commonality` restrito a `{"common", "moderate", "niche"}`
- `context_note` obrigatório quando `commonality` != `common`
- Avaliação é por string matching normalizado — o prompt deve gerar `acceptable_alternatives` suficientes para cobrir variações legítimas
