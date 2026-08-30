# Changelog - Dark Side of the Moon (Alpha)

Este documento registra todas as decisões, implementações e configurações realizadas durante o desenvolvimento da versão Alpha do projeto.

## [Alpha v1] - Prova de Conceito Inicial

### Planejamento e Contexto
- Leitura dos arquivos de fundação (`Planejamento Geral.md`, `PlanejamentoGeral2.md`, `CONTEXTO_HANDOFF.md`).
- Definição do escopo do Alpha: Validar exclusivamente a capacidade da IA de extrair conceitos relevantes de cards do Anki (deck `English_Series`) e gerar quizzes de múltipla escolha com alta qualidade, testando o conceito em contextos variados.
- Funcionalidades complexas (Staged Area, TTS, Tags, FSRS) foram explicitamente isoladas e adiadas para fases futuras.

### Implementação
- **Backend (`main.py`)**: Criado com FastAPI.
  - Integração local com o AnkiConnect (porta 8765) via `httpx`.
  - Integração com a API do Gemini via SDK oficial `google-genai` (modelo `gemini-2.5-flash`).
  - Geração de endpoint `/api/quiz` para buscar um card aleatório, processá-lo na IA e devolver um JSON estruturado (Pydantic).
- **Frontend (`index.html`)**: HTML/JS puro (sem frameworks ou build steps) servido pela raiz da API. Implementou o fluxo básico: botão para gerar quiz, exibição da pergunta/opções, e feedback de acerto/erro.
- **Dependências (`requirements.txt`)**: Definidas de forma minimalista (`fastapi`, `uvicorn`, `httpx`, `google-genai`).

### Correções (Code Review)
- Implementado cache para os IDs dos cards do Anki para evitar chamadas redundantes de `findCards` a cada request.
- Adicionada função `strip_html()` para higienizar o conteúdo extraído do Anki (remoção de tags HTML, referências de áudio `[sound:...]` e entidades) antes do envio ao prompt da IA.
- Melhoria na robustez: Adicionados validadores semânticos no Pydantic para garantir que a IA retorne exatamente 4 opções e um índice de resposta válido (0-3).
- Remoção de comentários inválidos no prompt JSON que poderiam causar alucinações no modelo.

## [Infraestrutura e Configuração]

- Análise de viabilidade financeira: Confirmado o uso do Free Tier do Google AI Studio para o modelo `gemini-2.5-flash`.
- Resolução de problemas de ambiente Python local (ausência de `python3.14-venv`).
- **Instalação de Pacotes**: Devido às restrições locais de ambiente virtual, os pacotes foram instalados globalmente com flag de bypass:
  `pip install fastapi uvicorn httpx google-genai --break-system-packages`
- **Resolução de Conflitos de Porta**:
  - Tentativa inicial na porta `8000` falhou (`Address already in use`).
  - Migração para a porta `8080`.
  - A pedido, migração final para porta incomum `14567` para evitar conflitos com outros serviços locais de desenvolvimento.

## [Alpha v2] - UX e Refatoração Assíncrona

### Planejamento (`alpha_v2_plan.md`)
- Proposto plano de 7 melhorias de qualidade de vida para acelerar o ciclo de teste e validação da IA, focando em velocidade, redução de fadiga visual e feedback claro.

### Implementação
- **Backend Refatorado (Async)**:
  - Transição de código síncrono para operações assíncronas com `httpx.AsyncClient` e endpoint `async def`.
  - Nova rota `/api/quiz-session` recebendo parâmetro `n` (quantidade de quizzes).
  - Otimização do AnkiConnect: Chamada em batch via `cardsInfo` enviando a lista de IDs de uma vez.
  - Geração Paralela: Uso de `asyncio.gather` para despachar `n` requisições simultâneas para a API do Gemini, reduzindo drasticamente o tempo de espera da sessão.
- **Frontend Reformulado**:
  - **Aparência**: Adotado Dark Mode com paleta de cores coesa (fundo escuro, detalhes em roxo/verde/vermelho) para redução de fadiga visual, utilizando a tipografia `Inter` (Google Fonts).
  - **Sessão de Quizzes**: Implementado fluxo contínuo onde o usuário responde `n` perguntas consecutivamente.
  - **Interface**: Inserida barra de progresso.
  - **Debug de IA**: Adicionado elemento colapsável (details/summary) após responder cada quiz para visualizar os conteúdos Front/Back originais do card do Anki, facilitando a validação humana da eficácia da IA.
  - **Resumo de Sessão**: Tela final exibindo pontuação geral, agrupando conceitos acertados (colapsados) e destacando os conceitos errados juntamente com suas explicações.
  - **Usabilidade**: Mapeados atalhos de teclado (`1-4` para opções, `Enter/Space` para avançar, `N` para nova sessão) visando fluidez.

## [Alpha v3] - Sofisticação da Camada de Inteligência e Quizzes

### Planejamento e Diagnóstico
- Identificação de falha estrutural nos quizzes da Alpha v2: a extração unitária (1 card → 1 quiz) gerava apenas testes de reconhecimento passivo ("flashcards disfarçados").
- Decisão de elevar a sofisticação baseada na filosofia de fundação: focar na discriminação entre conceitos similares, na produção ativa da língua e no mapeamento explícito de interferências linguísticas do português.

### Implementação
- **Backend (`main.py`)**:
  - Refatoração do fluxo de requisição: transição de requisições isoladas por card para envio de um **pool de cards em lote** (composto por `n * 3` cards randômicos) em uma única chamada à API do Gemini, provendo área de superfície para correlações.
  - Reestruturação agressiva do Prompt do Gemini, exigindo a rotatividade de 5 estratégias de avaliação:
    1. **Discrimination**: escolha forçada entre termos próximos (ex: settle into vs settle for).
    2. **Production**: descrição de intenção comunicacional testando a expressão correta (saída ativa em vez de leitura passiva).
    3. **Interference**: mapeamento proativo de erros lógicos usando traduções literais para português (L1) como _distratores_ estruturais.
    4. **Polysemy**: teste de discernimento contextual de múltiplos significados da mesma raiz.
    5. **Contextual**: teste de implicações pragmáticas e registro (sarcasmo, formalidade, intenção).
  - Atualização do contrato Pydantic para processar e validar o novo campo `quiz_type` e acomodar um vetor de múltiplos `source_cards` por questão.
  - Ajuste de estabilidade: aumento do timeout HTTP do `httpx` de 15s para 30s.
- **Frontend (`index.html`)**:
  - Expansão visual: implementação de tags/badges dinâmicas categorizando em tempo real o tipo de raciocínio lógico demandado (`quiz_type`).
  - Expansão de _debug_: a área colapsável ("Ver card original") foi refatorada para iterar sobre múltiplos cards-fonte que porventura tenham embasado a criação transversal de um quiz específico.

## [Alpha v3.1] - Cloze Production e Exercício de Produção Ativa

### Princípios e Raciocínio que Guiaram Esta Sessão

Esta sessão partiu de uma revisão crítica do estado do projeto: o quiz, mesmo com as 5 estratégias da v3, continuava sendo fundamentalmente um exercício de **reconhecimento** — o usuário seleciona entre opções pré-definidas. Reconhecimento é o nível mais raso de memória. A filosofia do projeto exige que o aprendizado seja testado com "diferentes lentes", e o quiz sozinho não cobre produção ativa.

O diagnóstico levantou três candidatas para o próximo exercício:
1. **Scenario Writing** (produção guiada com escrita livre) — descartado para o alpha por depender de avaliação de texto livre pela IA, cuja confiabilidade é baixa neste estágio. O risco de falsos negativos (respostas válidas marcadas como erradas) comprometeria a experiência.
2. **Register Shifting** (refatoração de diálogo) — descartado por ter conexão fraca com o deck do usuário. Funciona mais como exercício genérico de inglês do que como algo ancorado nos dados reais do Anki.
3. **Cloze Production** (preenchimento sem opções) — escolhido por equilibrar produção ativa com avaliação confiável. A restrição de resposta (uma expressão, não um parágrafo) mantém o espaço de avaliação manejável.

**Transparência sobre fontes**: foi identificado que o deck do Anki contém cards minerados de fontes variadas (séries, filmes, artigos). Algumas expressões são altamente contextuais, nicho ou incomuns no inglês cotidiano. O sistema precisa ser honesto sobre isso em vez de tratar toda expressão como igualmente relevante. Por isso, cada exercício cloze classifica a expressão-alvo em `common`, `moderate` ou `niche`, com uma nota contextual explicando quando a expressão não é de uso corrente.

### Implementação

- **Backend (`main.py`)**:
  - Novos modelos Pydantic: `ClozeItem` (com campos `sentence`, `target_expression`, `acceptable_alternatives`, `hint`, `commonality`, `context_note`, `explanation`, `source_cards`) e `ClozeSession`.
  - Validador para `commonality` restrito a `{"common", "moderate", "niche"}`.
  - Novo prompt builder `build_cloze_prompt()`: instrui o Gemini a gerar exercícios de preenchimento a partir do pool de cards, exigindo honestidade na classificação de frequência e produção de context_notes quando a expressão não é `common`.
  - Novo endpoint `/api/cloze-session?n=` com a mesma lógica de pool (`n * POOL_MULTIPLIER`) e mapeamento de `used_cards` para `source_cards`.
- **Frontend (`index.html`)**:
  - **Seletor de modo**: botões `Quiz | Cloze` na tela inicial, permitindo alternar entre os dois exercícios.
  - **Tela Cloze completa**:
    - Frase com lacuna estilizada (`_____` renderizado como `<span>` com borda tracejada).
    - Campo de texto livre para digitação da resposta.
    - `Show hint` colapsável com dica gerada pela IA.
    - Feedback graduado em 3 níveis após submit:
      - **Correto** (verde): resposta bate com `target_expression`.
      - **Alternativa válida** (azul): resposta bate com uma das `acceptable_alternatives`.
      - **Incorreto** (vermelho): exibe resposta-alvo e alternativas aceitas.
    - Badge de `commonality` (`common`/`moderate`/`niche`) com cores distintas ao lado do conceito.
    - `context_note` visível quando a expressão é `moderate` ou `niche`.
    - Cards-fonte do Anki colapsáveis (mesma estrutura do quiz).
  - **Avaliação client-side**: normalização (lowercase, trim, colapsar espaços) e comparação contra `target_expression` + `acceptable_alternatives`. Sem chamada adicional à API.
  - **Atalhos de teclado**: `Enter` no campo de texto para submit, `Enter` após feedback para avançar.
  - **Tela de resumo unificada**: agora exibe `userAnswer` vs `targetAnswer` nos conceitos errados do modo cloze.
  - Refatoração do JS: estado compartilhado (`exercises`, `currentMode`) entre quiz e cloze, com funções de navegação unificadas (`advanceExercise`, `showSummary`).

### Limitações Conhecidas
- A avaliação do cloze é por string matching normalizado. Respostas semanticamente corretas mas lexicamente diferentes da `target_expression` e das `acceptable_alternatives` pré-geradas serão marcadas como incorretas. Para o alpha, isso é aceitável — o objetivo é testar a qualidade do output da IA, não construir um avaliador perfeito.
- A classificação de `commonality` depende do julgamento do Gemini, que pode ser impreciso. O prompt instrui honestidade, mas não há validação externa.
