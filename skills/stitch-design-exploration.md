# Skill: Exploração de Design via Google Stitch

Use quando for gerar ou refinar mockups de UI para o UniversePie via Google
Stitch (design gerado por IA a partir de prompt de texto).

Ler `docs/CONTEXT.md` seção "Origem do nome e filosofia" antes de escrever
ou ajustar qualquer prompt de design.

---

## Princípios não-negociáveis do prompt

- [ ] Ancora na filosofia real do produto (acumulação de conhecimento em
      camadas, IA como camada de inteligência sobre dados do próprio
      usuário, produção ativa > reconhecimento passivo) — nunca um prompt
      genérico de "app de idiomas".
- [ ] Não prescreve cores, tipografia ou layout específicos — o objetivo é
      ver a direção de design que o Stitch propõe, não implementar algo já
      decidido.
- [ ] Deixa claro que seriedade pedagógica ≠ frieza visual (dark, bordas
      retas, "edgy"). Calor, cor e personalidade são bem-vindos; o que fica
      de fora é gamificação vazia (pontos, streaks, mascotes, conquistas).
- [ ] Qualquer desvio de convenções visuais comuns em apps de idiomas deve
      ser justificado pela filosofia do produto — nunca novidade pela
      novidade (cores/formas aleatórias só para parecer diferente).
- [ ] Inclui o princípio de "juice" (micro-interações e game feel) nos
      pontos de maior frequência de interação — seleção de resposta, avanço
      entre exercícios, atualização de progresso — sem virar mecânica de
      jogo.
- [ ] Descreve o fluxo funcional das 6 telas (início, geração, quiz,
      cloze, resumo, erro) em termos do que cada uma precisa resolver, não
      de como deve parecer.

---

## Prompts de referência

Dois prompts-base já validados, cada um testando uma leitura diferente da
metáfora do nome ("torta" como eco abstrato vs. elemento visual real). Usar
como ponto de partida, não copiar cegamente — ajustar conforme o que os
resultados anteriores do Stitch revelarem.

- **Prompt A — eco sutil/cósmico:** metáfora de acumulação e camadas fica
  abstrata (cosmos, construção, "todo composto de partes"); nenhuma
  ilustração literal de torta/sobremesa.
- **Prompt B — torta como elemento visual real:** mesma base filosófica,
  mas convida o Stitch a explorar ativamente formas circulares, fatias e
  paletas que evoquem confeitaria, combinadas com o lado cósmico.

Os textos completos dos dois prompts estão no histórico da conversa em que
esta skill foi criada — se não estiverem disponíveis, reconstruir a partir
dos princípios acima e da seção "Origem do nome e filosofia" em
`docs/CONTEXT.md`.

---

## Rodando exploração em lote (Stitch MCP)

Quando o servidor MCP do Stitch estiver configurado:

- [ ] Rodar um lote pequeno e deliberado (2-4 variações) em vez de um loop
      autônomo e longo — avaliar direção de design ainda exige olho humano,
      então gerar dezenas de variantes sem supervisão desperdiça cota de
      API sem ganho proporcional.
- [ ] A criação/refinamento dos prompts (julgamento criativo, ancoragem na
      filosofia) deve ficar com o modelo mais capaz da conversa — é
      trabalho de julgamento, não repetitivo.
- [ ] O disparo mecânico do loop (chamar a ferramenta do Stitch MCP repetidas
      vezes com prompts já prontos) pode rodar em um subagente com modelo
      mais barato (ex: Haiku), já que não exige julgamento — só execução.
      Isso não acontece automaticamente: por padrão, `/loop` reexecuta na
      mesma sessão/modelo que a disparou. Para separar os dois papéis é
      preciso spawnar um subagente explícito com override de modelo para a
      parte repetitiva.
- [ ] Revisar os resultados junto com o usuário antes de outra rodada —
      não encadear lotes automaticamente.

---

## Documentação

- [ ] Se um prompt gerar uma direção de design adotada, registrar a decisão
      e o raciocínio em `docs/CONTEXT.md` ou `CHANGELOG.md`.
- [ ] Atualizar os prompts de referência nesta skill se a direção mudar.
