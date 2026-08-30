# Auditoria da Documentação — UniversePie

**Data:** 2026-08-30  
**Escopo:** Todos os arquivos `.md` do projeto — premissas, ADRs (0001–0013), roadmap, débito técnico, regras de IA, arquitetura, sessões e histórico congelado.

---

## 1. Veredicto geral

A documentação é internamente consistente na maior parte. As decisões formam uma cadeia lógica coerente (0005→0006→0011→0012, 0009→0010, 0003→0004, etc.) e o projeto demonstra disciplina rara ao registrar tensões em aberto em vez de resolvê-las artificialmente.

Há, porém, **6 problemas concretos** que merecem atenção, listados por gravidade.

---

## 2. Problemas identificados

### 2.1 — `ai-rules.md` contradiz `premissas.md` na prática (GRAVE)

**Onde:** [ai-rules.md](file:///home/rafael/dev/projects/UniversePie/docs/ai-rules.md#L67-L81) · [premissas.md](file:///home/rafael/dev/projects/UniversePie/docs/premissas.md#L26-L28)

O `premissas.md` declara que a ferramenta existe para expor variações (n+1). O `ai-rules.md` impõe rotação obrigatória de 5 estratégias, das quais `production` e `interference` testam o sentido *já conhecido* — são "n", não "n+1". Resultado: o prompt **garante** que ≥40% da sessão viole a premissa central. A métrica de auditoria (5/5 coverage) registra isso como saúde.

> [!IMPORTANT]
> O problema **já está documentado** como débito técnico nº 8 e como revisão pendente no ADR 0002. Porém, `ai-rules.md` continua prescrevendo a regra como se fosse intacta. O arquivo deveria marcar explicitamente que a rotação de 5 estratégias está em revisão, com referência cruzada ao ADR 0002 e ao débito nº 8 — não apenas no parágrafo final, mas na tabela de estratégias em si.

**Ação sugerida:** Anotar na tabela de estratégias quais são "n" e quais são "n+1", com link para o ADR 0002. Não corrigir o prompt ainda — a correção pede remedição — mas não apresentar a regra como se fosse saudável.

---

### 2.2 — `lapses` como semente contradiz o antipadrão (MODERADO)

**Onde:** [ADR 0005](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0005-anki-fonte-de-material.md#L27-L30) · [debito-tecnico.md item 1](file:///home/rafael/dev/projects/UniversePie/docs/debito-tecnico.md#L32-L34) · [premissas.md](file:///home/rafael/dev/projects/UniversePie/docs/premissas.md#L61-L74)

O ADR 0005 diz que `lapses` mede "tropeço" e serve como semente para partida a frio. Porém, se o usuário tropeça repetidamente num card, ele ainda não domina o "n" — e a ferramenta propõe apresentar variações ("n+1") sobre algo que o usuário sequer memorizou no nível base. Isso é exatamente o antipadrão descrito em `premissas.md`: material mal calibrado gera tédio/irritação.

Há uma segunda leitura possível: `lapses` alto → "fricção" → usar esses cards como ponto de *partida* (não necessariamente para variação, mas para reforço). Essa leitura é plausível mas **não está escrita** no ADR. A ambiguidade é o problema.

**Ação sugerida:** Esclarecer no ADR 0005 ou no `debito-tecnico.md` item 1 se cards com alto `lapses` entram na rotação para **reforço do sentido base** (n) ou para **apresentação de variações** (n+1). São caminhos diferentes e a ambiguidade vai se propagar para a implementação.

---

### 2.3 — Circularidade nos critérios de sucesso (MODERADO)

**Onde:** [premissas.md](file:///home/rafael/dev/projects/UniversePie/docs/premissas.md#L101-L117)

O critério primário é comportamental ("o autor voltar a usar"). O critério secundário é de desempenho ("taxa de acerto subir"). O documento reconhece que o secundário é circular — o sistema pode simplesmente mostrar coisas fáceis. Porém, o critério primário sofre do viés oposto: uma ferramenta que maximize engajamento sem carga cognitiva (gamificação, dopamina rápida, sem "n+1" de verdade) pode reter o usuário sem ensiná-lo.

**Não há métrica externa isolada.** Ambos os critérios são vulneráveis a vieses internos.

O documento foi honesto ao subordinar o secundário ao primário, mas não registra a vulnerabilidade do primário.

**Ação sugerida:** Registrar a vulnerabilidade como ponto de atenção. Não precisa ser resolvido agora, mas a pendência nº 5 (juiz automático) e a revisão humana planejada são candidatas naturais a essa métrica externa.

---

### 2.4 — Risco da classificação na ingestão sem mecanismo de reversão (MODERADO)

**Onde:** [ADR 0009](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0009-unidade-de-conhecimento.md#L32-L33) · [ADR 0010](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0010-lista-de-conceitos.md)

A decisão de inferir conceito gramatical na ingestão (uma vez por card, gravado, não recalculado) é crucial para estabilidade da trilha. Porém, se a IA classificar mal 2000 cards, toda a base de evidência fica corrompida desde a origem.

O ADR 0010 prevê versionamento da lista e recomenda sessão dedicada antes de implementar. Porém, **nenhum dos documentos prevê auditoria da classificação em si** ou mecanismo de rollback. A única menção é que "lista fechada permite auditar por amostra e medir concordância" — mas não há procedimento descrito.

> [!TIP]
> O skill [prompt-review.md](file:///home/rafael/dev/projects/UniversePie/skills/prompt-review.md) e o auditor existente podem servir de base para um procedimento de auditoria da ingestão, mas isso precisa ser planejado explicitamente.

**Ação sugerida:** Registrar como ponto de atenção (na pendência nº 3 ou no próprio ADR 0010) que a sessão dedicada precisa incluir: (a) como auditar a classificação por amostra, (b) como reverter/reclassificar se necessário.

---

### 2.5 — Conflito de autorrelato quando o desempenho é ruim (MENOR)

**Onde:** [ADR 0007](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0007-autorrelato-e-comando.md#L18-L25)

A precedência é: texto espontâneo > desempenho > autorrelato. O autorrelato é lido como "comando" (escale/desescale). Porém: se o usuário erra tudo (desempenho ruim) e clica "fácil demais" (comando para escalar), o sistema deveria obedecer o comando e apresentar material mais complexo a alguém que já falha no atual? A decisão fixa a precedência, não o fluxo de conflito.

O ADR reconhece isso no ponto de atenção ("a combinação dos três sinais pode ser aprimorada") e remete ao planejamento do loop de precisão (pendência nº 2 do `premissas.md`).

**Ação sugerida:** Nenhuma imediata. A pendência nº 2 cobre isso. O cenário conflitante está implícito mas merece ser registrado como caso de teste futuro.

---

### 2.6 — Roadmap tensiona com "gramática emergente" (MENOR)

**Onde:** [roadmap.md](file:///home/rafael/dev/projects/UniversePie/docs/roadmap.md#L48) · [premissas.md](file:///home/rafael/dev/projects/UniversePie/docs/premissas.md#L127-L134)

O `premissas.md` estabelece que gramática é emergente — aparece como consequência do volume, não como ponto de partida. O `roadmap.md` lista "Testar conceito gramatical isolado — quero verificar meu *I've…*" e "Declaração espontânea de fraqueza". Ambos pressupõem que o usuário B1/B2 sabe nomear suas falhas gramaticais. Isso não é proibido pela premissa (é "treino sob demanda" do ADR 0008), mas tensiona com a ideia de que gramática não é ponto de partida.

**Ação sugerida:** Nenhuma. A tensão é legítima e o ADR 0008 a resolve (é o usuário que escolhe, não o sistema que impõe). Registrar como nota no roadmap é suficiente.

---

## 3. Análise dos ADRs — Estrutura e Completude

### O que está correto

| ADR | Veredicto |
|-----|-----------|
| [0001](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0001-pool-em-lote.md) | Completo. Contexto/decisão/consequências claros. Efeito colateral medido (73% vazamento) |
| [0002](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0002-rotacao-de-estrategias.md) | Bem escrito. Identifica seu próprio defeito e registra revisão pendente |
| [0003](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0003-cloze-como-producao-ativa.md) | Completo. Alternativas rejeitadas documentadas com motivo |
| [0004](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0004-string-matching-no-cloze.md) | Completo. Escopo bem delimitado (congela avaliação por IA, não normalização) |
| [0006](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0006-medida-nasce-na-ferramenta.md) | Completo. Rejeição explícita de calibração inicial é coerente |
| [0008](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0008-trilha-e-espelho.md) | Lógica sólida. A diferença entre espelho e prescrição está bem nomeada |
| [0009](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0009-unidade-de-conhecimento.md) | Fundamentação forte. É a base matemática da trilha |
| [0010](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0010-lista-de-conceitos.md) | O mais completo. O raciocínio de versionamento é concreto |
| [0011](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0011-origem-da-evidencia.md) | Bem estruturado. Tensão futura registrada em vez de ignorada |
| [0012](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0012-memoria-em-sqlite.md) | Objetivo e correto |
| [0013](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0013-ordem-de-execucao.md) | Raciocínio tático correto (isolar variáveis de melhoria) |

### O que precisa de atenção

| ADR | Problema |
|-----|----------|
| [0004](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0004-string-matching-no-cloze.md) | Não discute por que `acceptable_alternatives` no payload de geração não pode cobrir conjugações. Essa saída intermediária (entre string matching puro e avaliação por IA) não foi avaliada |
| [0005](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0005-anki-fonte-de-material.md) | Ambiguidade sobre como usar cards com alto `lapses` (ver item 2.2 acima) |
| [0007](file:///home/rafael/dev/projects/UniversePie/docs/decisoes/0007-autorrelato-e-comando.md) | Caso de conflito desempenho vs. autorrelato não resolvido (ver item 2.5) |

---

## 4. Histórico congelado — Contradições e ideias perdidas

O `CLAUDE.md` avisa corretamente que `docs/historico/` contém instruções contrárias às decisões atuais. As contradições concretas são:

| Arquivo histórico | Contradição |
|--|--|
| `contexto-handoff.md`, `planejamento-geral.md`, `planejamento-geral-2.md` | Instruem a usar `interval`/`lapses` do Anki para medir domínio → contradiz ADR 0005 e 0006 |
| `planejamento-geral.md` | Define "n+1" como incremento de Krashen → contradiz a redefinição em `premissas.md` |
| `brainstorm.md` | Sugere classificação por CEFR (A1–C2) → contradiz ADR 0010 |
| `contexto-handoff.md` | Instrui a IA a ler `PlanejamentoGeral2.md` como referência ativa → contradiz `CLAUDE.md` |
| `planejamento-geral-2.md` | Exige Svelte + Vite + API do Claude → contradiz stack atual |

### Ideias do histórico que merecem verificação no roadmap

| Ideia | Origem | Status no roadmap |
|--|--|--|
| Exposição passiva de sinônimos (estilo DeepL) | `brainstorm.md` | ✅ Presente |
| Estatística de nicho (áreas de vocabulário) | `brainstorm.md` | ✅ Presente |
| Conceitos dominados saem da rotação | ambos os planejamentos | ✅ Presente |
| Fixtures de teste com dados reais do `expressoes-de-fundamento.md` | `expressoes-de-fundamento.md` | ❌ Ausente — tabelas de polissemia prontas para usar como fixtures |

---

## 5. Resumo de ações sugeridas

| # | Ação | Urgência | Referência |
|---|------|----------|------------|
| 1 | Anotar na tabela de estratégias do `ai-rules.md` quais são "n" e quais "n+1", com link para ADR 0002 | Alta | §2.1 |
| 2 | Esclarecer no ADR 0005 se cards com alto `lapses` entram para reforço (n) ou variação (n+1) | Média | §2.2 |
| 3 | Registrar vulnerabilidade do critério comportamental em `premissas.md` | Baixa | §2.3 |
| 4 | Incluir auditoria da classificação e rollback na sessão dedicada do ADR 0010 | Média | §2.4 |
| 5 | Considerar usar `expressoes-de-fundamento.md` como fixture de teste | Baixa | §4 |
| 6 | Avaliar se `acceptable_alternatives` no prompt de cloze pode cobrir conjugações (saída intermediária antes de IA-juiz) | Baixa | §3 |

---

## Fechamento — triagem das ações

Feita no mesmo dia, pelo agent que escreveu a documentação auditada.

| # | Achado | Decisão |
|---|---|---|
| 2.1 | `ai-rules.md` apresenta a rotação como saudável (GRAVE) | **Rejeitado — falso positivo.** A nota já existe logo abaixo da tabela de estratégias, nomeando quais são "n" e quais são "n+1", com link para o ADR `0002` e a marca de revisão pendente. O auditor leu versão anterior ou não chegou ao parágrafo. |
| 2.2 | `lapses` ambíguo: reforço (n) ou variação (n+1)? | **Aceito.** Melhor achado da auditoria — ambiguidade real que se propagaria para a implementação. Resolvido no ADR `0005`: card com `lapses` alto entra para reforçar o sentido base. Mostrar o "+1" de algo cujo "n" o usuário não segura é o mesmo defeito de calibração na direção oposta. |
| 2.3 | O critério comportamental também tem viés | **Rejeitado.** Verdadeiro em tese — engajamento não é aprendizado. Mas o usuário é o próprio autor, e o projeto já proíbe gamificação por escrito. Documentar risco de manipulação de um usuário único, por ele mesmo, é peso sem retorno. |
| 2.4 | Sem auditoria nem reclassificação da ingestão | **Aceito.** Uma frase no ADR `0010`: o versionamento da lista resolve "a lista cresceu", não resolve "a IA errou". |
| 2.5 | Conflito autorrelato × desempenho | **Rejeitado** — o próprio auditor registra "nenhuma ação imediata". Coberto pela pendência nº 2. |
| 2.6 | Roadmap tensiona com gramática emergente | **Rejeitado** — o próprio auditor registra "nenhuma ação". A tensão é legítima e o ADR `0008` a resolve. |
| §3 | `acceptable_alternatives` pode cobrir conjugação? | **Aceito, e é o achado mais acionável dos seis.** Estava classificado como urgência baixa e é código, não documento: mover o problema do avaliador para o gerador não exige código novo e é medível pelo auditor. Registrado no `debito-tecnico.md` item 5 como saída intermediária. |
| §4 | Fixtures a partir de `expressoes-de-fundamento.md` | **Aceito.** Entrou no `roadmap.md`. |

**Resultado:** 4 aceitos, 4 rejeitados, 24 linhas adicionadas, nenhum documento
reescrito.

**Calibração para quem ler depois:** o único achado classificado como GRAVE era
falso, e dois dos seis vinham com "nenhuma ação sugerida" do próprio auditor. A
tabela da seção 3 classifica 11 dos 13 ADRs como completos. A leitura razoável é
que a documentação está em estado utilizável e que outra rodada de auditoria
renderia pouco — o gargalo do projeto voltou a ser código, conforme a decisão
`0013`.
