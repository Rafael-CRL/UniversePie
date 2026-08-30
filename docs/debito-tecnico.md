# Débito técnico

Problemas identificados e ainda não resolvidos. Cada entrada carrega a evidência
que a originou — sem isso, daqui a alguns meses nenhuma delas é acionável.

Este arquivo é diferente do `roadmap.md`: lá ficam features não implementadas,
aqui ficam defeitos e lacunas do que já existe.

Última revisão: 2026-08-30.

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

## Registrado mas fora de escopo aqui

O formato dos cards varia legitimamente entre usuários do Anki — back vazio,
back em português, back em inglês, back longo ou curto, front como expressão ou
como frase inteira. Isso não é débito: é a realidade da fonte de dados, e o
sistema precisa lidar com ela. O auditor já mede o efeito disso através da
checagem `source_without_back`, que compara a taxa de defeito entre exercícios
construídos sobre cards com e sem back.

---

## 7. O campo `concept` é texto livre e inviabiliza qualquer agregação

**O que é.** `QuizItem.concept` e `ClozeItem.concept` são descritos no prompt como
*"Brief label of the concept being tested"* (`prompts.py:64`). A IA inventa o
rótulo a cada chamada. Nada normaliza, nada persiste.

**Evidência.** `prompts.py:64` e `:118`. Dois exercícios sobre a mesma estrutura
podem sair como "present perfect vs past perfect" e "tempos compostos", e o sistema
não tem como saber que são a mesma coisa.

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

**O que é.** A regra 7 do prompt de quiz (`prompts.py:52`) manda variar a
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

**Custo.** Baixo, mas exige remedição contra a linha de base. É a quarta correção
de prompt pendente; as outras três estão em
`sessoes/2026-08-29-auditoria.md`.
