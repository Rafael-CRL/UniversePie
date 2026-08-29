# Débito técnico

Problemas identificados e ainda não resolvidos. Cada entrada carrega a evidência
que a originou — sem isso, daqui a alguns meses nenhuma delas é acionável.

Este arquivo é diferente do backlog do `docs/CONTEXT.md`: lá ficam features não
implementadas, aqui ficam defeitos e lacunas do que já existe.

Última revisão: 2026-08-29.

---

## 1. Dados de agendamento do Anki são descartados

**O que é.** `cardsInfo` devolve o card inteiro, incluindo `interval`, `factor`,
`lapses`, `reps`, `queue` e `due`. `src/anki_client.py` lê apenas
`fields.Front.value` e `fields.Back.value`. O resto é jogado fora.

**Evidência.** `anki_client.py:92-94`. Um card com 9 lapses tem exatamente a
mesma probabilidade de ser sorteado que um card maduro de oito meses.

**Impacto.** O produto se descreve como "camada de inteligência sobre o banco de
dados do usuário", mas hoje opera sobre um saco de strings. O estado de
aprendizado existe na fonte e é ignorado.

**Bloqueia.** Qualquer seleção de pool por dificuldade. Priorizar o que o
usuário erra é o caminho mais curto entre o deck e um exercício relevante.

**Custo.** Baixo. Ou ponderar o `random.sample` por `lapses`/`factor`, ou
filtrar na própria query do `findCards` (`prop:lapses>2`, `is:review`).

---

## 2. Nenhuma resposta do usuário é persistida

**O que é.** Não há camada de dados. A sessão é gerada, respondida e descartada.

**Evidência.** Não existe nenhum módulo de persistência no projeto.

**Impacto.** Não é possível responder "esta ferramenta está ajudando?" — não há
registro de acerto e erro por conceito. Um card errado no cloze tem a mesma
chance de reaparecer que qualquer outro.

**Bloqueia.** O item "detecção de lacunas por padrão de erro" do backlog do
`CONTEXT.md` depende inteiramente disso e hoje está listado como se fosse uma
feature independente.

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

**O que é.** O `AI_RULES.md` exige distratores plausíveis, derivados de
confusões reais e de interferência do português. Nenhuma verificação existe.

**Evidência.** O auditor (`scripts/audit_exercises.py`) checa opções duplicadas
e vazias. Nada além disso. É a única regra explícita do `AI_RULES.md` que
governa a qualidade central do quiz e não tem nenhuma cobertura.

**Impacto, medido.** Na linha de base de 2026-08-29 a métrica inverteu a
ordenação real. O `openai/gpt-oss-20b` tirou a melhor nota (93% limpos)
produzindo, num exercício de `interference`, as alternativas "out of your
depth" / "out of depth" / "out of your depthness" / "out of depthness" —
palavras inventadas, nenhuma interferência de português, exatamente o que o
`AI_RULES.md` proíbe. O Gemini tirou 73% e produziu a única armadilha de L1
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

**Custo.** Alto. Sobram duas saídas, não excludentes: um LLM atuando como juiz
— o que é diferente de IA avaliando a resposta do aluno e portanto não conflita
com a decisão consolidada nº 2 do `CLAUDE.md` — ou revisão humana por amostra
cega. O auditor já exporta a amostra (`--sample N`), com o gabarito de qual
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

**Nota de escopo.** A decisão consolidada nº 2 do `CLAUDE.md` congela
*avaliação de texto livre pela IA*. Melhorar a normalização continua sendo
string matching e não conflita com ela.

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
