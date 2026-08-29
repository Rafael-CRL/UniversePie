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
- Chamadas reais à API do Gemini fora do servidor rodando localmente
- Modificar o deck do Anki

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
