# Sessão de 2026-08-30 — extração das premissas

**Tipo: registro — migrado.** O conteúdo durável está em `premissas.md`, nos ADRs `0005`–`0013` e em `historico/README.md`. Mantido pela narrativa da descoberta do termo "n+1"; não é referência ativa.

Registro do que foi extraído, decidido e descoberto. A sessão foi de perguntas
(`/grill-me`), não de código: nenhuma linha de `src/` mudou.

**Motivo, nas palavras do autor:** havia dúvidas e inconsistências sobre o
entendimento do projeto, e isso estava prejudicando a qualidade do desenvolvimento
e dos testes.

---

## O que foi produzido

`premissas.md`, 13 ADRs em `decisoes/`, `roadmap.md` e `arquitetura.md`
(substituindo o antigo `CONTEXT.md`), `historico/` com o cofre importado, e
reestruturação da documentação inteira.

## A descoberta principal

O termo **"n+1"** — que a sessão anterior registrou como "não aparece em nenhum
arquivo do repositório" — **estava documentado**, fora do repositório, e com uma
definição diferente da que o autor usa hoje.

Em `historico/planejamento-geral.md`:

> **n+1 natural:** exemplos gerados podem introduzir vocabulário levemente acima
> do nível atual

Isso é uma leitura de Krashen: incremento de **vocabulário**. A revisão seguinte
(`historico/planejamento-geral-2.md`) **removeu esse princípio** e o substituiu por
dois outros — "o quanto de novidade introduzir é julgamento da IA, não uma regra
fixa" e "sem estar presa a introduzir exatamente um conceito novo por vez".

Ou seja: o incremento fixo já tinha sido rejeitado por escrito, uma vez. O termo
sobreviveu na fala do autor com um sentido diferente e mais rico — variação e
nuance de material já conhecido — que também já estava escrito, em
`historico/brainstorm.md`, com os exemplos de *run* e *flip*.

**A premissa não estava indocumentada. Estava fora do controle de versão, num
cofre que o repositório nunca referenciou.** É por isso que o cofre foi importado.

## Conceitos recuperados do cofre

Estavam nos planejamentos originais e nunca chegaram ao repositório:

- **Gramática emergente** — padrões surgem do volume de input, não são ensinados;
  "dar nome aos bois". É o fundamento das decisões `0009` e `0010`.
- **`commonality` como estatística de nicho** — não só transparência sobre a fonte,
  mas revelar em quais áreas o usuário tem vocabulário.
- **Tags como índice do conhecimento**, não categoria passiva.
- **Exposição passiva de sinônimos**, no espírito do DeepL.
- **"Conceitos dominados saem da rotação"** e o princípio de **equilíbrio**.

## O que a sessão descobriu no código

| Achado | Onde |
|---|---|
| A premissa central existe no prompt em **uma linha** — regra 9, um "prioritize" | `prompts.py:54` |
| Só 2 das 5 estratégias apresentam variação, e ambas são condicionais ao sorteio | `prompts.py:20`, `:35` |
| A regra 7 **garante** que parte da sessão não seja n+1 | `prompts.py:52` |
| Família de palavras: **0 ocorrências** nos prompts, apesar de central na premissa | `prompts.py` |
| O cloze é mais fiel à premissa que o quiz — exige contexto diferente do card | `prompts.py:93` |
| `concept` é texto livre reinventado a cada chamada: agregação impossível | `prompts.py:64` |
| `skills/prompt-review.md` reprovava quem reduzisse a rotação — desfaria a correção | skill |

## Medição feita nesta sessão

Custo de classificar o deck inteiro contra uma lista de conceitos, para responder
se a decisão `0010` escala além do deck do autor:

- 166 caracteres por card em média (~47 tokens), medido em `audit/pool-real.json`
- 1267 tokens de prompt para 15 cards, medido em `audit/history.jsonl`
- **2000 cards ≈ 40 chamadas, ~110k tokens de entrada, ~24k de saída** — cerca de
  20 minutos no tier gratuito mais apertado, gratuito no Ollama

Conclusão: o custo não é o token. É que a classificação precisa ser **job
incremental e retomável**, e que auditar 2000 classificações à mão é impossível —
o que só a lista fechada torna amostrável.

## O que não confiar desta sessão

- **Nada foi medido sobre qualidade de exercício.** A sessão foi de extração de
  premissa. Os quatro achados de prompt não foram corrigidos nem remedidos.
- **As decisões `0009` e `0010` foram tomadas em nível de visão geral.** São
  acionáveis, mas o autor pediu — e o ADR registra — sessão dedicada antes da
  implementação.
- **O loop de precisão não foi desenhado.** A precedência entre os três sinais
  está fixada (`0007`); a fórmula, não.

## Próximo passo

Pela decisão `0013`: corrigir os quatro prompts e remedir contra
`audit/baseline-*.json`. Depois, sessão de planejamento do núcleo n+1.
