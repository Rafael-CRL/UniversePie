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

## Escopo Mínimo (MVP)

### Sistema de Cards Inteligente

**Input:**

- Palavra, expressão ou frase colada pelo usuário
- Arquivo importado (PDF, texto, artigo)
- Integração com fluxo do MPV/mpvacious
- Extensão de navegador para captura direta em qualquer site

**Processamento via IA:**

- Identifica o conceito central
- Captura nuances não óbvias
- Gera múltiplos exemplos em contextos diferentes (quantidade configurável)
- Detecta formas mais comuns ou naturais de dizer o mesmo
- Identifica sinônimos relevantes
- Identifica falsos cognatos e interferências do português quando pertinente

**Staged Area:**

- Conteúdo capturado não vira card automaticamente
- Fica em fila de revisão onde o usuário decide o que processa e o que descarta

**Output:**

- Cards padronizados com texto
- Áudio opcional (TTS)
- Flag de revisão no primeiro exibição
- Indicação de fonte
- Tags automáticas quando possível; opcionais nos demais casos

---

## Input — Detalhamento

### Texto Web (via extensão de navegador)

- Usuário seleciona texto em qualquer página e envia ao sistema com um clique
- Extensão captura o texto selecionado
- Metadados opcionais e configuráveis pelo usuário: URL, título da página, domínio
- Útil para contexto e tag automática — ex: conteúdo do Reddit pode ser taggeado como "informal/coloquial", artigo técnico como "tecnologia"
- Captura de metadados pode ser ligada ou desligada pelo usuário

### Vídeo Web

- Integração com YouTube via extensão — captura legenda em reprodução
- Mining direto para o sistema sem baixar o vídeo
- Streaming (Netflix, HBO) — apenas se houver solução simples existente; não é prioridade

### Local

- MPV/mpvacious — fluxo já existente, sistema recebe o card e enriquece o back
- PDF, texto, artigo importado diretamente

---

## Rastreamento de Conhecimento

O sistema precisa saber o que o usuário domina para gerar exemplos relevantes e não repetir o que já foi consolidado. Duas abordagens possíveis, não excludentes:

- **Integração com Anki via AnkiConnect** — lê o histórico de revisões do usuário
- **FSRS próprio** — o sistema implementa o algoritmo internamente

Qual abordagem faz mais sentido será definido durante o desenvolvimento. O importante é que o sistema tenha acesso ao estado de aprendizado do usuário de alguma forma.

---

## Features Planejadas (pós-MVP)

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
- Filtros por tag para sessões temáticas

### Estatísticas de Aprendizado

- Reflexo real do progresso
- Conceitos dominados saem da rotação

### Exercícios de Escrita (futuro)

- Baseados no vocabulário e expressões já adquiridos

---

## Princípios do Sistema

- **Âncoras:** conteúdo já estudado serve como base
- **n+1 natural:** exemplos gerados podem introduzir vocabulário levemente acima do nível atual
- **Sem repetição burra:** conceitos dominados saem da rotação
- **Fricção mínima:** o usuário faz o input, o sistema faz o resto
- **Staged antes de salvar:** nada vira card sem passar pela revisão do usuário
- **Nuances explícitas:** o sistema não deixa passar o que o aprendizado tradicional ignora
- **Fonte rastreada:** todo card tem origem registrada para contexto e filtragem
- **Configurável:** metadados, áudio, quantidade de exemplos — o usuário decide o que ativa

---

## Stack (a definir em detalhe)

- **Backend:** Python + FastAPI
- **Frontend:** a definir
- **Banco de dados:** SQLite (uso pessoal inicial)
- **IA:** Claude API
- **TTS:** edge-tts ou equivalente
- **Deploy:** Docker Compose
- **Extensão:** Chrome Extension (Manifest V3)

---

## Observações

- Sistema inicialmente pessoal, com possibilidade de expansão futura
- Foco inicial em inglês, arquitetura deve permitir extensão para outros idiomas
- Pode ser usado como complemento do Anki ou como substituto — escolha do usuário