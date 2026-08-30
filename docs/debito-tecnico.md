# Débito técnico

Problemas identificados e ainda não resolvidos. Cada entrada carrega a evidência
que a originou — sem isso, daqui a alguns meses nenhuma delas é acionável.

Este arquivo é diferente do `roadmap.md`: lá ficam features não implementadas,
aqui ficam defeitos e lacunas do que já existe.

Última revisão: 2026-08-30.

## As correções de prompt: quatro fechadas, uma aberta

Corrigidas e medidas na sessão de 2026-08-30
(`sessoes/2026-08-30-correcao-de-prompts.md`), contra a linha de base do grupo 1
(`audit/base-g1-*.json`, pool ideal congelado `audit/pool-exemplo.json`). Cada
correção foi medida **isolada**, no modelo em que o defeito aparece.

| # | Defeito | Prompt | Antes | Depois | Medido em |
|---|---|---|---|---|---|
| [9](#9-a-resposta-correta-quase-nunca-cai-nas-últimas-posições) | Resposta nunca na última posição | quiz | **0/122** | 3/15, 3/15, 3/12 | gemini, qwen3, groq |
| [10](#10-a-numeração-interna-do-pool-vaza-para-o-texto-que-o-aluno-lê) | Numeração do pool vaza | quiz | 3/15 | **0/10** | gemini |
| [11](#11-o-prompt-de-cloze-gera-exercício-sem-resposta-certa-possível) | Cloze sem resposta possível | cloze | 7/15 | **0/13** | groq |
| [12](#12-exercício-que-não-se-ancora-no-card-do-usuário) | Exercício não ancorado | quiz | 6/15 | **1/15** | qwen3 |
| [8](#8-a-rotação-obrigatória-das-estratégias-dilui-a-premissa) | Rotação dilui a premissa | quiz | sem número | `variation_share` **0,40** | **instrumentado, não corrigido** |

**Item 8 é o que sobra, e deixou de ser "estrutural".** `variation_type` fez o
quiz declarar o que ele faz com a âncora, e a primeira rodada deu
`variation_share` **0,40** com `strategy_coverage` **5/5** — as duas métricas na
mesma sessão, uma dizendo saúde e a outra dizendo que 6 de 10 exercícios
reapresentam o sentido que o card já ensina. O número existe; a correção do
prompt, não.

**Duas ressalvas sobre o "depois".**

1. **O item 10 está subdimensionado.** A cota diária do Gemini (20 requisições no
   free tier) acabou no meio da rodada de confirmação: 0 vazamentos em **10**
   quizzes, não em 15. O sinal é bom — a linha de base tinha 3/15 e a primeira
   versão da regra teve 4/15 — mas a confirmação em 15 quizzes está pendente.
2. **A primeira versão da regra do item 10 piorou o defeito**, e o motivo virou
   regra de escrita de prompt neste projeto: ela listava as strings proibidas
   entre aspas, incluindo `"Card 1"`, e o modelo passou a anotar cada expressão
   com `(Card N)`. **Instrução negativa com exemplo literal prima o formato que
   proíbe.** A versão que funcionou é positiva e não escreve o literal.

Procedimento em `skills/prompt-review.md`. Mudar prompt exige confirmação do
autor — ver `CLAUDE.md`.

---

## 1. Dados de agendamento do Anki são descartados

**O que é.** `cardsInfo` devolve o card inteiro, incluindo `interval`, `factor`,
`lapses`, `reps`, `queue` e `due`. `src/anki_client.py` lê apenas
`fields.Front.value` e `fields.Back.value`. O resto é jogado fora.

**Evidência.** `anki_client.py:92-94`. Um card com 9 lapses tem exatamente a
mesma probabilidade de ser sorteado que um card maduro de oito meses.

**Impacto.** O produto se descreve como "camada de inteligência sobre o banco de
dados do usuário", mas hoje opera sobre um saco de strings.

**Justificativa revisada em 2026-08-30.** A versão anterior deste item propunha
ponderar por `lapses`/`factor` para priorizar cards maduros. A decisão
[0005](decisoes/0005-anki-fonte-de-material.md) derrubou metade disso: maturidade
não é prova de domínio — um card pode ter ficado maduro porque o usuário absorveu
o conceito por input externo, e exercitá-lo é o tédio que o projeto existe para
evitar. `interval` e `factor` saem.

O que sobrevive é `lapses`: ele mede **tropeço**, não maturidade, e tropeço é
sinal legítimo de fricção. Serve como semente de partida enquanto não houver
registro de evidência próprio.

**Bloqueia.** A partida a frio do sistema de precisão
([0006](decisoes/0006-medida-nasce-na-ferramenta.md)). Sem nenhum sinal inicial, o
primeiro dia é sorteio puro.

**Custo.** Baixo. Filtrar na query do `findCards` (`prop:lapses>2`) ou ponderar o
`random.sample` por `lapses`.

---

## 2. Nenhuma resposta do usuário é persistida

**O que é.** Não há camada de dados. A sessão é gerada, respondida e descartada.

**Evidência.** Não existe nenhum módulo de persistência no projeto.

**Impacto.** Não é possível responder "esta ferramenta está ajudando?" — não há
registro de acerto e erro por conceito. Um card errado no cloze tem a mesma
chance de reaparecer que qualquer outro.

**Bloqueia.** A detecção de lacunas por padrão de erro (`roadmap.md`) depende
inteiramente disso. Depois da [0006](decisoes/0006-medida-nasce-na-ferramenta.md)
esse item deixou de ser feature independente e virou núcleo da premissa.

**Custo.** Médio. SQLite, mas pela razão certa: histórico de resposta, não
"persistência de cards" genérica.

---

## 3. Rate limit chega ao usuário como HTTP 500

**O que é.** `services.run_session` converte qualquer exceção em
`HTTPException(500)`. Um 429 do provedor vira erro interno.

**Evidência.** `services.py:68-70`. Para Groq e OpenRouter a mensagem já é
controlada e inclui o tempo de retry quando o provedor informa
(`providers.py`), mas o status continua 500. Para Gemini, o erro do SDK cai no
`except Exception` genérico de `GeminiProvider.generate` e é repassado como está.

**Impacto.** O frontend não tem como distinguir "espere 8 segundos" de "algo
quebrou". O usuário vê a mesma tela nos dois casos.

**Custo.** Baixo. Mapear rate limit para HTTP 429 com header `Retry-After`.

---

## 4. Plausibilidade dos distratores não é medida por nada

**O que é.** O `ai-rules.md` exige distratores plausíveis, derivados de
confusões reais e de interferência do português. Nenhuma verificação existe.

**Evidência.** O auditor (`scripts/audit_exercises.py`) checa opções duplicadas
e vazias. Nada além disso. É a única regra explícita do `ai-rules.md` que
governa a qualidade central do quiz e não tem nenhuma cobertura.

**Impacto, medido.** Na linha de base de 2026-08-29 a métrica inverteu a
ordenação real. O `openai/gpt-oss-20b` tirou a melhor nota (93% limpos)
produzindo, num exercício de `interference`, as alternativas "out of your
depth" / "out of depth" / "out of your depthness" / "out of depthness" —
palavras inventadas, nenhuma interferência de português, exatamente o que o
`ai-rules.md` proíbe. O Gemini tirou 73% e produziu a única armadilha de L1
legítima da rodada ("contar sua mãe fora" para *tell off*), penalizado por
citar "Card 2" numa explicação, defeito cosmético que o aluno vê depois de já
ter respondido.

**Duas heurísticas determinísticas foram testadas e rejeitadas** contra os 62
quizzes da linha de base:

1. *Palavra inexistente na wordlist do sistema.* Pegou `depthness`, mas com 4
   falsos positivos em 5: `blotto` (gíria real, do próprio deck do usuário),
   `underwhelmed` e `wellbeing` (palavras reais fora do dicionário) e `'em`
   (contração). Precisão de 20%.
2. *Distratores parecidos demais com a resposta* (similaridade de superfície).
   Não separa: "on the hook" / "off the hook" / "in the hook" tem similaridade
   0,91 e é um exercício **bom** — discriminação legítima, que é justamente o
   que o prompt pede. "depthness" pontua 0,89. A mediana da amostra é 0,51.

A conclusão dos dois testes é que plausibilidade de distrator não é detectável
por forma superficial, porque a diferença entre um bom distrator e um inventado
é semântica.

**Ligação com a premissa.** Distrator inventado não é variação de nada. Um
exercício de `interference` cujas alternativas são palavras inexistentes não
apresenta nem o "n" nem o "+1" — é ruído com formato de exercício. Esta checagem
ausente é, portanto, a que mede se a premissa do projeto está sendo cumprida.

**Custo.** Alto. Sobram duas saídas, não excludentes: um LLM atuando como juiz
— o que é diferente de IA avaliando a resposta do aluno e portanto não conflita
com a decisão [0004](decisoes/0004-string-matching-no-cloze.md) — ou revisão
humana por amostra cega. **Restrição do autor sobre o juiz:** um LLM só serve
nesse papel se verificar e entender as premissas do projeto com maestria; juiz
que não entende o que está julgando reproduz o defeito que ele deveria detectar. O auditor já exporta a amostra (`--sample N`), com o gabarito de qual
modelo gerou cada exercício em arquivo separado. A revisão humana vem primeiro:
é ela que calibra qualquer juiz automático depois.

---

## 5. O matching do cloze marca conjugação correta como erro

**O que é.** A avaliação client-side normaliza com
`toLowerCase().trim().replace(/\s+/g, ' ')` e compara por igualdade exata contra
`target_expression` e contra `acceptable_alternatives`.

**Evidência.** `src/static/index.html:1138` e `:1192-1195`. Se a frase exige
passado e o usuário escreve "gave up on" contra um alvo "give up on", o
feedback é vermelho. Pontuação, artigo e contração produzem o mesmo resultado.

**Impacto.** Falso negativo é o erro mais caro numa ferramenta de produção
ativa: ensina ao usuário que a resposta certa está errada. A taxa real desse
falso negativo nunca foi medida.

**Agravante medido em 2026-08-29.** Parte dos exercícios já nasce quebrada,
antes de qualquer questão de matching. Em 56 exercícios de cloze da linha de
base, 6 não têm resposta certa possível: `take upon yourself` numa frase sobre
"She" ("She was hesitant to take upon yourself the enormous task"),
`get your head around` numa frase sobre "me", e alternativas que duplicam
palavra da frase ("it _____ that" com alternativa "it transpired" produz "it
it transpired"). O auditor passou a detectar isso — checagens
`person_mismatch` e `does_not_fit_the_blank` — mas **o prompt continua gerando**.
Corrigir o matching não resolve esses casos; a correção é no prompt de cloze.

**Nota de escopo.** A decisão [0004](decisoes/0004-string-matching-no-cloze.md)
congela *avaliação de texto livre pela IA*. Melhorar a normalização continua sendo
string matching e não conflita com ela.

**Bloqueia.** O exercício de família de palavras — passado, particípio, derivados
—, que é parte da premissa n+1 e está no `roadmap.md`. Enquanto "gave up on" for
marcado como erro contra o alvo "give up on", esse exercício testaria exatamente a
dimensão que o avaliador não sabe avaliar.

**Saída intermediária ainda não avaliada.** Antes de mexer no matcher, existe um
caminho mais barato: instruir o prompt a incluir as conjugações plausíveis em
`acceptable_alternatives`. Move o problema do avaliador para o gerador, não exige
código novo e é mensurável pelo auditor. Não cobre tudo — a lista é finita e o
usuário pode produzir uma forma válida fora dela —, mas nunca foi testado e é a
tentativa de menor custo.

**Custo.** Baixo a médio. Stemming leve, ignorar artigos e pontuação, aceitar
variação de conjugação do verbo principal.

---

## 6. `le=10` nos endpoints é um limite não medido

**O que é.** `/api/quiz-session` e `/api/cloze-session` aceitam `n` até 10.
Ninguém mediu qual `n` a geração sustenta sem timeout ou perda de qualidade.

**Evidência.** `routers/quiz.py:11` e `routers/cloze.py:11`. O dump de teste
antigo (removido) registrou timeouts com `n=5`.

**Impacto.** O limite ou é folgado demais (o usuário pede 10 e toma timeout) ou
apertado demais. Não dá para saber sem medir.

**Custo.** Baixo. É uma medição, não uma implementação: rodar o auditor com `n`
crescente e observar onde a latência e a taxa de item descartado disparam.

---

## 7. O campo `concept` é texto livre e inviabiliza qualquer agregação

**O que é.** `QuizItem.concept` e `ClozeItem.concept` são descritos no prompt como
*"Brief label of the concept being tested"* (`prompts.py:64`). A IA inventa o
rótulo a cada chamada. Nada normaliza, nada persiste.

**Evidência.** `prompts.py:64` e `:122`. Dois exercícios sobre a mesma estrutura
podem sair como "present perfect vs past perfect" e "tempos compostos", e o sistema
não tem como saber que são a mesma coisa.

**Parcialmente aliviado no quiz em 2026-08-30.** `QuizItem.source_expression`
copia a expressão do card, então o quiz passou a ter uma chave estável para *de
onde ele veio*. Não resolve o item: `concept` continua descrevendo *o que está
sendo testado* em prosa livre, e é essa a chave que a trilha da
[0008](decisoes/0008-trilha-e-espelho.md) precisa. Alivia a agregação por
expressão de origem; não a agregação por conceito.

**Impacto.** A trilha por conceito descrita na
[0008](decisoes/0008-trilha-e-espelho.md) é **impossível** com o modelo atual,
independente de banco de dados: agregação exige chave estável, e não há nenhuma.
Isto não é uma feature faltando, é um defeito do que existe — o campo promete
identidade e entrega rótulo.

**Custo.** Médio, e coberto pelas decisões
[0009](decisoes/0009-unidade-de-conhecimento.md) e
[0010](decisoes/0010-lista-de-conceitos.md).

---

## 8. A rotação obrigatória das estratégias dilui a premissa

**O que é.** A regra 7 do prompt de quiz (`prompts.py:53`) manda variar a
estratégia e proíbe tipos iguais consecutivos.

**Evidência.** Das cinco estratégias, `polysemy` (`prompts.py:35`) e
`discrimination` (`:20`) apresentam variação — e ambas são condicionais ao pool
(*"Use when the pool contains…"*). `production` (`:25`) e `interference` (`:30`)
testam o sentido já conhecido. A auditoria de 2026-08-29 mediu cobertura 5/5 em
todos os modelos: a rotação está sendo obedecida à risca.

**Impacto.** O sistema **garante** que parte de cada sessão não apresente
variação nenhuma, e a métrica de auditoria registra isso como saúde.

**Cuidado ao corrigir.** A rotação existe por um motivo real, registrado em
[0002](decisoes/0002-rotacao-de-estrategias.md): ela foi o antídoto contra os
"flashcards disfarçados" da Alpha v2. A correção precisa preservar o antídoto e
remover a diluição — não simplesmente remover a regra.

**É o único item do índice sem número.** Os outros quatro têm contagem medida;
este está lá como "estrutural", porque nada no auditor sabe dizer se um exercício
apresenta variação ou reapresenta o sentido que o card já ensina — que é a
premissa n+1 inteira.

**Caminho para medi-lo, registrado em 2026-08-30 e não implementado.** O mesmo
movimento que tornou o item 12 exato serviria aqui: fazer o quiz declarar o
sentido do card (`sense_on_card`) e o sentido testado (`sense_tested`), ou um
enum `variation_type`. Declarar os dois iguais é flashcard disfarçado, e é
detectável. Dá para cruzar com `quiz_type`: `polysemy` e `discrimination`
implicam sentido diferente, então declarar sentidos iguais nesses tipos é
contradição.

A ressalva honesta: isso é **declarativo** — verifica o modelo contra si mesmo,
pega contradição, não pega erro. Diferente do `source_expression`, que é
verificável contra o card. Ainda assim é a única via visível para tirar este item
do "estrutural", e o custo é dois campos. Decidir quando o item 12 estiver medido,
com dado na mão em vez de no plano.

## Instrumentado em 2026-08-30 — e o número apareceu na primeira rodada

`QuizItem.variation_type` (novo, `models.py`): enum declarando o que o quiz faz
com a âncora — `same_sense`, `other_sense`, `derived_form`, `different_particle`,
`different_register`.

**Enum e não os dois campos de sentido que este item propunha.**
`sense_on_card` + `sense_tested` seriam mais expressivos e seriam dois campos de
prosa livre — exatamente a doença do item 7, em que `concept` promete identidade
e entrega rótulo. Enum agrega e cruza com `quiz_type`.

Três coisas novas no auditor:

- `variation_contradicts_type` (ERRO) — `polysemy` e `discrimination` existem
  para apresentar sentido diferente; declarar `same_sense` neles é contradição.
  `production` e `interference` testam o sentido conhecido **por desenho**, e ali
  `same_sense` é honestidade, não defeito: punir a declaração honesta ensinaria o
  modelo a mentir.
- `empty_variation_type` (ALERTA) — quem não declara.
- `variation_share` — a fração da sessão que apresenta variação. É a premissa n+1
  em número, e entrou na tabela do `--compare`.

**Primeira medição, `v2-item8-adesao-groq`, 10 quizzes:**

| | |
|---|---|
| Adesão | **10/10** declararam o campo |
| `variation_share` | **0,40** |
| Distribuição | `same_sense` 6, `different_particle` 2, `other_sense` 1, `different_register` 1 |
| `strategy_coverage` | **5/5** |
| `variation_contradicts_type` | 1 (um `polysemy` declarando `same_sense`) |

**As duas últimas linhas juntas são o item inteiro.** Cobertura 5/5 na mesma
rodada em que 6 de 10 exercícios reapresentam o sentido que o card já ensina: a
métrica que dizia saúde e a que diz diluição, lado a lado, na mesma sessão. É o
que a [0002](decisoes/0002-rotacao-de-estrategias.md) descreveu em prosa e nunca
teve como contar.

**O que isto ainda não é.** A checagem é **declarativa**: pega o modelo se
contradizendo, não pega o modelo mentindo com coerência. Um quiz `production` que
declara `same_sense` honestamente e um que declara `other_sense` falsamente saem
iguais do auditor. Continua valendo menos que `source_expression`, que é
verificável contra o card.

**O que falta, e por que não foi feito hoje.** O número existe; a **correção do
prompt** não. Baixar `variation_share` exige mexer na regra 7 preservando o
antídoto da 0002 — e mudar prompt sem linha de base é o que esta branch existe
para não fazer. A linha de base agora existe: 0,40 no gpt-oss-20b. Falta repetir
nos outros modelos e então corrigir.

**Custo.** Baixo para o prompt, mas exige remedição contra a linha de base. É a
quinta correção de prompt pendente — todas as cinco estão no índice no topo deste
arquivo.

---

## 9. A resposta correta quase nunca cai nas últimas posições

**O que é.** O prompt de quiz define `answer_index` e nunca pede distribuição.

**Evidência.** 62 quizzes, quatro modelos independentes (Google, Alibaba, OpenAI,
Google local; de 4B a proprietário grande), linha de base de 2026-08-29:

| pos 0 | pos 1 | pos 2 | pos 3 |
|---|---|---|---|
| 38 (61%) | 22 (35%) | 2 (3%) | 0 (0%) |

A última alternativa **nunca** foi a resposta.

> Recontado em 2026-08-30 a partir dos cinco `baseline-*.json`. A versão anterior
> dizia 36/22/2/0 em 60 porque deixava de fora os 2 quizzes do `baseline-groq`,
> que a contagem de 26 achados no quiz desta mesma página inclui.

**Reconfirmado no pool ideal congelado** (2026-08-30, `base-g1-*`), quatro
modelos, 60 quizzes novos:

| pos 0 | pos 1 | pos 2 | pos 3 |
|---|---|---|---|
| 31 (52%) | 14 (23%) | 15 (25%) | **0 (0%)** |

O viés para a primeira posição afrouxou (52% contra 61%) — o material ideal ajuda
—, mas a **última posição continua absolutamente nunca**. Somando os dois pools:
**0 em 122 quizzes, seis configurações de modelo, dois dias.** É o defeito mais
reproduzível do projeto e por isso lidera o índice.

**Impacto.** Quem marcar sempre a primeira acerta 60% sem saber inglês. Como o
viés é idêntico em modelos não relacionados, a causa é o prompt, não o modelo.

## Corrigido em 2026-08-30

A posição passou a ser **atribuída**, não pedida. `_answer_positions`
(`prompts.py:4`) embaralha `[i % 4]` — o que garante as quatro posições quando
n >= 4 — e a regra 2 lista a atribuição quiz a quiz. Duas partes mecânicas:

1. A lista explícita. "Varie a posição" é vago e o modelo não tem como saber o
   que já usou entre itens da mesma resposta.
2. **`answer_index` subiu para antes de `options` no `## Output Format`.**
   Geração é autorregressiva: com `options` primeiro, o modelo escrevia as
   alternativas e só depois escolhia o índice — ou seja, escolhia "onde já pôs a
   certa". Invertendo, ele se compromete com a posição antes de escrever.

**Medido, três modelos, posição 3 antes → depois:**

| Modelo | Antes | Depois | Distribuição depois |
|---|---|---|---|
| gemini-2.5-flash | 0/15 | **3/15** | 6/3/3/3 |
| qwen3:8b | 0/15 | **3/15** | 6/3/3/3 |
| gpt-oss-20b (groq) | 0/15 | **3/12** | 5/2/2/3 |

`answer_position_top_share` no Gemini caiu de 0,67 para 0,40; no Groq, de 0,80
para 0,42. O alerta `answer_position_bias` sumiu nos três. `6/3/3/3` é
exatamente a atribuição `[0,0,1,2,3]` repetida em três rodadas: obediência
perfeita no Gemini e no qwen3.

**O risco que a correção cria, e por que foi aceito.** Atribuir o índice abre a
possibilidade de o modelo declarar `answer_index: 3` e deixar a resposta certa
noutra posição — e **o auditor não detecta isso**, porque ele não sabe qual é a
resposta certa. Os três quizzes com índice 3 da rodada `v2-item9-gemini` foram
lidos um a um e os três estavam corretos. Em escala, quem pega é a amostra cega.

**Custo.** Baixo — uma instrução de distribuição no prompt de quiz. Exige
remedição contra a linha de base.

---

## 10. A numeração interna do pool vaza para o texto que o aluno lê

**O que é.** O bloco do pool é formatado como `Card 1:`, `Card 2:`
(`prompts.py:4`), e a regra 3 manda derivar distratores de outros cards. O modelo
leva a numeração adiante, para dentro da explicação.

**Evidência.** 13 ocorrências na linha de base ("Card 2", "Card 10", "not in the
pool" dentro da explicação), todas no quiz. O que dirige é combinar cards, não o
back vazio — nos 62 quizzes:

```
1 card-fonte:  4/42  (10%)
2 cards-fonte: 0/7   (0%)
4 cards-fonte: 8/13  (62%)
```

> Recontado em 2026-08-30 a partir dos `baseline-*.raw.json`. A versão anterior
> dizia 4/87 (5%) e 8/11 (73%), que não reproduzem sob nenhum recorte.

**A causa declarada não sobreviveu ao pool congelado.** Nos 60 quizzes de
`base-g1-*`, a correlação com o número de cards some:

```
1 card-fonte:  1/24  (4%)
4 cards-fonte: 2/26  (8%)
```

Quatro por cento contra oito, não quatro por cento contra sessenta e dois. Ou o
efeito vinha do material sorteado, ou nunca existiu e o recorte de 08-29 foi
ruído em amostra pequena. **Não corrigir "combinar cards" — o vazamento é real e
o mecanismo não está estabelecido.**

O que se sustenta: 6 ocorrências em 60 quizzes no pool congelado (10%), e **está
presente no Gemini** (3 das 6). É o único item além do 9 que aparece no modelo
que roda em produção.

**Impacto.** Cosmético do ponto de vista de aprendizado — o aluno vê depois de já
ter respondido — mas expõe mecânica interna e polui a explicação, que é a parte
que deveria ensinar.

## Corrigido em 2026-08-30, na segunda tentativa

A numeração precisa continuar existindo — `used_cards` depende dela —, então a
correção proíbe a citação, não remove o número. O bloco virou
`## Card Pool (internal — the learner never sees this)` e a regra 10 cobre os
três campos que o aluno lê.

**A primeira versão piorou o defeito e o achado vale mais que ela.** Ela listava
as strings proibidas entre aspas: `"Card 1"`, `"the pool"`, `"the deck"`. Medida
em `v2-item10-gemini`: **4 vazamentos em 15 quizzes contra 3 da linha de base**,
todos num único batch e todos no formato `(Card N)` — o modelo passou a anotar
cada expressão citada com o número entre parênteses:

```
'Drop it' (Card 1) is an informal way to tell someone to stop talking about a
topic. 'Lay low' (Card 2) means to avoid attention.
```

**Instrução negativa com exemplo literal prima o formato que ela proíbe.** A
versão que funcionou é positiva, manda identificar expressão só por aspas, e o
contraexemplo usa uma palavra que não aparece no bloco do pool.

| Run | Vazamentos | Quizzes |
|---|---|---|
| `base-g1-gemini` | 3 | 15 |
| `v2-item10-gemini` (1ª versão) | **4** | 15 |
| `v2-item10b-gemini` (2ª versão) | **0** | 10 |

**Ressalva de tamanho.** A cota diária do Gemini acabou no meio da rodada de
confirmação, então são 10 quizzes e não 15. Confirmar em 15 quando a cota voltar.

**Custo.** Baixo. Proibir referência a card no texto visível, ou mudar o formato
do bloco do pool para não sugerir numeração citável.

---

## 11. O prompt de cloze gera exercício sem resposta certa possível

**O que é.** Duas classes de defeito: alvo em pessoa incompatível com a frase, e
alternativa que duplica palavra já presente na frase.

**Evidência.** 5 exercícios em 56 da linha de base, 7 achados (um exercício pode
disparar as duas checagens). `take upon yourself` numa frase sobre "She" ("She was
hesitant to take upon yourself the enormous task"); `get your head around` numa
frase sobre "me" ("it took me a week to _____ its features"); "it _____ that" com
a alternativa "it transpired", que produz "it it transpired".

**Impacto.** Exercício impossível de acertar. Quando acontece, é o defeito mais
caro, porque ensina ao usuário que ele errou algo que não tinha resposta.

**Ressalva de 2026-08-30: também é condicional ao modelo.** No pool ideal
congelado, 15 exercícios de cloze por modelo — Groq **7**, Gemini **0**,
qwen3 **0**, gemma4 **0**. Em 2026-08-29, com pool sorteado, tinha sido gemma4 3
e Groq 2. O denominador comum é o Groq; o Gemini nunca produziu um. Medir a
correção em Gemini daria zero antes e zero depois.

**Estado.** O auditor **detecta** — checagens `person_mismatch` e
`does_not_fit_the_blank`, ambas de severidade ERRO. O prompt continua gerando.
Distinto do item 5: ali o avaliador rejeita resposta certa; aqui o exercício nasce
sem resposta certa, e corrigir o matching não resolve.

## Corrigido em 2026-08-30

Duas regras novas no topo do `## Rules:` do cloze, ambas procedimentais: montar a
frase com `target_expression` no lugar da lacuna e **ler de volta palavra por
palavra** antes de entregar, com concordância obrigatória quando a expressão
carrega pronome ou possessivo; e rodar o mesmo teste em cada
`acceptable_alternative`, que é inválida se repete palavra já encostada na
lacuna.

A formulação é procedimental de propósito. Escrever os dois casos medidos por
extenso ("She ... take upon yourself", "it ___ that" + "it transpired") era a
alternativa óbvia, e foi descartada pela lição da regra 10 do quiz: exemplo
literal do defeito prima o defeito.

**Medido no Groq, que é onde ele aparece:**

| Run | `does_not_fit_the_blank` | Exercícios de cloze |
|---|---|---|
| `base-g1-groq` | **7** | 15 |
| `v2-item1112-groq` | **0** | 13 |

Nenhum ERRO novo apareceu no lugar: o run fechou com 0 erros contra 3 da linha de
base, e `clean_rate` subiu de 90% para 96%.

**Não zerou, e a rodada isolada engana.** A linha de base final
(`v2-final-groq`, 15 exercícios) trouxe **4** de volta. Somando as duas medições
pós-correção: **4 em 28 (14%), contra 7 em 15 (47%) antes.** É melhora grande e
não é solução.

## O que a saída ao vivo mostrou, e a checagem não pegou — 2026-08-30

Verificação de ponta a ponta pelo servidor HTTP com o **deck real** (não o pool
congelado), 5 exercícios de cloze, `openai/gpt-oss-20b`:

```
When the stock market is booming, many investors _____.
  target_expression: "quit while you're ahead"
```

Preenchida, sai *"many investors quit while you're ahead"* — a mesma classe de
defeito que este item descreve, sobrevivendo à correção do prompt. **O auditor
não marcou.** Duas lacunas, de naturezas diferentes:

1. **Contração não reconhecida — corrigido.** O padrão procurava
   `your|yourself|yourselves`. Em `you're`, o apóstrofo fecha a borda de palavra
   antes do "r", então nada casava. Agora cobre `you`, `you're`, `you'd`,
   `you'll`, `you've`, `yours`, com o imperativo preservado como exceção.
   Reanalisar seis `.raw.json` com a checagem corrigida devolve contagens
   **idênticas**: a contração não ocorre no pool congelado, só no deck real.
2. **Sujeito nominal não detectado — aberto.** `other_subject` só procura
   pronomes, e *"many investors"* não é pronome. Cobrir isso exigiria decidir
   "esta oração tem sujeito de 3ª pessoa" por regex, que dispara em imperativo
   com objeto determinado ("Please give the report to _____"). O item 4 desta
   mesma página já rejeitou duas heurísticas por precisão ruim; não vale
   adicionar uma terceira sem medir.

**Consequência para o número.** Com a lacuna 2 aberta, **4 em 28 é piso, não
contagem exata.** Qualquer leitura deste item tem que carregar isso.

**Segundo achado da mesma rodada.** Um dos cinco exercícios nasceu **sem lacuna**
— a frase vinha com a expressão escrita por extenso. O auditor pega
(`missing_blank` e `target_in_sentence`, ambos ERRO), então é defeito de prompt
sem instrumentação faltando. Não foi corrigido nesta sessão: apareceu na
verificação final, e mudar prompt sem medir é o que o plano desta branch proíbe.

**Custo.** Baixo. Exigir no prompt que a expressão-alvo encaixe gramaticalmente na
frase construída.

**Ressalva resolvida em 2026-08-30.** A checagem `does_not_fit_the_blank` varria a
frase inteira, então "had had" ou "that that" legítimos disparavam contra qualquer
candidato. Agora compara a frase antes e depois de preencher e só reporta a
repetição que o candidato **introduziu**.

O número não estava inflado: reanalisar os cinco `baseline-*.raw.json` com a
checagem corrigida devolve os mesmos 40 achados, idênticos checagem a checagem.
A contagem que estava errada era outra — "6 em 56" não sai dos dados; são 5
exercícios distintos e 7 achados. **Não precisa reconfirmar.**

A primeira correção, porém, tinha aberto dois furos, fechados na auditoria de
2026-08-30: medir a frase original trocando a lacuna por espaço encostava as
palavras vizinhas e inventava uma repetição na linha de base, mascarando a real
("to ___ to" + "talk to"); e comparar conjuntos de palavras deixava uma
repetição pré-existente apagar uma nova da mesma palavra. Agora usa contagem por
ocorrência e um marcador na lacuna, com quatro testes de regressão.

---

## 12. Exercício que não se ancora no card do usuário

**O que é.** O produto existe para gerar em cima do que o usuário já estudou. Duas
formas de quebrar isso: o exercício não referencia card nenhum, ou referencia mas
não tem nada em comum com ele.

**Evidência.** `check_grounding` (`audit_exercises.py:186`) mede exatamente isso —
a docstring dela diz *"a promessa do produto é gerar em cima do que o usuário já
estudou"*. Na linha de base disparou **5 vezes**, todas no quiz:

```
Zero sobreposição léxica entre o que é testado
  ('Pragmatic implication of a boss's message The team will be i…')
  e os cards-fonte.
```

E `ungrounded` (severidade ERRO, `used_cards` vazio) disparou numa rodada de 5
itens em 2026-08-30 — o exercício não se apoiava em card nenhum.

## Ressalva que muda a prioridade — 2026-08-30

**Este defeito não aparece em modelo de API.** Medido no mesmo pool ideal
congelado, quatro modelos, 15 quizzes cada:

| Modelo | Âncora fora do card-fonte |
|---|---|
| Gemini 2.5 Flash | 0 |
| Groq gpt-oss-20b | 0 |
| gemma4:e4b (local) | 1 |
| qwen3:8b (local) | 4 |

Somando **todo o histórico do projeto** — 15 rodadas, dois dias, incluindo
OpenRouter minimax e nemotron: **18 achados de ancoragem em modelo local, 0 em
modelo de API.**

**A causa é o próprio prompt se autocitando.** Os cinco casos são as expressões
dos exemplos embutidos nas descrições de estratégia: `sound` vem de
`prompts.py:36` (*"sound" = healthy/safe vs noise vs to seem*) e
`loop in the whole team` de `prompts.py:42`. O modelo pequeno copia o exemplo
literal que tem à mão em vez de trabalhar o pool, e depois cita `used_cards`
para parecer ancorado — num caso, os 15 cards de uma vez.

Isso reproduz o `ungrounded` de `audit/medicao-fria.json`, que também era
"Polysemy of **'sound'**", e os `weak_grounding` de 2026-08-29, que eram a
mensagem do chefe do exemplo `contextual`.

**Consequência para o plano.** Corrigir este item medindo no Ollama otimiza para
um modelo que não é o que roda em produção. Se for corrigido, medir em API. E a
correção candidata é barata: tirar as expressões literais dos exemplos de
estratégia, ou marcá-las como ilustração proibida de reusar.

---

**Impacto.** Quando acontece, é o defeito mais grave da lista: ataca a premissa
em vez da execução. Um exercício com viés de posição ainda ensina alguma coisa do
deck do usuário; um exercício não ancorado é conteúdo genérico de inglês, que é
precisamente o que o `premissas.md` diz que o projeto não faz.

Mas *quando acontece* é a parte que faltava, e a resposta é: em modelo local. A
frase anterior aqui dizia que ele era "mais grave" que os outros quatro e por isso
liderava o índice. Gravidade não é frequência — ver a ressalva acima.

**A medida ficou exata em 2026-08-30.** O quiz passou a declarar
`source_expression` — a expressão do pool em que ele se apoia, copiada do card.
Antes o quiz dizia o que testava só em prosa (`concept`, item 7), então ancoragem
só dava para estimar por sobreposição de palavras, que é o que `weak_grounding`
faz. Agora o auditor pergunta o exato: a âncora existe no card citado
(`anchor_not_in_source_card`, ERRO) e o exercício tem alguma relação com a âncora
que ele mesmo declarou (`anchor_absent_from_exercise`, ALERTA). Quem não declara
vira `empty_source_expression`. A checagem de "aparece no exercício" é frouxa de
propósito: o quiz **deve** testar uma variação da âncora, e exigir a expressão
inteira reprovaria a própria premissa.

**A investigar antes de corrigir.** A contagem não separa duas causas com
correções diferentes: o modelo ignorou o pool e inventou, ou o modelo usou o pool
e o `used_cards` veio errado. A segunda é defeito de contrato, não de conteúdo.

> **Isto não era investigável até 2026-08-30.** `services.build_items` faz
> `raw.pop("used_cards")`, então o índice que o modelo emitiu era destruído antes
> de virar registro e o `.raw.json` guardava só o placeholder
> `(source unavailable)` — idêntico nos dois casos. O auditor passou a guardar
> `used_cards_emitted` em cada item no caminho `--source direct`. **A rodada de
> medição da próxima sessão precisa ser `--source direct`**; por HTTP o servidor
> já descartou o campo e a pergunta continua sem resposta.

**Evidência preservada.** `audit/medicao-fria.json` (versionado, como as linhas
de base; o `.md` e o `.raw.json` ficam locais pela mesma regra do `.gitignore`),
rodada de 5 itens no `qwen3:8b` em 2026-08-30 12:07. O item 4 (`polysemy` — "Polysemy of
'sound'") é o `ungrounded`: pergunta sobre 'sound' significando "healthy/safe"
sem card-fonte nenhum. Estava só no scratchpad de sessão em `/tmp`, que é
apagado.

## Corrigido em 2026-08-30

Um parágrafo logo abaixo de `## Quiz Strategy Types` declarando que os exemplos
são **forma, não conteúdo**: todo quiz tem que nascer de uma expressão do pool, e
expressão que só existe no exemplo está fora. Os exemplos ficaram — são eles que
ensinam o formato de cada estratégia, e a cobertura 5/5 nunca foi o problema.

**Medido no qwen3:8b, que é onde ele aparece.** A medição precisou de duas
rodadas porque as correções 9 e 10 vieram antes e mexem no mesmo prompt:

| Run | `anchor_not_in_source_card` | `weak_grounding` | Erros |
|---|---|---|---|
| `base-g1-qwen3` | 4 | 4 | 4 |
| `v2-item910-qwen3` (9 e 10, sem o 12) | 6 | 6 | 6 |
| `v2-item1112-qwen3` (com o 12) | **1** | **1** | **2** |

**A rodada do meio é o controle e ela importa.** Sem a correção do item 12, os
achados de ancoragem *subiram* (4 → 6) com as correções 9 e 10 no prompt. Não há
mecanismo estabelecido para isso — pode ser ruído em amostra de 15, pode ser o
modelo pequeno generalizando a proibição da regra 10 para além do texto visível.
O que a terceira rodada mostra é que a correção do item 12 não só reverteu como
levou abaixo da linha de base.

**Ponto de atenção.** A pergunta que o item deixou em aberto — se o modelo ignora
o pool ou se o `used_cards` vem errado — **continua sem resposta**. As três
rodadas foram `--source direct` e `used_cards_emitted` está gravado nos `.raw`,
mas com 1 achado restante não há amostra para separar as duas causas. Fica para
quando houver contagem maior, ou some junto se não voltar.

**Custo.** Baixo se for prompt. A instrução de ancorar existe; falta ser
exigência verificável.

---

## 13. O cliente do Gemini é cache de classe e não sobrevive a troca de event loop

**O que é.** `GeminiProvider._client` é atributo de classe
(`providers.py:161`), criado uma vez e reusado para sempre. O cliente `.aio` do
`google-genai` carrega um transporte `httpx` amarrado ao event loop em que foi
construído. Se um segundo loop chamar o mesmo cliente, a chamada falha com
`Event loop is closed`.

**Evidência.** Medido em 2026-08-30, run `v2-item9-gemini`, na virada do modo
quiz para o modo cloze:

```
[cloze] rodada 1/3 via gemini/gemini-2.5-flash...
  falhou (ProviderError: gemini/gemini-2.5-flash: Event loop is closed); nova tentativa em 25s
  ok em 20.01s (5 itens)
```

O auditor chamava `asyncio.run()` uma vez **por modo**, então `--mode both
--source direct` sempre queimava uma tentativa exatamente ali. O `--retries`
mascarava: a rodada terminava "ok" e o número saía certo.

**Corrigido do lado do auditor, não do provedor.** `main` passou a rodar os dois
modos num único `asyncio.run` (`audit_exercises.py:1253`), com teste de
regressão que falha se voltarem a ser dois loops. Isso elimina a falha
observada, mas **não** a fragilidade: qualquer chamador que use mais de um event
loop no mesmo processo reproduz.

**Por que não foi corrigido no provedor.** Em produção o uvicorn tem um loop só e
o defeito não aparece — não há evidência de impacto no usuário. A correção
(indexar o cache por loop, ou detectar loop fechado e reconstruir) é barata mas
mexe em código de produção para consertar um sintoma que só o instrumento vê.
Fica registrado com a evidência, que é o que este arquivo existe para carregar.

**Impacto.** Uma requisição desperdiçada por rodada `--mode both` — em tier
gratuito, cota que não volta. Com `--retries 0`, a metade cloze da medição
falharia inteira.

**Custo.** Baixo.

---

## Registrado mas fora de escopo aqui

O formato dos cards varia legitimamente entre usuários do Anki — back vazio,
back em português, back em inglês, back longo ou curto, front como expressão ou
como frase inteira. Isso não é débito: é a realidade da fonte de dados, e o
sistema precisa lidar com ela. O auditor já mede o efeito disso através da
checagem `source_without_back`, que compara a taxa de defeito entre exercícios
construídos sobre cards com e sem back.
