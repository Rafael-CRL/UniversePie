# Project Darksideofthemoon

## Visão Geral

Ferramenta web local para aprendizado de idiomas com foco inicial em inglês. O sistema parte do conhecimento já adquirido pelo usuário e o aprofunda de forma automatizada, reduzindo a fricção mental do processo manual de criação de cards e captura de nuances.

Não é necessariamente um substituto do Anki — pode ser usado como complemento via integração, ou como sistema independente completo. Essa escolha é do usuário.

---

## Problema que Resolve

O aprendizado por sentence mining exige trabalho manual intenso: encontrar a expressão, buscar o significado, criar o card, adicionar exemplos, inserir áudio. Esse processo se repete para cada nuance de uma mesma expressão.

Além disso, nuances importantes frequentemente se perdem:
- "down the street" não é "descendo a rua"
- "but" em "I wish nothing but the best" não é "mas"
- "settle for" vs "settle on" vs "settle into" têm usos completamente diferentes
- Expressões de textos antigos podem não refletir o uso contemporâneo mais comum

---

## Público-Alvo

O sistema não é voltado para iniciantes absolutos. Parte-se do princípio de que o usuário já possui vocabulário básico — palavras como "have", "house", "go" não são material de card. O foco é em estruturas, expressões idiomáticas, phrasal verbs, nuances contextuais e vocabulário intermediário/avançado.

---

## Escopo Mínimo (MVP)

O objetivo do MVP é validar o core do sistema: **input chega, IA processa, card inteligente sai**. Tudo que não testa isso é adiado.

### Input (MVP)

- **Fase 1:** Texto colado manualmente pelo usuário — suficiente para validar a qualidade de geração da IA
- **Fase 2 (imediata):** Importação do Anki via AnkiConnect — o usuário já possui uma base relevante de cards com front e back. Esse conteúdo pode ser usado para testes mais ricos: geração de quizzes personalizados, exercícios de reforço e validação da filosofia do projeto com dados reais

### Inputs pós-MVP

- PDF ou arquivo de texto importado
- Integração com MPV/mpvacious
- Extensão de navegador
- YouTube via extensão

### Processamento via IA

A IA não é apenas geradora de cards — é a **camada de inteligência que opera sobre o banco de dados**. Ela lê o estado de conhecimento do usuário (cards aprovados, tags, histórico via AnkiConnect) para gerar conteúdo contextualizado e relevante.

- Identifica o conceito central (ou múltiplos, quando o input é uma frase completa)
- Gera múltiplos exemplos em contextos diferentes (quantidade configurável)
- **Considera família de palavras** — exemplos incluem formas derivadas e variações temporais: *settle, settled, settling, settlement*; presente, passado, futuro
- Detecta formas mais comuns ou naturais de dizer o mesmo
- Identifica sinônimos relevantes
- Identifica falsos cognatos e interferências do português quando pertinente
- Âncora no conhecimento existente — o que o usuário já domina serve como base; a IA tem consciência disso e usa como referência, sem estar presa a introduzir exatamente um conceito novo por vez
- **Nuances são condicionais** — só aparecem quando genuinamente necessárias (ex: "but" em "I wish nothing but the best" não é "mas"). Se o usuário simplesmente não sabe uma palavra isolada, não há nuance a capturar — o sistema não força nuances onde elas não existem

### Como o input se transforma em aprendizado — exemplos concretos

O input do usuário se torna ferramenta de aprendizado sob diferentes óticas:

**Frase com expressão desconhecida:**
Input: *"the only thing to do in your position when it comes to me"*
Back do card: `when it comes to` = quando se trata de, no que diz respeito a — *"when it comes to money"*, *"when it comes to me"*. Ou, em vez de tradução, o meaning em inglês, dependendo da configuração do usuário.

**Estrutura extraível:**
Input: *"would I put my life on hold for a child I didn't want? Yes, I would."*
Conceito: `put [something] on hold` → outros exemplos, variações, quiz.

**Múltiplos conceitos em uma frase:**
Input: *"I've already reached out to the McBeal camp."*
Conceito 1: `reach out to` → contact someone, especially to discuss something or ask for help. *"I reached out to her yesterday"*, *"The company reached out to its customers."*
Conceito 2: `camp` → a person's group, team, or inner circle. *"The senator's camp denied the allegations"*, *"We're waiting for a response from their camp."*

### Staged Area

- Conteúdo capturado não vira card automaticamente
- Fica em fila de revisão onde o usuário decide o que processa e o que descarta

### Output

- Cards padronizados com texto
- Áudio opcional (TTS)
- Flag de revisão no primeiro exibição
- Indicação de fonte
- Tags automáticas quando possível; opcionais nos demais casos

---

## Princípios de Geração de Conteúdo (Regras da IA)

Estas são as diretrizes não rígidas que guiarão o prompt do sistema para a geração de cards:

- **Tradução:** Fiel ao tom, sem eufemismos, natural em português. O tom emocional e sensorial deve ser capturado (ex: *itching* não é apenas "ansioso", carrega uma sensação física de urgência).
- **Idioma do back:** Preferir inglês quando o significado é direto e claro. Português é reservado para expressões idiomáticas, falsos cognatos, interferências do idioma nativo ou termos genuinamente opacos.
- **Sem redundância:** Se o significado for óbvio pelo contexto ou pela tradução direta, a explicação extra deve ser cortada.
- **Termos não óbvios:** Explicar somente o que realmente precisa de explicação.
- **Estrutura/padrão:** Quando a expressão faz parte de um padrão maior ou função discursiva, isso deve ser mostrado (ex: *"all well and good"* → frequentemente introduz uma objeção).
- **Exemplos paralelos:** Fornecer de 1 a 2 exemplos em contextos diferentes quando a estrutura gerada for de uso comum.
- **Gíria/registro:** Identificar claramente o registro da expressão (informal, vulgar, técnico, sarcástico).
- **Origem/Etmologia:** Mencionar apenas quando for genuinamente útil para fixar o contexto ou significado (ex: *top-shelf*, *gold standard*).
- **Phrasal verbs e Expressões Idiomáticas:** Destacar explicitamente quando o significado não for composicional, ou seja, quando a soma das palavras não deduz o significado (ex: *out of the blue*, *get off*, *come Monday*).
- **Falsos cognatos e Interferências do português:** Sinalizar quando a tradução literal induz ao erro estrutural (ex: *down the street* ≠ descendo a rua).
- **Traduções com nuance:** Diferenciar explicitamente expressões que parecem sinônimos em português mas têm usos distintos em inglês (ex: *come on* ≠ *let's go*).

---

## Gramática Emergente

O sistema não é um módulo de gramática. É um sistema de input que, com o tempo, acumula volume suficiente para revelar padrões.

Quando o banco de dados do usuário tiver conteúdo suficiente, o sistema pode:
- Identificar estruturas gramaticais recorrentes no material estudado
- Gerar quizzes sobre tempos verbais usando vocabulário que o usuário já conhece
- Sugerir "dar nome aos bois" — explicar a estrutura que o usuário já usa intuitivamente

Isso emerge do uso, não é ensinado desde o início. A gramática aparece como consequência do volume de input, não como ponto de partida.

---

## Rastreamento de Conhecimento

O sistema precisa saber o que o usuário domina para gerar exemplos relevantes e não repetir o que já foi consolidado.

**Decisão para o MVP: AnkiConnect.**

O AnkiConnect cumpre dois papéis distintos no sistema — é importante não misturar as responsabilidades:

1. **Importação de base existente** — o usuário que já tem histórico no Anki pode importar seus cards como ponto de partida, sem começar do zero
2. **Leitura do estado de aprendizado** — o sistema consulta o histórico de revisões para saber o que o usuário domina, o que está consolidado e o que ainda é frágil

FSRS próprio é uma possibilidade futura, para usuários que não usam Anki.

---

## Features Planejadas (pós-MVP)

### Extensão de Navegador
- Captura de texto selecionado em qualquer site com um clique
- Metadados opcionais e configuráveis

### Quiz Contextualizado
- Gerado a partir do banco de conhecimento existente do usuário
- Baseado no que o usuário menos domina
- Múltiplos formatos: múltipla escolha, input livre
- Sem mecânicas predatórias

### Detecção de Lacunas
- Sistema identifica padrões de erro recorrentes
- Gera automaticamente mais exemplos do conceito que o usuário erra com frequência

### Tags por Área e Contexto
- Culinária, tecnologia, finanças, ambiente de trabalho, gírias, jargões
- Tags automáticas via IA quando possível
- Tags são o **índice do conhecimento acumulado** — não são categorias passivas. São o mecanismo pelo qual o usuário e a IA filtram e navegam o banco de dados
- "Quero estudar vocabulário tech" → IA lê o que existe com essa tag, cruza com o histórico AnkiConnect e gera exercícios, quizzes ou cards dentro desse recorte

### Estatísticas de Aprendizado
- Conceitos dominados saem da rotação

### Exercícios de Escrita
- Baseados no vocabulário e expressões já adquiridos

---

## Princípios do Sistema

- **Âncoras:** conteúdo já estudado serve como base
- **Consciência do nível:** a IA conhece o estado de aprendizado do usuário e usa isso como âncora — o quanto de novidade introduzir em cada geração é julgamento da IA, não uma regra fixa
- **Família de palavras:** exemplos cobrem formas derivadas e variações temporais
- **Fricção mínima:** o usuário faz o input, o sistema faz o resto
- **Staged antes de salvar:** nada vira card sem passar pela revisão do usuário
- **Nuances condicionais:** o sistema captura nuances não óbvias quando elas existem — não força nuances onde não há
- **Fonte rastreada:** todo card tem origem registrada
- **Gramática emergente:** padrões gramaticais surgem do volume de input, não são ensinados
- **Configurável:** metadados, áudio, quantidade de exemplos — o usuário decide o que ativa

---

## Stack

- **Backend:** Python + FastAPI
- **Frontend:** Svelte + Vite (SPA estático, servido pelo próprio FastAPI no MVP para simplificar o Docker)
- **Banco de dados:** SQLite (uso pessoal inicial)
- **IA (MVP):** A definir entre Antigravity CLI/SDK e chamada direta à API (Gemini, Claude). Depende do acesso disponível no plano atual. Arquitetura deve abstrair o provedor para permitir troca futuramente
- **TTS:** edge-tts ou equivalente
- **Deploy:** Docker Compose (uso pessoal) / Tauri como possibilidade futura para distribuição desktop multiplataforma
- **Extensão:** Chrome Extension (Manifest V3) — pós-MVP

---

## Observações

- Sistema inicialmente pessoal, com possibilidade de expansão futura
- Foco inicial em inglês, arquitetura deve permitir extensão para outros idiomas
- Pode ser usado como complemento do Anki ou como substituto — escolha do usuário
- Distribuição futura como app nativo (Linux/Windows/Mac) é um cenário cogitado — Tauri é a opção mais promissora para isso
