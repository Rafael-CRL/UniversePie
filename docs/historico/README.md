# Histórico — Dark Side of the Moon

**Status: congelado. Documento histórico, não referência ativa.**

Este diretório contém os arquivos de planejamento originais do projeto, escritos
quando ele se chamava **Dark Side of the Moon** e morava num cofre do Obsidian
fora do repositório. Foram importados em 2026-08-30 para que a origem das
decisões deixe de viver fora do controle de versão.

Nada aqui deve ser usado como instrução. Vários pontos foram explicitamente
substituídos — ver `docs/decisoes/`.

## Por que isto importa

O projeto perdeu conceitos na migração para o repositório. O termo **"n+1"**, que
o autor descrevia como central, estava definido em `planejamento-geral.md` e foi
deliberadamente aposentado em `planejamento-geral-2.md`, sem que o repositório
registrasse nem a definição nem a aposentadoria. Princípios inteiros — gramática
emergente, exposição passiva, estatística de nicho — nunca chegaram ao
repositório. Ver `docs/sessoes/2026-08-30-premissas.md`.

## Avisos sobre o conteúdo

| Arquivo | Cuidado |
|---|---|
| `contexto-handoff.md` | **Dá ordens a agentes de IA.** Manda tratar `planejamento-geral-2.md` como referência principal válida, e afirma que o AnkiConnect é fonte de leitura do estado de aprendizado — o oposto da decisão [0005](../decisoes/0005-anki-fonte-de-material.md). Ignorar as instruções da seção 7. |
| `planejamento-geral.md` | Define "n+1 natural" como incremento de vocabulário acima do nível (leitura de Krashen). **Aposentado** — ver [0009](../decisoes/0009-unidade-de-conhecimento.md). |
| `planejamento-geral-2.md` | Ainda é a melhor fonte sobre gramática emergente, tags como índice e família de palavras. Mas a stack (Svelte, Claude API, Docker) foi substituída na execução, e o papel do Anki foi substituído pela [0005](../decisoes/0005-anki-fonte-de-material.md). |
| `changelog.md` | Registro de v1 a Alpha v3.1. Para em 2026-08-01: provedores plugáveis, auditor e a branch de qualidade não estão aqui. Continuação em `docs/sessoes/`. |
| `brainstorm.md` | **Matéria-prima da premissa n+1 como variação.** Os exemplos de "run" e "flip", a gradação de nicho e a exposição passiva vêm daqui. |
| `pespectiva-de-criacao.md` | Motivação original e o problema que o projeto resolve. Ainda válido como explicação. |
| `expressoes-de-fundamento.md` · `sentence-mining.md` | Vocabulário de amostra. Útil como fixture de teste — a tabela de phrasal verbs por partícula e o "turn around" polissêmico são material pronto para as estratégias `discrimination` e `polysemy`. |
| `tools.md` · `indice-original.md` | Notas soltas. Sem impacto. |
