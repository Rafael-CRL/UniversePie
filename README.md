# UniversePie

Ferramenta web local de aprendizado de inglês via sentence mining. A IA opera como camada de inteligência sobre o banco de dados do usuário — não gera conteúdo genérico, gera exercícios ancorados no que o usuário já estudou no Anki.

**Estado:** Alpha — funcional, em desenvolvimento ativo.

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.14 + FastAPI (assíncrono) |
| Frontend | HTML/JS/CSS puro |
| IA | Google Gemini `gemini-2.5-flash` via SDK `google-genai` |
| Fonte de dados | AnkiConnect (porta 8765), deck `English_Series` |
| Servidor | Uvicorn, porta `14567` |

## Pré-requisitos

- Anki aberto com o add-on [AnkiConnect](https://ankiweb.net/shared/info/2055492159) instalado
- Deck `English_Series` populado
- Variável de ambiente `GEMINI_API_KEY` configurada

## Rodando localmente

```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Rodar o servidor
uvicorn src.main:app --reload --port 14567
```

Acesse `http://localhost:14567`.

## Endpoints

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve o frontend |
| `/api/quiz-session?n=5` | GET | Gera `n` quizzes de múltipla escolha |
| `/api/cloze-session?n=5` | GET | Gera `n` exercícios cloze (preenchimento livre) |

## Estrutura

```
src/          código fonte (main.py, static/)
tests/        testes
docs/         contexto e regras para agentes de IA
skills/       procedimentos reutilizáveis para tarefas recorrentes
scripts/      utilitários e automações
```

## Documentação

- [`docs/CONTEXT.md`](docs/CONTEXT.md) — contexto do projeto, fluxo de dados, modelos e backlog
- [`docs/AI_RULES.md`](docs/AI_RULES.md) — regras para geração de conteúdo pela IA
- [`CLAUDE.md`](CLAUDE.md) — instruções para agentes de IA trabalhando neste repositório
