# 0010 — Lista de conceitos fechada, versionada, derivada do deck

**Status:** aceita — **sessão dedicada recomendada antes de implementar**
**Data:** 2026-08-30

## Contexto

A [0009](0009-unidade-de-conhecimento.md) exige um vocabulário controlado. Restam
três perguntas: quem escreve a lista, ela pode crescer, e o que acontece quando
cresce.

**Custo, medido.** O pool real tem 166 caracteres por card em média (~47 tokens).
Uma geração medida gastou 1267 tokens de prompt para 15 cards
(`audit/history.jsonl`). Classificar 2000 cards em lotes de 50 dá ~40 chamadas,
~110k tokens de entrada e ~24k de saída: cerca de 20 minutos no tier gratuito mais
apertado, e gratuito no Ollama. O custo não é o token.

## Decisão

**Fechada.** O classificador escolhe de um conjunto fixo. É o que torna agregação
possível: trilha exige chave estável, e barra de progresso sobre rótulo livre é
barra de progresso sobre areia.

**Derivada do próprio deck.** A lista sai de classificar o material real e ver
quais conceitos de fato aparecem — não de copiar uma grade CEFR. Copiar a grade
devolveria a trilha genérica que o projeto critica.

**Versionada e capaz de crescer.** Palavras do autor: *"podem surgir novos
conceitos ou possibilidades de variações que são importantes ou pertinentes; esses
foram o que pensei no momento da criação, mas provavelmente existe outras nuances
e detalhes importantes."* Uma lista permanentemente congelada descartaria em
silêncio toda variação que o deck contém e a lista não previu.

**Cada classificação grava a versão da lista que a produziu.**

## Consequências

O versionamento não é burocracia — é o que impede a trilha de mentir depois que a
lista cresce. Concretamente: se a v1 não inclui "modal no passado" e 537 cards são
classificados sob ela, acrescentar o tipo na v2 não corrige o passado. Aqueles 537
nunca foram avaliados contra o tipo novo; alguns pertencem a ele e foram empurrados
para o rótulo vizinho ou para "outro". Uma trilha que então mostre "modal no
passado: 3 exercícios" está errada — não porque só existam 3, mas porque 537 cards
nunca entraram na conta.

Com a versão gravada, o sistema sabe dizer *"estes foram classificados sob a v1,
que não conhecia este tipo"* e ou reclassifica só eles, ou não apresenta o número
como se fosse completo. Custo: uma coluna.

Outras consequências:

- A classificação é **job incremental**, não script de passada única: card novo
  minerado precisa ser classificado, e a [restrição de escala](../premissas.md)
  exige que seja retomável.
- Auditar 2000 classificações à mão é impossível; a lista fechada permite auditar
  por amostra e medir concordância. Lista aberta não permitiria nem isso.

## Sessão dedicada

Esta decisão sustenta a trilha inteira e foi tomada em nível de visão geral.
Recomenda-se `/grill-me` ou planejamento dedicado antes da implementação —
registrado a pedido do autor.

A sessão precisa cobrir dois pontos que esta decisão levanta e não resolve:
**como auditar a classificação por amostra** (medir concordância contra que
gabarito?) e **como reclassificar** quando ela estiver errada. Classificação ruim
na ingestão corrompe a base de evidência desde a origem, e a gravação da versão da
lista só resolve o caso de a lista ter crescido — não o de a IA ter errado.
