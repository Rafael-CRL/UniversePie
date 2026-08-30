# Sessão de 2026-08-30 — auditoria da branch e linha de base do grupo 1

**Tipo: evidência.** Contém a linha de base vigente do projeto — 120 exercícios,
quatro modelos, pool ideal congelado. Os números não são regeneráveis sem gastar
cota e tempo de novo. Permanente.

Esta sessão foi convocada para **auditar** o que as duas anteriores fizeram, sob
suspeita de que a IA tivesse começado a alucinar. Não era o caso: as medições
registradas reproduzem. O que não sobreviveu foi o instrumento que as produziu e
três contagens.

---

## 1. A auditoria: o que se sustentou e o que não

**Sustentou-se.** Recalculei todas as afirmações numéricas dos registros
anteriores contra os artefatos brutos. As medições existem e conferem, inclusive
as que pareciam inventadas: os tempos do Ollama (21,5s e 44,8s medidos, tabela
dizia 21,8 e 45,1 — diferença é o tempo de processo), os tamanhos dos modelos
(5,2 GB e 9,6 GB, batem com os manifests), e o achado `ungrounded` que estava
num scratchpad em `/tmp` e foi preservado em `audit/medicao-fria.json`.

**Não se sustentou:** seis defeitos de código e três contagens.

### Os seis defeitos, corrigidos

| Defeito | O que causava |
|---|---|
| `--compare` sem guarda de forma | O glob recomendado casa os `.raw.json`; cada run aparecia duas vezes, a segunda como "0% limpos" |
| `--from-raw` ignorava `--out-dir`/`--tag` | Reanalisar sobrescrevia a linha de base no lugar. Aconteceu durante esta sessão |
| `does_not_fit_the_blank` | A correção anterior trocou um falso positivo por dois falsos negativos |
| `used_cards` destruído por `build_items` | A investigação que o item 12 pedia era impossível com o dado salvo |
| `parse_json` em resposta truncada | Devolvia sessão de 1 exercício em vez de erro |
| `AI_TIMEOUT_S` inerte no Ollama | A mensagem de timeout mandava aumentar uma variável sem efeito |

### As três contagens

| Item | Dizia | É |
|---|---|---|
| 9 | 36/22/2/0 em 60 | 38/22/2/0 em 62 |
| 10 | 4/87 (5%) e 8/11 (73%) | 4/98 (4%) e 8/13 (62%) |
| 11 | 6 em 56 | 5 exercícios distintos, 7 achados |

Nenhuma conclusão mudou. Mas `debito-tecnico.md` existe para carregar evidência
acionável, e número que ninguém reproduz não é evidência.

---

## 2. O quiz ganhou a âncora que o cloze sempre teve

O cloze é medido melhor que o quiz, e a razão não é cuidado de quem escreveu.
`ClozeItem` declara `target_expression` — uma string —, e **sete das dezesseis
checagens de cloze existem só por causa dela**. O quiz declarava o que testa só
em prosa (`concept`, item 7), então ancoragem só dava para estimar por
sobreposição de palavras.

`QuizItem.source_expression` (novo): a expressão do pool em que o quiz se apoia,
copiada literalmente do Front do card. Nome diferente do cloze de propósito — lá
é a **resposta**, aqui é a **âncora**, e o quiz existe para testar uma variação
dela.

Três checagens novas: `anchor_not_in_source_card` (ERRO),
`anchor_absent_from_exercise` (ALERTA) e `empty_source_expression` (ALERTA). A
segunda é frouxa de propósito: exigir a expressão inteira no enunciado reprovaria
a premissa n+1.

**Adesão medida: 60/60 quizzes declararam o campo**, nos quatro modelos. Custo:
irrelevante (419–947 tokens por item, dentro da variação normal entre modelos).

---

## 3. Linha de base do grupo 1

Dois grupos de material foram decididos nesta sessão:

- **Grupo 1** — `audit/pool-exemplo.json`: 15 cards, **todos com back**, fronts
  como expressões limpas. Mede qualidade de prompt sem que variação de material
  entre na conta.
- **Grupo 2** — `audit/pool-real.json`: 15 cards, 5 sem back, fronts como frases
  inteiras. Mede o comportamento na realidade da fonte. Sessão futura.

Medição do grupo 1: `--mode both --runs 3 --n 5`, pool congelado, quatro modelos.

| Run | Provedor | Itens | Limpos | Erros | Alertas |
|---|---|---|---|---|---|
| `base-g1-gemini` | gemini-2.5-flash | 30 | **90%** | 0 | 4 |
| `base-g1-groq` | openai/gpt-oss-20b | 30 | **90%** | 3 | 5 |
| `base-g1-qwen3` | ollama qwen3:8b | 30 | 87% | 4 | 4 |
| `base-g1-gemma4` | ollama gemma4:e4b | 30 | **50%** | 11 | 10 |

Por checagem:

| Checagem | gemini | groq | qwen3 | gemma4 |
|---|---|---|---|---|
| `missing_context_note` | 0 | 0 | 0 | 8 |
| `does_not_fit_the_blank` | 0 | 7 | 0 | 0 |
| `anchor_not_in_source_card` | 0 | 0 | 4 | 1 |
| `weak_grounding` | 0 | 0 | 4 | 3 |
| `meta_leak_explanation` | 3 | 0 | 0 | 3 |
| `repeated_concept` | 3 | 0 | 10 | 0 |
| `answer_in_question` | 0 | 0 | 0 | 2 |
| `telegraphed_trap` | 0 | 0 | 0 | 2 |
| `answer_position_bias` | 1 | 1 | 0 | 0 |
| `alternative_equals_target` | 0 | 0 | 0 | 1 |
| `anchor_absent_from_exercise` | 0 | 0 | 0 | 1 |

Cobertura de estratégias: 5/5 nos quatro modelos.

---

## 4. O achado principal: metade dos defeitos é do modelo, não do prompt

**Achados de ancoragem, todo o histórico do projeto** — 15 rodadas, dois dias,
incluindo OpenRouter minimax e nemotron:

> **Modelos locais: 18. Modelos de API: 0.**

Zero. Gemini, Groq e os dois do OpenRouter nunca produziram um exercício não
ancorado, em nenhuma rodada.

**A causa é o prompt se autocitando, e só o modelo pequeno cai nela.** Os cinco
casos são as expressões dos exemplos embutidos nas descrições de estratégia:
`sound` de `prompts.py:36` e `loop in the whole team` de `prompts.py:42`. O
modelo copia o exemplo literal em vez de trabalhar o pool, e depois cita
`used_cards` para parecer ancorado — num caso, os 15 cards de uma vez.

Reproduz o `ungrounded` de `medicao-fria.json` (também "Polysemy of *sound*") e
os `weak_grounding` de 2026-08-29 (a mensagem do chefe, do exemplo `contextual`).

O mesmo vale para o item 11: `does_not_fit_the_blank` deu 7 no Groq e **0 no
Gemini**.

**Consequência.** O plano anterior mandava iterar no Ollama porque não gasta
cota. Para os itens 11 e 12 isso otimizaria para um modelo que não roda em
produção. O índice de `debito-tecnico.md` foi reordenado por evidência no modelo
que o usuário roda.

---

## 5. O que a linha de base nova confirmou e o que desmentiu

**Confirmou o item 9, e forte.** No pool congelado, quatro modelos, 60 quizzes:
31/14/15/**0**. Somando os dois pools: **0 em 122 quizzes, seis configurações,
dois dias.** A última alternativa nunca foi a resposta. É o defeito mais
reproduzível do projeto.

**Desmentiu o mecanismo do item 10.** A correlação com número de cards-fonte
some no pool congelado: 1 card 4%, 4 cards 8% — não 4% contra 62%. O vazamento é
real (6/60, e presente no Gemini), mas a causa declarada não está estabelecida.

---

## Pendências abertas

- **Item 8 não tem número** e continua sem. O caminho para medi-lo está
  registrado no próprio item: declarar sentido do card × sentido testado. É
  declarativo — pega contradição, não pega erro.
- **`repeated_concept` deu 10 no qwen3 e 3 no Gemini** e não está catalogado como
  débito. Num pool congelado de 15 cards a repetição entre rodadas é esperada;
  falta decidir se é defeito ou artefato da medição.
- **A amostra cega** (`audit/base-g1-qwen3-amostra.json`, 10 exercícios com
  gabarito à parte) **não foi lida por humano.** `clean_rate` mede conformidade
  com regra, não valor pedagógico — achado 4 de 2026-08-29, não caducou.
- **Nenhum prompt foi alterado.** Três sessões, zero exercício melhorado. O plano
  da próxima está em `PLANO-qualidade-do-output.md`.
