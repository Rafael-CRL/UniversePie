# UniversePie — Contexto do Projeto

**Estado:** Alpha v3.1 — funcional, em desenvolvimento ativo.

---

## Problema e solução

Sentence mining exige trabalho manual repetitivo e perde nuances essenciais.
A solução não é automatizar a criação de cards — é fazer a IA operar com inteligência sobre o que o usuário já estudou, gerando exercícios que testam produção ativa, não reconhecimento passivo.

Público-alvo: intermediários/avançados. Vocabulário básico não é material de card.

---

## Origem do nome e filosofia

"UniversePie" vem da frase de Carl Sagan: *"se você quer fazer uma torta de
maçã do zero, primeiro precisa inventar o universo"*. A ideia central é que
todo conhecimento — ciência, arte, linguagem — é construído em camadas, peça
por peça, geração sobre geração, até formar algo completo. Fluência em um
idioma segue a mesma lógica: milhares de pedacinhos de linguagem, acumulados
e reconectados, até formarem algo íntegro e fluido. O produto existe para
tornar essa acumulação visível e intencional — cada exercício é literalmente
reconstruído a partir de fragmentos que o próprio usuário já estudou.

Isso informa tom, não só mecânica: seriedade pedagógica não é sinônimo de
frieza visual ou de linguagem. O produto pode ser rigoroso no conteúdo e
ainda assim caloroso, colorido, com personalidade — o que fica de fora é
gamificação vazia (pontuação artificial, streaks, mascotes, conquistas), não
o calor ou a cor. Ver `skills/stitch-design-exploration.md` para como essa
filosofia se traduz em prompts de design de UI.

---

## Provedor de IA

Escolhido por `AI_PROVIDER`/`AI_MODEL` no `.env`, implementado em `src/providers.py`.
Gemini (padrão), Groq, Ollama (local, sem chave nem rate limit), Anthropic, e os
compatíveis com a API da OpenAI (DeepSeek, Kimi, Z.ai, OpenRouter, `custom`).

Trocar de provedor é o que torna a auditoria de qualidade viável: o tier gratuito
do Gemini não aguenta rodadas longas, e comparar o mesmo pool de cards em modelos
diferentes separa "o prompt está ruim" de "o modelo é fraco".

---

## Endpoints ativos

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve `index.html` |
| `/api/quiz-session?n=5` | GET | Gera `n` quizzes de múltipla escolha |
| `/api/cloze-session?n=5` | GET | Gera `n` exercícios cloze (preenchimento livre) |
| `/api/status` | GET | Diagnóstico: Anki, deck, provedor de IA ativo |

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
