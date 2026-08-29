# UniversePie

Ferramenta web local de aprendizado de inglês via sentence mining. A IA opera como camada de inteligência sobre o banco de dados do usuário — não gera conteúdo genérico, gera exercícios ancorados no que o usuário já estudou no Anki.

**Estado:** Alpha — funcional, em desenvolvimento ativo.

## Stack

| Componente | Tecnologia |
|---|---|
| Backend | Python 3.14 + FastAPI (assíncrono) |
| Frontend | HTML/JS/CSS puro |
| IA | Qualquer provedor: Gemini, Groq, Anthropic, DeepSeek, Kimi, Z.ai, OpenRouter ou modelos locais via Ollama |
| Fonte de dados | AnkiConnect (porta 8765) |
| Servidor | Uvicorn, porta `14567` |

## Pré-requisitos

- Anki aberto com o add-on [AnkiConnect](https://ankiweb.net/shared/info/2055492159) instalado
- Um deck com cards cujo note type tenha campos chamados `Front` e `Back` (o nome do próprio note type não importa — só os nomes dos campos)
- Um provedor de IA configurado: uma chave de API (Gemini, Groq, Anthropic, …) **ou** Ollama rodando localmente, que não precisa de chave

## Rodando localmente

```bash
# Instalar dependências
pip install -r requirements.txt --break-system-packages

# Configurar variáveis de ambiente
cp .env.example .env
# edite o .env: escolha AI_PROVIDER e preencha a chave dele
# (e ANKI_DECK_NAME, se seu deck não se chamar "English_Series")

# Rodar o servidor
uvicorn src.main:app --reload --port 14567
```

Acesse `http://localhost:14567`. A tela inicial mostra se o Anki, o deck e o provedor de IA estão configurados corretamente antes de você iniciar uma sessão.

## Provedores de IA

O provedor é configuração, não código: `AI_PROVIDER` e `AI_MODEL` no `.env`.

| Provedor | Chave | Modelo padrão | Observação |
|---|---|---|---|
| `gemini` | `GEMINI_API_KEY` | `gemini-2.5-flash` | padrão |
| `groq` | `GROQ_API_KEY` | `openai/gpt-oss-20b` | rápido; a resposta traz os headers de rate limit |
| `ollama` | — | `qwen3:8b` | local, sem chave e sem rate limit; timeout de 900s |
| `anthropic` | `ANTHROPIC_API_KEY` | `claude-sonnet-5` | JSON via prefill (a API não tem modo JSON) |
| `openrouter` | `OPENROUTER_API_KEY` | `minimax/minimax-m3:free` | catálogo com modelos `:free`; o pool gratuito é compartilhado, então 429 do provedor de baixo é rotina |
| `deepseek` · `kimi` · `zai` | chave própria | ver `.env.example` | compatíveis com a API da OpenAI |
| `custom` | `AI_API_KEY` | `AI_BASE_URL` | vLLM, llama.cpp, LM Studio ou qualquer endpoint compatível |

```bash
python scripts/audit_exercises.py --list-providers   # o que está configurado e o que falta
```

Modelos menores costumam cercar o JSON em ```` ```json ````, narrar antes dele ou trocar o nome da chave da lista — o `ai_client` recupera esses casos em vez de descartar a sessão. Agregadores como o OpenRouter às vezes devolvem HTTP 200 com o erro do provedor de baixo dentro do corpo; a mensagem que chega ao usuário é a de lá, com o tempo de retry quando informado.

## Testes

```bash
pytest
```

Cobre as partes que não dependem de Anki nem Gemini rodando: sanitização de HTML, validadores dos modelos Pydantic, o mapeamento `used_cards` → `source_cards` e as checagens do auditor de exercícios.

## Auditoria de qualidade dos exercícios

`scripts/audit_exercises.py` coleta sessões reais da API e roda checagens determinísticas sobre cada exercício gerado: vazamento da mecânica interna (`Card 6`, "from the cards"), resposta entregue no enunciado ou na dica, reconhecimento passivo onde o prompt exige produção ativa, exercício sem card-fonte, `context_note` faltando em expressão não-`common`, viés de posição e de tamanho da resposta correta, cobertura das 5 estratégias de quiz.

```bash
# via HTTP: audita o servidor rodando (precisa de Anki aberto)
python scripts/audit_exercises.py                      # 3 rodadas de quiz, n=5
python scripts/audit_exercises.py --mode both --runs 2

# modo direto: escolhe o provedor por rodada, sem reiniciar o servidor
python scripts/audit_exercises.py --provider groq --model openai/gpt-oss-120b
python scripts/audit_exercises.py --provider ollama --model gemma4:e4b

# mesmo pool de cards para todos, senão a comparação mistura modelo com sorteio
python scripts/audit_exercises.py --save-cards docs/audit/pool.json --runs 0
python scripts/audit_exercises.py --provider ollama --cards docs/audit/pool.json --tag qwen

# comparar e reanalisar
python scripts/audit_exercises.py --compare docs/audit/groq.json docs/audit/qwen.json
python scripts/audit_exercises.py --from-raw docs/audit/qwen.raw.json   # sem gastar cota
```

`docs/audit/pool-exemplo.json` é um pool de 15 cards no formato esperado — dá para auditar qualquer provedor sem o Anki aberto.

Cada run escreve três arquivos em `docs/audit/`: `.md` (leitura, com a resposta correta marcada), `.json` (findings e estatísticas, para comparar versões de prompt) e `.raw.json` (respostas cruas da API). O script sai com código != 0 quando encontra findings de severidade ERRO — use como portão antes de aceitar uma mudança de prompt.

## Endpoints

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Serve o frontend |
| `/api/status` | GET | Diagnóstico: Anki conectado, deck encontrado, `GEMINI_API_KEY` configurada |
| `/api/quiz-session?n=5` | GET | Gera `n` quizzes de múltipla escolha |
| `/api/cloze-session?n=5` | GET | Gera `n` exercícios cloze (preenchimento livre) |

## Estrutura

```
src/
  main.py           cria o app FastAPI, monta os routers, serve o frontend
  config.py         variáveis de ambiente e constantes
  models.py         schemas Pydantic (Quiz*, Cloze*, SourceCard)
  anki_client.py    integração com AnkiConnect (busca e parsing de cards)
  ai_client.py      integração com o Gemini (chamadas de geração)
  prompts.py        prompts enviados ao Gemini
  services.py       mapeamento de source_cards + validação dos itens gerados
  routers/          endpoints (quiz, cloze, status)
  static/           frontend (HTML/JS/CSS puro)
tests/        testes
scripts/      utilitários (auditoria de qualidade dos exercícios)
docs/         contexto e regras para agentes de IA
skills/       procedimentos reutilizáveis para tarefas recorrentes
```

## Documentação

- [`docs/CONTEXT.md`](docs/CONTEXT.md) — contexto do projeto, fluxo de dados, modelos e backlog
- [`docs/AI_RULES.md`](docs/AI_RULES.md) — regras para geração de conteúdo pela IA
- [`docs/DEBITO_TECNICO.md`](docs/DEBITO_TECNICO.md) — defeitos e lacunas conhecidos, com a evidência de cada um
- [`CLAUDE.md`](CLAUDE.md) — instruções para agentes de IA trabalhando neste repositório
