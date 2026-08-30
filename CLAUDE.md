# UniversePie — CLAUDE.md

## O que é este projeto
Ferramenta web local de aprendizado de inglês via sentence mining. A IA opera sobre o
banco de dados do usuário: reforça o que ele já estudou **e apresenta variações e
outros usos daquilo** — outros sentidos, formas derivadas, mudanças de partícula,
registro. A aposta é encurtar o caminho que normalmente exige milhares de horas de
input. Isso é a premissa "n+1", e ela governa o resto.

| Antes de… | Leia |
|---|---|
| qualquer tarefa de produto, seleção de card ou exercício novo | `docs/premissas.md` |
| tocar em prompt ou geração de conteúdo | `docs/ai-rules.md` |
| mexer em endpoint, fluxo ou contrato | `docs/arquitetura.md` |
| discordar de algo que parece arbitrário | `docs/decisoes/` — provavelmente já foi decidido, com o motivo |
| mexer nos prompts ou na auditoria | `docs/sessoes/` — o README aponta o plano da próxima sessão, a linha de base vigente e o que cada registro ainda sustenta |
| saber o que fazer agora | `docs/debito-tecnico.md` — o índice no topo lista as cinco correções de prompt pendentes, ordenadas por evidência |

`docs/historico/` é o planejamento original, **congelado**. Não é referência ativa
e contém instruções contrárias às decisões atuais.

## Método de trabalho
Visão geral primeiro, planejamento específico na hora de desenvolver. Decisão
tomada em nível de visão geral vem marcada como tal nos ADRs — é acionável, mas
não deve virar implementação direto a partir do documento.

Dúvida aberta é registrada como **ponto de atenção**, não resolvida à força para o
texto ficar limpo.

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

Cada uma tem um ADR em `docs/decisoes/` com contexto e consequências. A lista aqui
é índice; o raciocínio está lá.

**Sobre a premissa**
1. **Anki é fonte de material, não de medida de domínio.** `interval` alto não
   prova domínio; `lapses` é sinal de fricção e semente descartável. `0005`
2. **A medida do que o usuário sabe nasce dentro da ferramenta**, do registro de
   evidência. Precisão é acumulada, não estimada de uma vez. `0006`
3. **Autorrelato é direcionamento, não medida.** "Fácil demais" significa
   "escale", não "eu sei". Desempenho vence em conflito; texto espontâneo vence os
   dois. `0007`
4. **A trilha é espelho descritivo**, com treino sob demanda e sugestão
   dispensável. Nunca ordem obrigatória. `0008`
5. **Unidade de conhecimento em dois eixos:** expressão × tipo de variação.
   Conceito gramatical inferido na ingestão, gravado, não recalculado. `0009`
6. **Lista de conceitos fechada, versionada e derivada do próprio deck** — não de
   grade CEFR. Cada classificação grava a versão da lista. `0010`
7. **O registro de evidência prevê a origem** (`exercise` | `writing` |
   `self_report`) desde o primeiro dia. `0011`
8. **Memória em SQLite local.** Nunca gravar no deck do Anki. `0012`
9. **Ordem:** documentar → corrigir prompts e remedir → núcleo n+1. `0013`

**Sobre a implementação**
10. **Pool em lote:** múltiplos cards em uma única chamada ao provedor. Não voltar
    para 1-para-1. `0001`
11. **String matching no cloze:** avaliação de texto livre pela IA é prematura no
    alpha. Melhorar a normalização não conflita com isso. `0004`
12. **HTML/JS puro no frontend:** migração para Svelte está no backlog, não é
    prioridade agora.
13. **Nuances são condicionais:** o sistema não força nuances onde não existem.

---

## Estrutura de pastas

```
src/          código fonte
tests/        testes
scripts/      utilitários e automações
skills/       procedimentos reutilizáveis para tarefas recorrentes
docs/
  premissas.md       por que o projeto existe, para quem, o que é sucesso
  arquitetura.md     como funciona hoje: fluxo, endpoints, contratos
  ai-rules.md        regras de geração de conteúdo pela IA
  roadmap.md         features não construídas
  debito-tecnico.md  defeitos do que existe, com a evidência de cada um
  decisoes/          um ADR por decisão, numerado e imutável
  sessoes/           registros datados de sessões de trabalho
  historico/         planejamento original, congelado
  audit/             dados das rodadas de auditoria
```
