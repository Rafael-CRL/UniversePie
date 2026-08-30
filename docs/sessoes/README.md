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

**`PLANO-qualidade-do-output.md`** — corrigir os prompts e baixar os defeitos
medidos. É o que a branch `feat/card-quality-audit` existe para fazer.

## Linha de base vigente

**`2026-08-30-linha-de-base-g1.md`** — 120 exercícios, 4 modelos, **pool ideal
congelado** (`audit/pool-exemplo.json`). É contra ela que as correções de prompt
devem ser comparadas:

```
--compare docs/audit/base-g1-gemini.json docs/audit/base-g1-groq.json           docs/audit/base-g1-qwen3.json docs/audit/base-g1-gemma4.json
```

`2026-08-29-auditoria.md` continua sendo evidência permanente, mas **não serve
de comparação**: sorteou pool a cada rodada, e é anterior ao campo
`source_expression`. É a referência do grupo 2 (material real), não do grupo 1.

Atualizar esta linha quando houver medição nova.
