# 0006 — A medida do conhecimento nasce dentro da ferramenta

**Status:** aceita · **Data:** 2026-08-30

## Contexto

Decorre da [0005](0005-anki-fonte-de-material.md): se o Anki não mede domínio,
alguma coisa precisa medir. E os dados do Anki refletem revisões feitas **no
Anki** — o usuário pode responder duzentos exercícios aqui e o deck continua cego
a todos eles.

O autor descreveu o mecanismo: detectar o erro, exercitar em cima do erro,
registrar o resultado, *"fazendo assim com que tenhamos cada vez mais precisão
sobre o quanto o usuário sabe sobre determinado conceito"*.

## Decisão

A medida do que o usuário sabe é construída **dentro da ferramenta**, a partir do
registro de evidência das próprias interações. Precisão é propriedade acumulada,
não estimativa feita de uma vez.

## Consequências

- Duas perguntas que pareciam projetos separados passam a ser a mesma tabela com
  consultas diferentes: *"o que o usuário sabe do conceito X"* (seleção) e *"a
  ferramenta está ajudando?"* (impacto). A segunda barateia de "instrumentação
  nova" para "um `SELECT` diferente".
- Exige persistência — ver [0012](0012-memoria-em-sqlite.md).
- Cria um problema de partida a frio: no primeiro dia não há evidência nenhuma. É
  o que a semente de `lapses` da [0005](0005-anki-fonte-de-material.md) cobre.
- **Rejeitada explicitamente:** sessão de calibração inicial. É o ritual dos apps
  de trilha que o projeto critica, e mede no vazio, antes de qualquer variação ter
  sido apresentada.
