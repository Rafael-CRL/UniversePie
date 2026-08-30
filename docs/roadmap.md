# UniversePie — Roadmap

**Última revisão:** 2026-08-30

Features não construídas. Defeitos do que já existe ficam em `debito-tecnico.md`;
o *porquê* do projeto, em `premissas.md`.

Vários itens abaixo foram recuperados de `historico/` — o projeto os perdeu na
migração do cofre para o repositório, e o motivo original de cada um estava lá.

---

## Núcleo da premissa n+1

Não são features opcionais: sem elas a premissa do projeto não existe no código.
Estavam listados como backlog comum e foram promovidos.

- **Classificação de conceito na ingestão** — inferir o conceito gramatical de
  cada card contra a lista controlada, gravar, não recalcular.
  [0009](decisoes/0009-unidade-de-conhecimento.md) · [0010](decisoes/0010-lista-de-conceitos.md)
- **Lista de conceitos derivada do deck**, fechada e versionada.
  [0010](decisoes/0010-lista-de-conceitos.md) — pede sessão dedicada.
- **Registro de evidência em SQLite** — `(expressão, conceito, tipo de variação,
  versão da lista, origem, resultado, data)`.
  [0011](decisoes/0011-origem-da-evidencia.md) · [0012](decisoes/0012-memoria-em-sqlite.md)
- **Detecção de lacunas por padrão de erro** — identificar o que o usuário erra e
  gerar exercícios direcionados àquilo. Depende inteiramente do registro acima.
- **Família de palavras como exercício** — passado, particípio, derivados.
  **Bloqueado** pelo item 5 do `debito-tecnico.md`: enquanto o matching do cloze
  marcar conjugação correta como erro, este exercício testaria exatamente a
  dimensão que o avaliador não sabe avaliar.

## Trilha e sinalização

- **Trilha por conceito** — espelho descritivo do progresso, com treino sob
  demanda. [0008](decisoes/0008-trilha-e-espelho.md)
- **Sinalização no exercício** — botão de "fácil demais / difícil / conheço as
  variações", lido como direcionamento. [0007](decisoes/0007-autorrelato-e-comando.md)
- **Sugestão dispensável de revisão** — o sistema aponta um conceito que merece
  atenção; ignorar não tem consequência. Sugestão que não se pode ignorar é
  prescrição, e prescrição está fora. [0008](decisoes/0008-trilha-e-espelho.md)
- **Declaração espontânea de fraqueza** — o usuário informa que é ruim em algo
  ("tense") e o sistema usa como ponto de partida. *Hipótese.* Distinguir de
  calibração compulsória: a diferença está em quem inicia, e o momento em que o
  sistema **pergunta** é o momento em que vira o ritual que o projeto critica.
- **Estatística de nicho** — quais áreas o usuário tem vocabulário, a partir da
  acumulação de `commonality` e tags. *Recuperado de `historico/brainstorm.md`.*
- **Testar conceito gramatical isolado** — "quero verificar meu *I've…*".

## Exposição e variação

Recuperados de `historico/brainstorm.md`, ausentes do repositório até hoje.

- **Exposição passiva de sinônimos** — mostrar a alternativa discretamente, sem
  exigir interação, no espírito do que o DeepL faz com traduções alternativas.
  *"Não é estudo ativo, é exposição passiva que planta uma semente."*
  Ex.: "when it comes to me" → "as far as I'm concerned".
- **Variação de registro** como eixo próprio — coloquial, formal, dialeto.
- **Minigame de associação** entre expressões equivalentes.
- **Equilíbrio** — ver muitos conceitos por dia não é aprender muitos conceitos.
  Parte do que o sistema mostra é primeiro contato, e o desenho precisa respeitar
  isso em vez de maximizar volume.
- **Conceitos dominados saem da rotação** — princípio presente nos dois
  planejamentos originais e ausente do sistema atual.

## Escrita

- **Análise de texto próprio** — o usuário cola algo que escreveu (artigo,
  conversa com IA) e o sistema identifica padrões. **Voluntário:** o software não
  solicita explicitamente; deixa claro que ajuda. É a origem `writing` da
  [0011](decisoes/0011-origem-da-evidencia.md).
- **Avaliação por redação** — o sistema pede um texto como diagnóstico.
  *Hipótese.* Inverte a restrição do item acima e esbarra na
  [0004](decisoes/0004-string-matching-no-cloze.md). Tensão registrada em
  [0011](decisoes/0011-origem-da-evidencia.md).
- **Exercícios de escrita livre** — dependem de avaliação confiável de texto.

## Entrada de conteúdo

- **Staged Area** — fila de revisão: nada vira card sem o usuário aprovar.
- **Inputs além do Anki** — texto colado, PDF, extensão de navegador, captura de
  legenda do YouTube, integração MPV/mpvacious.
- **Tags automáticas por área** — culinária, tecnologia, finanças, gírias. No
  planejamento original, tags são o **índice do conhecimento acumulado**, não
  categoria passiva: são o mecanismo pelo qual usuário e IA navegam o banco.

## Infraestrutura e forma

- **Fixtures de teste a partir do histórico** — `historico/expressoes-de-fundamento.md`
  tem uma tabela de phrasal verbs por partícula (out, on, off, in, down, up, over,
  around, back, away, through, along, forward) e o *turn around* com três sentidos.
  É material pronto para testar `discrimination` e `polysemy` sem depender do Anki.
- **TTS** — áudio nos cards.
- **Migração Svelte + Vite** — no backlog; não é prioridade.
- **Distribuição desktop** (Tauri) e **multi-idioma** — cogitados no planejamento
  original, sem decisão.

## Sem decisão

- **FSRS próprio.** A [0005](decisoes/0005-anki-fonte-de-material.md) reduz muito
  a necessidade — o sistema deixa de depender do Anki para medir domínio —, mas
  não a elimina para quem não usa Anki. Estava listado como backlog comum e não é:
  é uma decisão em aberto. Argumento do autor a favor de não reimplementar: o
  algoritmo do Anki é público e eficiente, não é preciso reinventar a roda.
