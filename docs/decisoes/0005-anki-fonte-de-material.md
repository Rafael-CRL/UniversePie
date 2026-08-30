# 0005 — Anki é fonte de material, não de medida de domínio

**Status:** aceita · **Data:** 2026-08-30
**Substitui:** `historico/planejamento-geral-2.md`, seção "Rastreamento de
Conhecimento", que atribuía ao AnkiConnect o papel de leitura do estado de
aprendizado do usuário.

## Contexto

O AnkiConnect devolve o card inteiro: `interval`, `factor`, `lapses`, `reps`,
`queue`, `due`. A tentação óbvia é usar maturidade como proxy de domínio —
priorizar o que está "verde", ou o contrário.

O autor rejeitou essa leitura com um argumento que se sustenta: um card pode ter
ficado maduro porque, no meio do caminho, o usuário teve input externo relevante e
já viu as variações daquele conceito. Exercitá-lo é tedioso. E tédio por má
estimativa do que o usuário sabe é exatamente o antipadrão que originou o projeto.

Nas palavras dele: *"a premissa de 'card velho melhor para se estudar' é básica
demais."*

## Decisão

O Anki é **fonte de material**: as sentenças, as expressões, o vocabulário que o
usuário minerou. Não é fonte de medida de domínio.

Uma exceção estreita, e só uma: **`lapses` mede tropeço**, não maturidade. Alto
número de lapses é sinal legítimo de fricção e serve como **semente inicial** de
onde começar, enquanto não houver dado próprio. É descartável assim que a
ferramenta acumular evidência sua — ver [0006](0006-medida-nasce-na-ferramenta.md).

`interval` e `factor` não são usados como proxy de conhecimento.

**O que fazer com um card de `lapses` alto.** Reforçar o sentido base — é "n", não
"n+1". Um card em que o usuário tropeça repetidamente é um card cujo sentido base
ele ainda não segura; apresentar variações dele seria mostrar o "+1" antes de o
"n" existir, que é o mesmo defeito de calibração que o projeto existe para evitar,
só que na direção oposta. A expressão só entra na rotação de variação depois de
estabilizar. Sem essa regra a ambiguidade se propaga para a implementação.

## Consequências

- Resolve o débito técnico nº 1, mas **muda a justificativa dele**: não é
  "priorizar card maduro", é "ler `lapses` como fricção".
- Torna o Anki substituível como fonte sem que o sistema perca a medida do
  usuário. Reduz muito — não elimina — a necessidade de FSRS próprio.
- O sistema nunca escreve no deck do Anki. Ver [0012](0012-memoria-em-sqlite.md).

## Ponto de atenção

O autor sinalizou que este tópico pode precisar de mais trabalho para uma resposta
mais precisa. A decisão é acionável como está; se surgir dúvida durante o
desenvolvimento, ela deve ser tratada aqui e não contornada em outro lugar.
