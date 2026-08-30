# 0007 — Autorrelato é direcionamento, não medida

**Status:** aceita · **Data:** 2026-08-30

## Contexto

O autor propôs um botão no exercício para o usuário informar que aquilo está fácil
demais, difícil, ou que já conhece as variações. É barato, funciona no primeiro
dia e não depende de histórico.

Mas é o sinal que a literatura de aprendizagem mais desmente: a sensação de
facilidade é justamente o que falha na hora da produção ativa. Tratar "achei
fácil" como "eu sei" reintroduz o defeito dos apps de trilha — estimativa ruim do
nível — com o próprio usuário no papel do algoritmo ruim.

## Decisão

Três sinais, com precedência explícita:

1. **Texto espontâneo do usuário** — produção ativa real, não solicitada. O mais
   forte. Ainda não implementado; ver [0011](0011-origem-da-evidencia.md).
2. **Desempenho registrado** — acerto e erro nos exercícios. Vence o autorrelato
   em caso de conflito.
3. **Autorrelato** — lido como **comando de direcionamento**, não como medida.
   "Fácil demais" significa *"não me mostre isto, escale"*, não *"eu sei isto"*.

Declaração espontânea de fraqueza pelo próprio usuário ("sou ruim em tense") cai
na mesma categoria: direciona por onde começar, não mede conhecimento.

## Consequências

- Resolve o tédio no primeiro dia sem esperar histórico, e sem corromper a medida.
- O botão é feature de roadmap; a regra de leitura vale desde já para qualquer
  mecanismo de sinalização que seja construído.

## Ponto de atenção

O autor registrou que a combinação dos três sinais pode ser aprimorada e que o
desenho do loop pede planejamento próprio. Esta decisão fixa a **precedência**,
não a fórmula.
