# UniversePie — Premissas

**Última revisão:** 2026-08-30
**Status:** ativo. Este é o documento de explicação do projeto — *por que* ele
existe, para quem, e o que conta como sucesso. Decisões acionáveis moram em
`decisoes/`; features não construídas, em `roadmap.md`; defeitos conhecidos, em
`debito-tecnico.md`.

Este documento foi escrito depois de uma sessão de extração com o autor
(`sessoes/2026-08-30-premissas.md`). O motivo dela, nas palavras dele: havia
dúvidas e inconsistências sobre o entendimento do projeto, e isso estava
prejudicando a qualidade do desenvolvimento e dos testes.

---

## A aposta

Existem detalhes do inglês que quase ninguém ensina de forma direta: os vários
sentidos que uma mesma expressão assume conforme o contexto, as formas derivadas
e os tempos de uma mesma palavra, a mudança de sentido que uma partícula produz,
o registro, a colocação, as armadilhas que a estrutura do português cria.

Esses detalhes normalmente são adquiridos por **milhares de horas de input**. Não
são ensinados; são absorvidos por exposição repetida em contextos variados.

**A aposta do UniversePie é que esse caminho pode ser encurtado se as variações
forem mostradas explicitamente**, ancoradas no que o usuário já estudou.

## "n+1"

O termo é jargão do projeto e a magnitude não é literal.

> O software reforça conceitos que o usuário já tem **e** apresenta variações e
> outras possibilidades de uso desses mesmos conceitos. O incremento é variável —
> pode ser n+1, n+2 ou n+3 conforme o contexto.

O que constitui o "+": polissemia, família de palavras (passado, particípio,
derivados), troca de partícula, registro, colocação, interferência do português e
os conceitos gramaticais presentes nas sentenças mineradas. **Esta relação não é
exaustiva** — ver [0010](decisoes/0010-lista-de-conceitos.md).

Os mecanismos atuais — quiz e cloze — são **substituíveis**. Formas mais precisas
e eficientes de testar estão previstas e não estão descartadas por nada aqui.

### Nota sobre o termo

O nome tem história e ela importa, porque explica por que ninguém o encontrava no
repositório. Ele aparece em `historico/planejamento-geral.md` com outra definição
— "exemplos gerados podem introduzir vocabulário levemente acima do nível atual",
uma leitura de Krashen — e foi **deliberadamente removido** na revisão seguinte,
que o substituiu por "o quanto de novidade introduzir em cada geração é julgamento
da IA, não uma regra fixa".

Ou seja: o incremento fixo já tinha sido rejeitado uma vez, por escrito. O termo
sobreviveu na fala do autor com um significado diferente e mais rico — o que está
definido acima. Mantemos a palavra porque é como o autor pensa o projeto; a
definição é que precisa vir junto dela.

---

## O antipadrão que originou o projeto

Nas palavras do autor:

> Aplicativos com trilha de aprendizado de inglês dificilmente acertam em
> quantificar o quanto o usuário sabe do idioma, então faz ele aprender coisas que
> já sabe, fazendo ser tedioso/irritante/improdutivo.

Disso decorre uma consequência que restringe o desenho inteiro: **heurística
grosseira de "o que estudar" é o defeito, não a solução.** Em particular, a
premissa "card mais antigo é melhor para estudar" foi examinada e rejeitada — um
card maduro pode ter ficado maduro porque o usuário absorveu o conceito por input
externo no meio do caminho, e exercitá-lo é exatamente o tédio que o projeto
existe para evitar. Ver [0005](decisoes/0005-anki-fonte-de-material.md).

---

## Público e objetivo

**Perfil:** quem está saindo do A2 e se encontra em B1/B2. Já tem vocabulário e
não precisa de conceitos básicos — "I have to go" não é material de card. O foco é
estrutura, expressão idiomática, phrasal verb, polissemia e nuance contextual.

**Escopo de uso:** a ferramenta é, hoje, para o autor, que pertence ao público-alvo.

**Validação em primeira pessoa.** O autor pertencer ao público-alvo permite gerar
evidência de qualidade antes de existir base de usuários. Isso não substitui teste
com terceiros — antecipa-o.

**Portão de abertura ao público:** quando houver MVP que demonstre resultado, a
ferramenta é aberta a terceiros para teste mais preciso. Antes disso, não.

**Restrição de escala.** Ainda que o uso hoje seja pessoal, o desenho não pode
depender do tamanho do deck do autor (537 cards). Um usuário com 1000 ou 2000
cards precisa ser viável — o que torna qualquer processamento sobre o deck
inteiro **incremental e retomável desde o primeiro desenho**, não uma passada
única que recomeça do zero se falhar no meio.

---

## O que conta como sucesso

**Critério principal — comportamental.** O autor voltar a usar a ferramenta por
vontade própria, com regularidade, no lugar de apenas revisar no Anki.

**Critério secundário — desempenho.** A taxa de acerto em variações de expressões
já exercitadas subir ao longo do tempo.

O secundário é subordinado ao principal por um motivo: ele é **circular**. O
sistema escolhe o que mostrar e depois se avalia sobre o que escolheu mostrar —
essa métrica melhora se o sistema simplesmente mostrar coisas mais fáceis. O
critério comportamental não é manipulável por dentro.

**Requisito da trilha — progresso observável.** Distinto dos critérios acima: o
avanço em um conceito precisa ser verificável pelo usuário, pelos dados
registrados e pela redução de dificuldade dos exercícios daquele conceito ao longo
do tempo. Isso é requisito de interface, não medida de sucesso.

---

## Princípios de desenho

**Precisão é acumulada, não medida.** O sistema não estima o nível do usuário de
uma vez. Ele acumula evidência exercício a exercício e fica progressivamente mais
preciso sobre o quanto o usuário sabe de cada conceito.

**Gramática emergente.** O sistema não é um módulo de gramática. É um sistema de
input que, com volume suficiente, revela padrões: identifica estruturas
recorrentes no material que o usuário estudou, gera exercícios sobre elas com
vocabulário que ele já conhece e pode "dar nome aos bois" — explicar a estrutura
que ele já usa intuitivamente. A gramática aparece como consequência do volume,
não como ponto de partida. *(Recuperado de `historico/planejamento-geral-2.md`;
é o fundamento das decisões [0009](decisoes/0009-unidade-de-conhecimento.md) e
[0010](decisoes/0010-lista-de-conceitos.md).)*

**Frequência é informação sobre o usuário, não só sobre a expressão.** A
classificação `common`/`moderate`/`niche` existe para que o usuário saiba se está
aprendendo uso geral ou vocabulário de nicho — e, acumulada, para revelar **em
quais nichos ele tem vocabulário**. Um advogado se beneficia de *flip someone*
("convencer um cúmplice a delatar"); um cozinheiro nunca verá esse uso.
*(Recuperado de `historico/brainstorm.md`.)*

**Equilíbrio.** Ver muitos conceitos por dia não significa aprender muitos
conceitos. Parte do que o sistema apresenta é primeiro contato, não estudo.

**Nuances são condicionais.** O sistema não força nuance onde ela não existe.

---

## Pendências — não decididas

Registradas como pendências, e não resolvidas à força, porque documento que finge
certeza vira premissa não questionada meses depois.

1. **Papel do Anki.** A decisão [0005](decisoes/0005-anki-fonte-de-material.md)
   está tomada e é acionável, mas o autor sinalizou que o tópico pode precisar de
   mais trabalho para uma resposta mais precisa. Se surgir dúvida durante o
   desenvolvimento, é aqui que ela mora.
2. **Desenho do loop de precisão.** Como sugestão do sistema, autorrelato e
   desempenho se combinam na prática — pede planejamento próprio.
3. **A lista de conceitos** ([0010](decisoes/0010-lista-de-conceitos.md)) sustenta
   a trilha inteira e foi decidida em nível de visão geral. Recomenda-se sessão
   dedicada antes de implementar.
4. **FSRS próprio.** Sem decisão. A [0005](decisoes/0005-anki-fonte-de-material.md)
   reduz muito a necessidade, mas não a elimina para quem não usa Anki.
5. **Juiz automático de qualidade.** Um LLM-juiz só é aceitável se verificar e
   entender as premissas do projeto com maestria — ver `debito-tecnico.md` item 4.
   Revisão humana cega vem primeiro, porque é ela que calibra o juiz.
6. **Testes paralelos com IA** para calibrar a avaliação de qualidade.
