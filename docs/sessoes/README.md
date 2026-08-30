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

**`2026-08-29-auditoria.md`** — 118 exercícios, 5 configurações de modelo. É contra
ela que as próximas correções de prompt devem ser comparadas
(`--compare docs/audit/baseline-*.json`). Atualizar esta linha quando houver
medição nova.
