# Dark Side of the Moon — Contexto e Handoff para IA

**Este arquivo serve como ponto de entrada para qualquer agente de IA que for dar continuidade a este projeto. Ele reflete o estado real da implementação e as decisões já consolidadas.**

**Última atualização:** Alpha v3.1 (2026-08-01)

---

## 1. O Projeto e a Filosofia

- **O que é:** Ferramenta web local para aprendizado de idiomas (foco inicial: inglês).
- **O problema:** O aprendizado por sentence mining exige trabalho manual repetitivo. Além disso, o aprendizado raso ignora nuances essenciais ("down the street" ≠ "descendo a rua"; "but" em "I wish nothing but the best" ≠ "mas").
- **A solução:** O usuário fornece input, a IA atua como motor inteligente sobre o banco de dados — extrai conceitos centrais, captura nuances (apenas quando existem), gera exemplos diversos e testa o conhecimento com exercícios de produção ativa, não apenas reconhecimento passivo.
- **Público-alvo:** Intermediários/Avançados. Foco em estruturas, phrasal verbs, polissemia, expressões idiomáticas e nuances contextuais. Não é para vocabulário básico.

---

## 2. Arquitetura Atual (Implementada)

| Componente | Tecnologia |
|---|---|
| **Backend** | Python 3.14 + FastAPI (assíncrono) |
| **Frontend** | HTML/JS/CSS puro (sem framework, servido pelo FastAPI) |
| **IA** | Google Gemini (`gemini-2.5-flash`) via SDK `google-genai` |
| **Fonte de dados** | AnkiConnect (porta 8765, deck `English_Series`) |
| **Servidor** | Uvicorn com hot-reload, porta `14567` |
| **Dependências** | `fastapi`, `uvicorn`, `httpx`, `google-genai` |

**Nota:** O planejamento original (`PlanejamentoGeral2.md`) mencionava Svelte+Vite como frontend e Claude como IA. Essas escolhas foram substituídas durante a execução do Alpha para simplificar a prova de conceito. A migração para Svelte e a abstração do provedor de IA permanecem como possibilidades futuras.

---

## 3. Estado Atual — O Que Já Funciona

### Endpoints

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve `index.html` |
| `/api/quiz-session?n=5` | GET | Gera `n` quizzes de múltipla escolha |
| `/api/cloze-session?n=5` | GET | Gera `n` exercícios cloze (preenchimento sem opções) |

### Modelos Pydantic (`main.py`)

- **`SourceCard`**: `front`, `back` — referência ao card original do Anki.
- **`QuizItem`**: `quiz_type`, `concept`, `question`, `options[4]`, `answer_index`, `explanation`, `source_cards[]`.
- **`QuizSession`**: `quizzes[]`, `total`.
- **`ClozeItem`**: `concept`, `sentence` (com `_____`), `target_expression`, `acceptable_alternatives[]`, `hint`, `commonality` (`common`|`moderate`|`niche`), `context_note`, `explanation`, `source_cards[]`.
- **`ClozeSession`**: `exercises[]`, `total`.

### Fluxo de Dados

1. O endpoint recebe `n` (quantidade de exercícios).
2. Busca IDs do deck do Anki via AnkiConnect (com cache em memória).
3. Seleciona um pool de `n * 3` cards aleatórios (pool maior para dar contexto à IA).
4. Busca conteúdo dos cards em lote (`cardsInfo`), sanitiza HTML (`strip_html`).
5. Envia o pool inteiro em **uma única chamada** ao Gemini com um prompt especializado.
6. O Gemini retorna `n` exercícios em JSON, com referências aos cards utilizados (`used_cards`).
7. O backend mapeia `used_cards` de volta para `source_cards` e valida via Pydantic.

### Modos de Exercício no Frontend

**Quiz (múltipla escolha):**
- 5 estratégias rotativas: `discrimination`, `production`, `interference`, `polysemy`, `contextual`.
- Badges coloridos por tipo de estratégia.
- Distratores instruídos a explorar interferência L1 (português) e confusões reais.

**Cloze (preenchimento livre):**
- Frase com lacuna, sem opções. O usuário digita a resposta.
- Avaliação client-side: comparação normalizada contra `target_expression` + `acceptable_alternatives`.
- Feedback graduado: correto (verde) / alternativa válida (azul) / incorreto (vermelho).
- Badge de `commonality` com `context_note` para expressões não comuns.
- Hint colapsável.

**Compartilhado:**
- Barra de progresso, resumo de sessão com conceitos errados destacados, atalhos de teclado.
- Cards-fonte do Anki em área colapsável de debug.

---

## 4. Decisões Consolidadas

1. **Pool em lote, não 1-para-1.** O envio de múltiplos cards em uma única chamada ao Gemini permite que a IA identifique relações, agrupe famílias de palavras e crie distratores a partir de cards reais do deck.
2. **Reconhecimento passivo é insuficiente.** O quiz de múltipla escolha testa reconhecimento. O cloze testa produção. Ambos são necessários, mas produção é o teste real.
3. **Transparência sobre fontes.** O deck contém cards minerados de séries, filmes e artigos. Algumas expressões são nicho. O sistema classifica (`common`/`moderate`/`niche`) e explica em vez de tratar tudo como igualmente relevante.
4. **Avaliação de texto livre pela IA é prematura.** Para exercícios de escrita livre (Scenario Writing, Register Shifting), a IA não avalia com confiabilidade suficiente no estágio alpha. O cloze foi escolhido por restringir o espaço de resposta a uma expressão, viabilizando avaliação por string matching.

---

## 5. O que NÃO foi implementado (Backlog)

Estas funcionalidades constam nos planejamentos originais e permanecem pendentes:

- **Staged Area** — fila de revisão onde o input do usuário é processado antes de virar card.
- **Banco de dados SQLite** — modelagem de cards, exemplos, nuances, tags.
- **Frontend em Svelte + Vite** — migração do HTML/JS puro atual.
- **Inputs além do Anki** — texto colado, PDF, extensão de browser, integração MPV.
- **TTS (Text-to-Speech)** — áudio nos cards.
- **FSRS próprio** — algoritmo de repetição espaçada independente do Anki.
- **Tags automáticas** — categorização por área (tecnologia, culinária, etc.).
- **Detecção de lacunas** — identificação de padrões de erro recorrentes.
- **Exercícios de escrita livre** — dependem de avaliação confiável de texto pela IA.
- **Abstração do provedor de IA** — atualmente hardcoded para Gemini.

---

## 6. Arquivos de Referência

| Arquivo | Conteúdo | Status |
|---|---|---|
| `PlanejamentoGeral2.md` | Visão completa do projeto, princípios de geração de conteúdo, filosofia. | **Válido** — referência principal para filosofia e regras da IA. |
| `Planejamento Geral.md` | Versão anterior do planejamento. | **Parcialmente obsoleto** — superado pelo `PlanejamentoGeral2.md`. |
| `CHANGELOG.md` | Registro cronológico de todas as implementações e decisões (v1 → v3.1). | **Válido e atualizado.** |
| `Pespectiva de Criacão.md` | Brainstorming original, exemplos de uso, motivação do projeto. | **Válido** — matéria bruta de referência. |
| `Expressões de Fundamento.md` | Lista de expressões e phrasal verbs de referência. | **Válido** — vocabulário-amostra. |
| `Sentence Mining.md` | Sentenças mineradas avulsas. | **Válido** — material bruto. |
| `main.py` | Backend FastAPI completo. | **Código ativo.** |
| `index.html` | Frontend HTML/JS/CSS completo. | **Código ativo.** |

---

## 7. Instruções para a Próxima IA

1. Leia este arquivo primeiro. Ele reflete o estado real.
2. Leia `PlanejamentoGeral2.md` para a filosofia e as regras de geração de conteúdo — elas continuam válidas e devem guiar qualquer prompt futuro.
3. Consulte `CHANGELOG.md` para o histórico detalhado de decisões.
4. Siga as regras globais do perfil do usuário (`user_global`): comunicação técnica, seca, direta. Zero jargão de marketing.
5. Não replaneje o que já foi decidido. Vá direto para a execução do que o usuário pedir.
6. Se precisar de contexto sobre *por que* algo foi feito de determinada forma, o `CHANGELOG.md` documenta os princípios por trás de cada decisão.
