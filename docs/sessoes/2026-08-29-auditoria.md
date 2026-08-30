# Sessão de 2026-08-29 — auditoria de qualidade

**Tipo: evidência.** Contém a linha de base de medição do projeto — os números não são regeneráveis sem gastar cota. Permanente.

Registro factual do que foi construído, medido e concluído. Escrito para quem
retomar o trabalho sem ter participado da sessão.

> **Nota de 2026-08-30.** Os caminhos citados aqui são os desta data:
> `CONTEXT.md` virou `arquitetura.md` + `roadmap.md` + `premissas.md`,
> `AI_RULES.md` virou `ai-rules.md`, `DEBITO_TECNICO.md` virou
> `debito-tecnico.md`. As pendências ao final foram parcialmente resolvidas — ver
> a nota de fechamento.

Branch: `feat/card-quality-audit`, publicada em `origin`. 107 testes passando.

---

## O que existe agora e não existia antes

**Camada de provedores** (`src/providers.py`). O provedor de IA virou
configuração (`AI_PROVIDER` / `AI_MODEL`), não código. Gemini segue o padrão.
Groq, DeepSeek, Kimi, Z.ai, OpenRouter e qualquer endpoint compatível com a API
da OpenAI compartilham uma implementação; Ollama, Gemini e Anthropic têm a sua.
Nenhuma dependência nova — tudo em `httpx`, menos o Gemini que continua no SDK.

**Auditor de exercícios** (`scripts/audit_exercises.py`, antes
`evaluate_quizzes.py`). 28 checagens sobre quiz e cloze. Roda contra o servidor
(`--source http`) ou chamando a geração no processo (`--source direct`), o que
permite trocar de provedor por rodada. Relatórios em markdown, JSON e respostas
cruas. Sai com código != 0 se houver achado de severidade ERRO.

**Correções de aplicação.** `strip_html` passou a decodificar todas as
entidades HTML (antes cobria cinco e deixava `&apos;` passar, presente em 17%
do deck). Ollama com `think: false`. Teto de saída nos compatíveis com OpenAI.

---

## A medição

Linha de base de 2026-08-29, sobre o deck real (`English_Series`, 537 cards),
pool sorteado a cada rodada, 3 rodadas × n=5, quiz e cloze. **118 exercícios.**

| Modelo | Itens | Limpos | Latência/sessão |
|---|---|---|---|
| Groq `openai/gpt-oss-20b` (quiz) | 15 | 93% | 3,6s |
| Gemini 2.5 Flash | 30 | 87% | 38,4s |
| Groq `openai/gpt-oss-20b` (cloze) | 13 | 85% | 2,6s |
| qwen3:8b local | 30 | 83% | 22,0s |
| gemma4:e4b local | 30 | 63% | 21,1s |

"Limpo" significa *sem violar regra mecânica*, não *bom*. A distinção é o
ponto principal desta sessão — ver o achado 4.

Dados em `docs/audit/`: `history.jsonl` (uma linha por run, versionado),
`baseline-*.json` (versionados), `.raw.json` e `.md` (locais, ignorados).

---

## Achados, por força de evidência

### 1. A resposta correta quase nunca está nas últimas posições

Em 60 quizzes de quatro modelos independentes (Google, Alibaba, OpenAI, Google
local; de 4B a proprietário grande):

| pos 0 | pos 1 | pos 2 | pos 3 |
|---|---|---|---|
| 36 (60%) | 22 (37%) | 2 (3%) | 0 (0%) |

A última alternativa **nunca** foi a resposta. Quem marcar sempre a primeira
acerta 60% sem saber inglês. Como o viés é igual em modelos não relacionados, a
causa é o prompt, que define `answer_index` e nunca pede distribuição.

**Correção pendente** — migrado para `debito-tecnico.md` item 9.

### 2. Numeração de card vaza para o texto que o aluno lê

13 ocorrências ("Card 2", "Card 10", "not in the pool" dentro da explicação). O
que dirige é combinar cards, não o back vazio:

```
1 card-fonte:  4/87  (5%)
4 cards-fonte: 8/11  (73%)
```

A regra 3 do prompt manda derivar distratores de outros cards, e o bloco do
pool é formatado como `Card 1:`, `Card 2:`. O modelo leva a numeração adiante.

**Correção pendente** — migrado para `debito-tecnico.md` item 10.

### 3. Exercícios de cloze sem resposta certa possível

6 em 56. Duas classes: alvo em pessoa incompatível com a frase ("She was
hesitant to _____ the enormous task" com alvo `take upon yourself`) e
alternativas que duplicam palavra da frase ("it _____ that" com alternativa
`it transpired` → "it it transpired"). O auditor passou a detectar
(`person_mismatch`, `does_not_fit_the_blank`), **o prompt continua gerando.**

**Correção pendente** — migrado para `debito-tecnico.md` item 11.

### 4. A métrica de qualidade inverteu a ordenação real

Este é o achado mais importante e o que mais limita conclusões.

No mesmo tipo de exercício (`interference`), o `gpt-oss-20b` — melhor nota da
sessão, 93% — produziu as alternativas "out of your depth" / "out of depth" /
"out of your depthness" / "out of depthness": palavras inventadas, nenhuma
interferência do português, exatamente o que o `ai-rules.md` proíbe. O Gemini —
73% — produziu a única armadilha de L1 legítima da rodada ("contar sua mãe
fora" para *tell off*), penalizado por citar "Card 2" numa explicação, defeito
cosmético que o aluno vê depois de responder.

**Consequência: não há como afirmar hoje se um modelo pequeno é suficiente para
o projeto.** A dimensão que separaria não é medida. Ver `DEBITO_TECNICO.md`
item 4 para as duas heurísticas determinísticas testadas e rejeitadas, com os
números. `--sample N` exporta amostra cega para revisão humana, que é o
caminho restante e também o que calibraria um LLM-juiz depois.

### 5. Card com back vazio não é o problema que parecia

38% do deck (205 de 537) não tem back. Um alarme inicial apontava 75% de
defeito nesses itens contra 9% nos demais, no Gemini. **A correlação é em boa
parte espúria**: o que dirige é o número de cards combinados. Lendo os itens um
a um, nenhum inventou significado; o exemplo mais claro veio limpo — card
"Evil Corp servers should be back up soon enough." sem back, e o Gemini
produziu um quiz de polissemia correto inferindo o alvo da própria frase.

**O prompt não precisa de regra sobre back vazio.** A checagem
`source_without_back` continua no auditor para monitorar.

### 6. Quiz e cloze estão em situações diferentes

Defeitos concentrados no quiz (18/62 antes das checagens novas de cloze). O
prompt de cloze tem um defeito real (achado 3) mas de outra natureza. Cobertura
das 5 estratégias foi 5/5 em todos os modelos, e `longest_option_is_answer`
ficou entre 0,20 e 0,27 contra 0,25 esperado por acaso — não há pista pelo
tamanho da alternativa.

---

## Fatos operacionais dos provedores

Todos em tier gratuito, por decisão de projeto. Falha de cota é condição normal
de operação, não defeito (ver `CLAUDE.md`).

- **Groq**: 1000 requisições e 8000 tokens/min no `gpt-oss-20b`. O `max_tokens`
  reservado conta contra o TPM: com 8192 a requisição leva 413 antes de sair;
  sem o campo, a sessão trunca e o modo JSON descarta tudo com 400. 4096 é o
  meio. Uma sessão de 5 exercícios gasta ~2.200 tokens de saída — os modelos
  gpt-oss emitem tokens de raciocínio que contam e não aparecem no conteúdo.
- **OpenRouter**: 18 modelos `:free`, pool compartilhado entre todos os
  usuários gratuitos; 429 do provedor de baixo é rotina e às vezes chega com
  HTTP 200 e o erro no corpo.
- **Ollama**: qwen3 e gemma4 raciocinam por padrão e gastavam a maior parte do
  tempo nisso (96s contra 22s por sessão). `think: false` resolve.
- **Gemini**: 503 UNAVAILABLE por alta demanda acontece.

---

## O que falta

1. **Três correções de prompt**, todas com evidência acima: distribuir a
   posição da resposta (achado 1), proibir referência a card no texto visível
   (achado 2), garantir que a expressão-alvo encaixe na frase do cloze
   (achado 3). Nenhuma foi feita — `CLAUDE.md` exige confirmação para mexer em
   prompt.
2. **Medir de novo depois de corrigir** e comparar com
   `--compare docs/audit/baseline-*.json`. A linha de base existe justamente
   para isso.
3. **Revisão humana cega** de uma amostra (`--sample 20`), única forma hoje de
   responder se modelo pequeno basta.
4. **Premissas não documentadas.** "n+1" não aparece em nenhum arquivo do
   repositório, embora seja descrito pelo autor como central. O vizinho mais
   próximo é `AI_RULES.md:10` ("âncora no conhecimento existente"). Pendente:
   sessão de `/grill-me` para extrair e então documentar.
5. **Documentação desatualizada por commits desta sessão**: `AI_RULES.md:3`
   ainda diz "qualquer prompt enviado ao Gemini"; `CONTEXT.md:65-66` descreve o
   fluxo como se Gemini fosse o único provedor.
6. **Revisão de código** da branch (`/code-review`), que nunca passou por uma.

---

## Fechamento — 2026-08-30

- **Item 1** passou de três para **quatro** correções de prompt. A quarta é a
  regra 7 (rotação obrigatória das estratégias), que dilui a premissa n+1 — ver
  `debito-tecnico.md` item 8 e `decisoes/0002-rotacao-de-estrategias.md`.
- **Item 4 cumprido.** A sessão de `/grill-me` aconteceu e produziu
  `premissas.md`, mais 13 ADRs. Com uma descoberta: o termo **estava** documentado
  — em `historico/planejamento-geral.md`, com outra definição, e foi
  deliberadamente aposentado na revisão seguinte. A afirmação "não aparece em
  nenhum arquivo do repositório" era verdadeira quanto ao repositório e falsa
  quanto ao projeto. Ver `2026-08-30-premissas.md`.
- **Item 5 cumprido.**
- **Item 6 cumprido.** O ultrareview da branch voltou com 6 achados, todos `nit`.
- Ressalva do achado 6 desta sessão: a cobertura 5/5 das estratégias foi lida como
  saúde e é, em parte, a diluição da premissa. Ver o ADR `0002`.

---

## O que não confiar desta sessão

- **Comparação entre modelos**: cada provedor sorteou pools diferentes, então
  parte da diferença vem do material. Para comparar de verdade, usar `--cards`
  com pool congelado.
- **Amostras pequenas**: as taxas por modelo vêm de 15 a 30 itens. Servem para
  detectar defeito sistemático (achados 1 e 2, presentes em todos os modelos),
  não para ranquear modelos próximos.
- **A palavra "limpo"**: mede conformidade com regra mecânica. O achado 4
  mostra que ela pode inverter a ordem real de qualidade.
