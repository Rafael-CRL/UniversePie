# 0011 — O registro de evidência prevê a origem desde o início

**Status:** aceita · **Data:** 2026-08-30

## Contexto

Além do exercício, existem outras origens possíveis de evidência sobre o que o
usuário sabe — em particular, texto que ele escreveu por conta própria (artigo,
conversa com IA) e que o sistema poderia analisar. É feature de roadmap, não de
agora. Mas o formato do registro é decisão de hoje.

## Decisão

O registro de evidência prevê o campo de origem — `exercise`, `writing`,
`self_report` — desde o primeiro dia, mesmo com apenas uma origem implementada.

## Consequências

- Custa um campo agora; é retrofit caro depois, porque mudaria a chave de tudo que
  já foi gravado.
- Formaliza a precedência da [0007](0007-autorrelato-e-comando.md): texto
  espontâneo é o sinal mais forte, porque é produção ativa real e sem aviso;
  exercício é desempenho sob condição artificial; autorrelato não é medida.
- Registro completo: `(expressão, conceito, tipo de variação, versão da lista,
  origem, resultado, data)`.

## Tensão registrada, não resolvida

Duas features futuras usam texto escrito e são incompatíveis entre si no desenho:

- **Análise de texto próprio** — voluntária. O autor foi explícito: *"não é algo
  que o software deve solicitar explicitamente, mas deixar claro que isso pode
  ajudar o entendimento melhor do sistema."*
- **Avaliação por redação** — o sistema **pede** o texto, como diagnóstico.

A segunda inverte a restrição da primeira, e esbarra também na
[0004](0004-string-matching-no-cloze.md). Não precisa ser resolvida agora; precisa
estar escrita para que a sessão que as planejar comece por aqui.
