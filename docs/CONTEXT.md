# UniversePie — Contexto do Projeto

**Estado:** Alpha v3.1 — funcional, em desenvolvimento ativo.

---

## Problema e solução

Sentence mining exige trabalho manual repetitivo e perde nuances essenciais.
A solução não é automatizar a criação de cards — é fazer a IA operar com inteligência sobre o que o usuário já estudou, gerando exercícios que testam produção ativa, não reconhecimento passivo.

Público-alvo: intermediários/avançados. Vocabulário básico não é material de card.

---

## Endpoints ativos

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve `index.html` |
| `/api/quiz-session?n=5` | GET | Gera `n` quizzes de múltipla escolha |
| `/api/cloze-session?n=5` | GET | Gera `n` exercícios cloze (preenchimento livre) |

---

## Fluxo de dados

1. Endpoint recebe `n`
2. Busca IDs do deck via AnkiConnect (cache em memória)
3. Seleciona pool de `n * 3` cards aleatórios
4. Busca conteúdo em lote (`cardsInfo`), sanitiza HTML (`strip_html`)
5. Envia pool inteiro em uma única chamada ao Gemini
6. Gemini retorna `n` exercícios em JSON com referências aos cards usados
7. Backend mapeia `used_cards` → `source_cards` e valida via Pydantic

---

## Modelos Pydantic

**Quiz:**
- `SourceCard`: `front`, `back`
- `QuizItem`: `quiz_type`, `concept`, `question`, `options[4]`, `answer_index`, `explanation`, `source_cards[]`
- `QuizSession`: `quizzes[]`, `total`

**Cloze:**
- `ClozeItem`: `concept`, `sentence` (com `_____`), `target_expression`, `acceptable_alternatives[]`, `hint`, `commonality` (`common`|`moderate`|`niche`), `context_note`, `explanation`, `source_cards[]`
- `ClozeSession`: `exercises[]`, `total`

---

## Modos de exercício

**Quiz:** 5 estratégias rotativas — `discrimination`, `production`, `interference`, `polysemy`, `contextual`. Badges por tipo. Distratores exploram interferência L1 (português).

**Cloze:** Frase com lacuna, sem opções. Avaliação client-side por string matching normalizado. Feedback em 3 níveis: correto (verde) / alternativa válida (azul) / incorreto (vermelho). Badge de `commonality`.

---

## Backlog (não implementado)

- Staged Area — fila de revisão antes de virar card
- SQLite — persistência de cards, exemplos, tags
- Migração Svelte + Vite
- Inputs além do Anki (texto colado, PDF, extensão de browser, MPV)
- TTS
- FSRS próprio
- Tags automáticas por área
- Detecção de lacunas por padrão de erro
- Exercícios de escrita livre (depende de avaliação confiável pela IA)
- Abstração do provedor de IA (hardcoded para Gemini hoje)
