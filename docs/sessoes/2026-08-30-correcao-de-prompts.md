# Sessão de 2026-08-30 — as correções de prompt, e a medição delas

**Tipo: evidência.** Contém a linha de base nova do projeto — três modelos, pool
ideal congelado, prompts corrigidos — e os pares antes/depois de cada correção.
Os números não são regeneráveis sem gastar cota e tempo de novo. Permanente.

Consome e substitui `PLANO-qualidade-do-output.md`, que foi apagado.

---

## O que mudou de fato

A branch `feat/card-quality-audit` tinha onze commits e **zero exercício
melhorado**. Quatro das cinco correções de prompt pendentes foram aplicadas e
medidas isoladas. A quinta (item 8) continua aberta, e a razão está no fim.

| # | Prompt | Antes | Depois | Medido em |
|---|---|---|---|---|
| 9 — resposta nunca na última posição | quiz | **0/122** | 3/15, 3/15, 3/12 | gemini, qwen3, groq |
| 10 — numeração do pool vaza | quiz | 3/15 | **0/10** | gemini |
| 11 — cloze sem resposta possível | cloze | 7/15 | **0/13**, depois 4/15 | groq |
| 12 — exercício não ancorado | quiz | 4/15 | **1/15** | qwen3 |

---

## 1. Item 9: a posição virou atribuição, não pedido

O prompt definia `answer_index` e nunca pedia distribuição. A correção tem duas
partes, e a segunda é a que provavelmente carrega o peso:

1. `_answer_positions` embaralha `[i % 4]` e a regra 2 lista a atribuição quiz a
   quiz. "Varie a posição" seria vago: o modelo não sabe o que já usou.
2. **`answer_index` subiu para antes de `options` no `## Output Format`.** Geração
   é autorregressiva. Com `options` primeiro, o modelo escrevia as alternativas e
   só depois escolhia o índice — escolhia *onde já tinha posto a certa*.

| Modelo | Antes | Depois | Distribuição |
|---|---|---|---|
| gemini-2.5-flash | 0/15 | 3/15 | 6/3/3/3 |
| qwen3:8b | 0/15 | 3/15 | 6/3/3/3 |
| gpt-oss-20b | 0/15 | 3/12 | 5/2/2/3 |
| gemma4:e4b | 0/15 | 2/15 | 5/4/4/2 |

`6/3/3/3` é exatamente `[0,0,1,2,3]` repetido em três rodadas: obediência
perfeita. `answer_position_top_share` caiu de 0,67 para 0,40 no Gemini e de 0,80
para 0,42 no Groq. O alerta `answer_position_bias` sumiu em todos.

**O risco que a correção cria.** Atribuir o índice abre a porta para o modelo
declarar `answer_index: 3` e deixar a resposta certa noutro lugar — e o auditor
**não detecta**, porque não sabe qual é a resposta certa. Os três quizzes com
índice 3 da rodada `v2-item9-gemini` foram lidos um a um: os três corretos. Em
escala, quem pega isso é a amostra cega.

---

## 2. Item 10: a primeira versão piorou o defeito, e esse é o achado

A regra 1 proibia citar card listando as strings entre aspas — `"Card 1"`,
`"the pool"`, `"the deck"`. Medida:

| Run | Vazamentos | Quizzes |
|---|---|---|
| `base-g1-gemini` | 3 | 15 |
| `v2-item10-gemini` (1ª versão) | **4** | 15 |
| `v2-item10b-gemini` (2ª versão) | **0** | 10 |

Os quatro caíram num único batch, todos no formato `(Card N)`:

```
'Drop it' (Card 1) is an informal way to tell someone to stop talking about a
topic. 'Lay low' (Card 2) means to avoid attention.
```

O modelo seguiu metade da regra: citou a expressão *e* anexou o número.

> **Instrução negativa com exemplo literal prima o formato que ela proíbe.**

A segunda versão é positiva — manda identificar expressão só por aspas — e o
contraexemplo usa uma palavra que não existe no bloco do pool. Essa lição foi
aplicada em seguida ao item 11, cuja regra ficou procedimental de propósito.

**Ressalva de tamanho.** A cota diária do Gemini (20 requisições no free tier)
acabou no meio da rodada de confirmação: são 10 quizzes, não 15.

---

## 3. Item 11: o teste de leitura de volta

Duas regras procedimentais no cloze: montar a frase com `target_expression` no
lugar da lacuna e ler de volta palavra por palavra, com concordância obrigatória
quando a expressão carrega pronome; e o mesmo teste em cada alternativa, que é
inválida se repete palavra encostada na lacuna.

| Run | `does_not_fit_the_blank` | Cloze |
|---|---|---|
| `base-g1-groq` | **7** | 15 |
| `v2-item1112-groq` | **0** | 13 |
| `v2-final-groq` | **4** | 15 |

**A rodada isolada deu zero e a linha de base final deu quatro.** Somando as duas
medições pós-correção: 4 em 28 (14%), contra 7 em 15 (47%) antes. A correção
funciona e **não elimina** — dizer que zerou seria ler só a rodada conveniente.

---

## 4. Item 12: o prompt parou de se autocitar

Um parágrafo abaixo de `## Quiz Strategy Types` declarando que os exemplos são
forma, não conteúdo. Os exemplos ficaram — são eles que ensinam o formato.

| Run | `anchor_not_in_source_card` | `weak_grounding` | Erros |
|---|---|---|---|
| `base-g1-qwen3` | 4 | 4 | 4 |
| `v2-item910-qwen3` (controle: 9 e 10, sem o 12) | 6 | 6 | 6 |
| `v2-item1112-qwen3` | **1** | **1** | **2** |

**A rodada do meio existe porque 9 e 10 mexem no mesmo prompt** e sem ela a
medição do 12 misturaria três mudanças. Ela mostra algo que não estava previsto:
sem a correção do 12, a ancoragem *subiu* com as correções 9 e 10 no prompt.
**Ponto de atenção:** não há mecanismo estabelecido para isso. Pode ser ruído em
amostra de 15, pode ser o modelo pequeno generalizando a proibição da regra 10
para além do texto visível. Uma medição não decide.

---

## 5. Linha de base nova

`--mode both --runs 3 --n 5`, pool congelado, prompts corrigidos.

| Run | Modelo | Limpos antes | Limpos depois | Erros antes | Erros depois |
|---|---|---|---|---|---|
| `v2-final-gemma4` | gemma4:e4b | 50% | **67%** | 11 | 8 |
| `v2-final-qwen3` | qwen3:8b | 87% | **93%** | 4 | 2 |
| `v2-final-groq` | gpt-oss-20b | 90% | **87%** | 3 | 2 |

**O Groq caiu em `clean_rate` e melhorou em erro**, o que é o item 4 do
`debito-tecnico.md` aparecendo de novo: `clean_rate` conta item marcado por
qualquer severidade, então quatro alertas novos pesam mais que um erro a menos.
Erro é a severidade que importa, e ela caiu nos três.

**Falta o Gemini.** É o modelo que roda em produção e a cota diária acabou. A
linha de base final dele é a primeira coisa da próxima sessão.

---

## 6. Dois defeitos do instrumento, achados e corrigidos

**O cliente do Gemini não sobrevive a troca de event loop.** `--mode both
--source direct` chamava `asyncio.run` uma vez por modo, e `GeminiProvider._client`
é cache de classe: o cliente `aio` ficava preso ao loop do quiz, fechado antes do
cloze começar. Toda rodada queimava uma tentativa com `Event loop is closed`, e o
`--retries` mascarava. Os dois modos passaram a rodar num loop só. A fragilidade
do lado do provedor ficou registrada como item 13 do `debito-tecnico.md`, sem
correção: em produção o uvicorn tem um loop só e o defeito não aparece.

**`count_mismatch` culpava o backend por saída truncada.** Batch curto tem duas
causas com correções opostas — item descartado pelo Pydantic, ou saída cortada no
teto de tokens. A mensagem afirmava a primeira. Os dois batches curtos do
`v2-item1112-groq` estavam em `completion_tokens` **4096/4096 exatos**, com os
outros quatro entre 2471 e 3536. Agora existe `output_truncated`, que só dispara
quando os dois números estão disponíveis e encostados.

---

## 7. A verificação de ponta a ponta, que achou o que a medição não achou

Todas as medições passaram por `--source direct` e pelo **pool ideal congelado**.
A verificação final foi pelo servidor HTTP com o **deck real** (537 cards), que é
o grupo 2 — fronts como frases inteiras, formato que o pool congelado não tem.

**O quiz saiu perfeito:** posições exatamente `[0,0,1,2,3]`, zero vazamento,
5/5 estratégias, `source_expression` em todos. É a correção 9 funcionando fora do
material que a mediu.

**O cloze entregou dois defeitos em cinco exercícios:**

```
When the stock market is booming, many investors _____.
  target_expression: "quit while you're ahead"
```

Preenchida: *"many investors quit while you're ahead"*. Item 11 sobrevivendo à
correção — e **o auditor não marcou**. A checagem procurava
`your|yourself|yourselves`, e em `you're` o apóstrofo fecha a borda de palavra
antes do "r". Corrigido, com reanálise de seis `.raw.json` confirmando que
nenhuma contagem histórica muda: a contração não ocorre no pool congelado.

A segunda lacuna ficou aberta de propósito: `other_subject` só procura pronomes e
*"many investors"* não é pronome. Cobrir isso é decidir por regex se a oração tem
sujeito de 3ª pessoa, o que dispara em imperativo com objeto determinado. **Com
ela aberta, o 4 em 28 do item 11 é piso, não contagem exata.**

O outro exercício nasceu **sem lacuna nenhuma**, com a expressão escrita por
extenso na frase. Esse o auditor pega. Não foi corrigido: apareceu na verificação
final, e mudar prompt sem medir é o que o plano desta branch proíbe.

**A lição de método.** Medir sempre no mesmo material esconde defeito que só o
outro material produz. O grupo 2 existe no plano desde 2026-08-30 e continua sem
rodada dedicada.

---

## Pendências abertas

- **Linha de base final do Gemini** — bloqueada por cota até o reset diário. É a
  primeira coisa da próxima sessão, e é ela que fecha o item 10 em 15 quizzes.
- **Item 8 continua sem número.** A pré-condição que o próprio item registrava
  ("decidir quando o item 12 estiver medido") foi cumprida nesta sessão, então a
  decisão está madura — mas ela exige campo novo no `QuizItem`, que é mudança de
  contrato.
- **As amostras cegas não foram lidas por humano.**
  `audit/amostra-v2-groq-amostra.json` e `audit/amostra-v2-qwen3-amostra.json`,
  10 exercícios cada, gabarito à parte. `clean_rate` mede conformidade com regra,
  não valor pedagógico — achado 4 de 2026-08-29, que não caducou.
- **Item 11 não zerou.** 4 em 28 depois, contra 7 em 15 antes — e é piso, não
  contagem exata, enquanto o sujeito nominal não for detectado.
- **Cloze sem lacuna**, achado na verificação final e não corrigido. O auditor
  pega; falta a rodada de prompt.
- **O grupo 2 (`audit/pool-real.json`) nunca teve rodada dedicada.** A
  verificação final mostrou que ele produz defeito que o grupo 1 não produz.
- **A interação entre a regra 10 e a ancoragem no modelo pequeno** não está
  explicada. Registrada acima como ponto de atenção.
