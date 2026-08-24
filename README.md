# UniversePie

Ferramenta web local de aprendizado de inglês via sentence mining. A IA opera como camada de inteligência sobre o banco de dados do usuário — não gera conteúdo genérico, gera exercícios ancorados no que o usuário já estudou no Anki.

**Estado:** Alpha — funcional, em desenvolvimento ativo.

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.14 + FastAPI (assíncrono) |
| Frontend | HTML/JS/CSS puro |
| IA | Google Gemini `gemini-2.5-flash` via SDK `google-genai` |
| Fonte de dados | AnkiConnect (porta 8765) |
| Servidor | Uvicorn, porta `14567` |

## Pré-requisitos

- Anki aberto com o add-on [AnkiConnect](https://ankiweb.net/shared/info/2055492159) instalado
- Um deck com cards cujo note type tenha campos chamados `Front` e `Back` (o nome do próprio note type não importa — só os nomes dos campos)
- Chave da API do Google Gemini

## Rodando localmente

```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Configurar variáveis de ambiente
cp .env.example .env
# edite o .env e preencha GEMINI_API_KEY (e ANKI_DECK_NAME, se seu deck não se chamar "English_Series")

# Rodar o servidor
uvicorn src.main:app --reload --port 14567
```

Acesse `http://localhost:14567`. A tela inicial mostra se o Anki, o deck e a `GEMINI_API_KEY` estão configurados corretamente antes de você iniciar uma sessão.

## Endpoints

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve o frontend |
| `/api/status` | GET | Diagnóstico: Anki conectado, deck encontrado, `GEMINI_API_KEY` configurada |
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
