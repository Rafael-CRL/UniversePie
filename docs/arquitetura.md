# UniversePie — Arquitetura

**Última revisão:** 2026-08-30
**Estado:** Alpha v3.1 — funcional, em desenvolvimento ativo.

Referência técnica: como o sistema funciona hoje. O *porquê* está em
`premissas.md` e `decisoes/`.

> **Sobre duplicação:** este arquivo descreve fluxo e contratos, não repete o
> código. Assinaturas de modelo e validadores vivem em `src/models.py` e são a
> fonte da verdade — a versão anterior deste documento os copiava e ficou
> desatualizada duas vezes.

---

## Provedor de IA

Escolhido por `AI_PROVIDER` / `AI_MODEL` no `.env`, implementado em
`src/providers.py`. Gemini (padrão), Groq, Ollama (local, sem chave nem rate
limit), Anthropic, e os compatíveis com a API da OpenAI (DeepSeek, Kimi, Z.ai,
OpenRouter, `custom`).

Trocar de provedor é o que torna a auditoria de qualidade viável: o tier gratuito
do Gemini não aguenta rodadas longas, e comparar o mesmo pool de cards em modelos
diferentes separa "o prompt está ruim" de "o modelo é fraco".

## Endpoints

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve `index.html` |
| `/api/quiz-session?n=5` | GET | Gera `n` quizzes de múltipla escolha |
| `/api/cloze-session?n=5` | GET | Gera `n` exercícios cloze |
| `/api/status` | GET | Diagnóstico: Anki, deck, provedor de IA ativo |

`n` aceita até 10. Esse teto nunca foi medido — ver `debito-tecnico.md` item 6.

## Fluxo de dados

1. Endpoint recebe `n`
2. Busca IDs do deck via AnkiConnect (cache em memória)
3. Seleciona pool de `n * 3` cards aleatórios (`anki_client.py:95`)
4. Busca conteúdo em lote (`cardsInfo`), sanitiza HTML (`strip_html`)
5. Envia o pool inteiro em **uma única chamada** ao provedor — ver
   [0001](decisoes/0001-pool-em-lote.md)
6. O provedor retorna `n` exercícios em JSON, com `used_cards` apontando para o pool
7. O backend mapeia `used_cards` → `source_cards` e valida via Pydantic

O passo 3 é sorteio uniforme sobre o deck inteiro. Não pondera por nada — ver
`debito-tecnico.md` item 1 e a decisão [0005](decisoes/0005-anki-fonte-de-material.md).

## Contratos

Definidos em `src/models.py`: `SourceCard`, `QuizItem`/`QuizSession`,
`ClozeItem`/`ClozeSession`. Validadores semânticos garantem 4 opções por quiz,
`answer_index` em 0–3 e `commonality` restrito a `common`/`moderate`/`niche`.

`QuizItem.source_expression` (2026-08-30) declara a expressão do pool em que o
quiz se apoia, copiada do card. É o análogo do `target_expression` do cloze com
sentido diferente de propósito: no cloze é a **resposta**, no quiz é a **âncora**
— o exercício existe para testar uma variação dela. É opcional com default vazio,
para que o item não declarado vire número no auditor em vez de ser descartado
pelo `build_items`.

Modificar esses modelos quebra contrato com o frontend e exige confirmação — ver
`CLAUDE.md`.

## Modos de exercício

Quiz e cloze são os mecanismos **atuais**, não os definitivos — ver `premissas.md`.

**Quiz.** Múltipla escolha, 5 estratégias rotativas (`discrimination`,
`production`, `interference`, `polysemy`, `contextual`), badge por tipo,
distratores instruídos a explorar interferência L1. A rotação obrigatória tem
revisão pendente — ver [0002](decisoes/0002-rotacao-de-estrategias.md).

**Cloze.** Frase com lacuna, sem opções. Avaliação client-side por string matching
normalizado ([0004](decisoes/0004-string-matching-no-cloze.md)), feedback em 3
níveis, badge de `commonality`.

## Auditoria

`scripts/audit_exercises.py` — checagens determinísticas sobre os exercícios
gerados, contra o servidor (`--source http`) ou chamando a geração no processo
(`--source direct`). Dados em `audit/`, com `history.jsonl` acumulando uma linha
por run. Ver `README.md` para os comandos e `sessoes/2026-08-29-auditoria.md` para
a linha de base e o que ela não permite concluir.
