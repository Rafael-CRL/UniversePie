# UniversePie — CLAUDE.md

## O que é este projeto
Ferramenta web local de aprendizado de inglês via sentence mining. A IA opera como camada de inteligência sobre o banco de dados do usuário — não gera conteúdo genérico, gera conteúdo ancorado no que o usuário já estudou.

**Leia antes de qualquer tarefa que envolva prompts ou novos endpoints:** `docs/CONTEXT.md`
**Leia antes de qualquer tarefa que envolva geração de conteúdo pela IA:** `docs/AI_RULES.md`

---

## Stack atual

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.14 + FastAPI (assíncrono) |
| Frontend | HTML/JS/CSS puro (sem framework) |
| IA | Provedor plugável (`src/providers.py`): Gemini, Groq, Ollama local, Anthropic, DeepSeek, Kimi, Z.ai, OpenRouter |
| Fonte de dados | AnkiConnect porta 8765, deck `English_Series` |
| Servidor | Uvicorn com hot-reload, porta `14567` |

---

## Comandos

```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Rodar servidor
uvicorn src.main:app --reload --port 14567

# Auditar a qualidade dos exercícios gerados (servidor precisa estar rodando)
python scripts/audit_exercises.py --mode both --runs 2

# Auditar sem passar pelo servidor, escolhendo o provedor (Ollama não gasta cota)
python scripts/audit_exercises.py --list-providers
python scripts/audit_exercises.py --provider ollama --model qwen3:8b --cards docs/audit/pool-exemplo.json

# Verificar se AnkiConnect está respondendo
curl http://localhost:8765 -X POST -d '{"action":"version","version":6}'
```

---

## O que o agent pode fazer sem pedir confirmação
- Ler qualquer arquivo do projeto
- Rodar testes (`pytest`)
- Rodar linters
- Criar branches

## O que o agent deve pedir confirmação antes de fazer
- Commits e push
- Modificar modelos Pydantic existentes (quebra contrato)
- Modificar prompts enviados à IA (impacto direto na qualidade dos exercícios)
- Instalar novas dependências

## O que o agent não faz
- Force-push
- Modificar o deck do Anki

## Todos os provedores estão em tier gratuito

Rodar medições contra as APIs reais faz parte do trabalho e não precisa de
autorização — inclusive no Gemini. O que muda é a leitura das falhas: cota
esgotada é condição normal de operação, não defeito do código.

Falhas já observadas e o que significam:

| Sintoma | Causa |
|---|---|
| Groq HTTP 429 | limite de requisições por minuto |
| Groq HTTP 413 | limite de tokens por minuto — o `max_tokens` reservado conta no total |
| Groq HTTP 400 "Failed to generate JSON" | saída truncada pelo teto de tokens; a causa real vem em `failed_generation` |
| OpenRouter 429 upstream | pool gratuito compartilhado entre todos os usuários; sai como erro no corpo, às vezes com HTTP 200 |
| Gemini HTTP 503 UNAVAILABLE | alta demanda momentânea no modelo |

Antes de investigar como bug, considerar a cota. Antes de concluir que um
provedor não funciona, tentar de novo — o auditor já tem `--retries` com
backoff exatamente por isso.

---

## Decisões consolidadas — não rediscutir

1. **Pool em lote:** múltiplos cards enviados em uma única chamada ao provedor. Não voltar para 1-para-1.
2. **String matching no cloze:** avaliação de texto livre pela IA é prematura no alpha. Manter até decisão explícita.
3. **HTML/JS puro no frontend:** migração para Svelte está no backlog, não é prioridade agora.
4. **Nuances são condicionais:** o sistema não força nuances onde não existem.

---

## Estrutura de pastas

```
src/          código fonte (main.py e módulos futuros)
tests/        testes
docs/         contexto e regras para agentes
skills/       procedimentos reutilizáveis para tarefas recorrentes
scripts/      utilitários e automações
```
