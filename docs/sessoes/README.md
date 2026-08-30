# Sessões

Registros datados de sessões de trabalho. Dois tipos, marcados no topo de cada
arquivo:

- **evidência** — contém medição que não dá para regenerar sem gastar cota e
  tempo de novo (números de auditoria, custo por modelo, taxas por provedor).
  Permanente.
- **registro** — narra o que foi feito. Decai assim que o conteúdo durável migra
  para um documento mantido (`decisoes/`, `debito-tecnico.md`, `premissas.md`,
  `roadmap.md`). Marcado como migrado, não apagado: apagar perde o rastro,
  manter sem marca faz alguém agir sobre coisa vencida.

- **plano** — escrito *antes* da sessão, com objetivo e definição de pronto.
  Consumido pela sessão que ele descreve e substituído pelo registro dela. É o
  único tipo que deve ser apagado, porque cumpriu a função.

A disciplina é a **migração**, não a marcação. Se o que a sessão produziu ainda
não aterrissou num documento mantido, ela continua sustentando peso e não pode
ser marcada como migrada.

## Próxima sessão

**Sem plano escrito.** O que estava em `PLANO-qualidade-do-output.md` foi
executado e o arquivo apagado, como o próprio tipo "plano" manda. As três
primeiras coisas a fazer estão em "Pendências abertas" de
`2026-08-30-correcao-de-prompts.md`, e a primeira é a linha de base final do
Gemini, que ficou bloqueada por cota.

## Linha de base vigente

**`2026-08-30-correcao-de-prompts.md`** — prompts corrigidos, pool ideal
congelado (`audit/pool-exemplo.json`), 90 exercícios em três modelos. É contra
ela que a próxima mudança de prompt deve ser comparada:

```
--compare docs/audit/v2-final-gemma4.json docs/audit/v2-final-qwen3.json           docs/audit/v2-final-groq.json
```

**Falta o Gemini nesta linha** — cota diária esgotada em 2026-08-30. O par
antes/depois dele existe por item (`base-g1-gemini` contra `v2-item9-gemini`,
`v2-item10-gemini` e `v2-item10b-gemini`), mas a rodada final com todos os
prompts corrigidos não foi feita.

`2026-08-30-linha-de-base-g1.md` continua sendo evidência permanente e é o
**antes** de todos os pares desta sessão. Deixou de ser a linha de comparação
vigente, porque os prompts que a produziram não existem mais.

`2026-08-29-auditoria.md` continua evidência permanente, mas **não serve de
comparação**: sorteou pool a cada rodada, e é anterior ao campo
`source_expression`. É a referência do grupo 2 (material real), não do grupo 1.

Atualizar esta linha quando houver medição nova.
