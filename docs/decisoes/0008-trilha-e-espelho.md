# 0008 — A trilha é espelho descritivo, não prescrição

**Status:** aceita · **Data:** 2026-08-30

## Contexto

O projeto nasceu de uma crítica a aplicativos com trilha de aprendizado. E, ao
mesmo tempo, o autor quer ver progresso por conceito. É preciso nomear a diferença,
ou o projeto reconstrói o defeito que o originou.

Palavras do autor, sem ambiguidade: *"a trilha que quero não é a trilha que
critico. Não considere isso em hipótese alguma."*

## Decisão

A trilha é **espelho descritivo**: mostra onde o usuário está, nunca dita ordem
nem obriga sequência. Sobre ela:

- **Treino sob demanda** — o usuário pede ("quero treinar past perfect agora").
- **Sugestão dispensável** — o sistema pode sinalizar um conceito que merece
  revisão, e a sugestão pode ser ignorada sem consequência.

## Consequências

O que separa isto do que o projeto critica não é a existência da trilha — é **quem
escolhe**. O pecado dos apps criticados é a ordem compulsória apoiada numa
estimativa ruim do nível do usuário.

Daí uma propriedade que vale registrar: **neste desenho o sistema pode errar sobre
o usuário sem custo**, porque ele não é obrigado a seguir. No desenho prescritivo,
todo erro de estimativa vira tédio — que é o defeito original.

Sugestão automática é permitida; sugestão que não se pode ignorar é prescrição.
