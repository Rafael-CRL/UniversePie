# Skill: Adicionar Novo Tipo de Exercício

Use quando for implementar um novo modo de exercício além de quiz e cloze.

---

## Checklist obrigatório

### 1. Validar a decisão antes de implementar
Antes de escrever qualquer código, confirmar:
- [ ] **O exercício apresenta variação do que o usuário já conhece, ou só reforça o
      que ele já sabe?** É a premissa n+1 (`docs/premissas.md`) e é o critério
      central. Quiz e cloze são os mecanismos atuais, não os definitivos —
      mecanismos mais precisos são bem-vindos, desde que passem por aqui
- [ ] O exercício testa produção ativa ou tem justificativa para ser apenas reconhecimento?
- [ ] A avaliação da resposta é confiável sem chamada extra à IA? (string matching, regex, ou estrutura fechada)
- [ ] O exercício pode ser gerado a partir do pool de cards existente sem mudar o fluxo de dados?

Se qualquer resposta for "não", documentar a decisão antes de prosseguir.

### 2. Backend

- [ ] Criar modelo Pydantic para o item (`XItem`) com todos os campos necessários
- [ ] Criar modelo Pydantic para a sessão (`XSession`)
- [ ] Adicionar validadores semânticos nos campos críticos (ex: `commonality` restrito a enum)
- [ ] Criar função `build_x_prompt()` seguindo as regras em `docs/ai-rules.md`
- [ ] Criar endpoint `/api/x-session?n=` com a mesma lógica de pool (`n * POOL_MULTIPLIER`)
- [ ] Mapear `used_cards` → `source_cards` (mesmo padrão do quiz e cloze)
- [ ] Ajustar timeout do httpx se necessário

### 3. Frontend

- [ ] Adicionar botão no seletor de modo (`Quiz | Cloze | Novo`)
- [ ] Implementar tela do exercício (frase, input, feedback)
- [ ] Feedback graduado: pelo menos correto / incorreto
- [ ] Area colapsável com cards-fonte do Anki (manter padrão dos outros modos)
- [ ] Atalhos de teclado (Enter para submit, Enter para avançar)
- [ ] Integrar com tela de resumo unificada (`advanceExercise`, `showSummary`)

### 4. Documentação

- [ ] Adicionar o novo endpoint na tabela de `docs/arquitetura.md`
- [ ] Registrar a escolha do mecanismo como ADR em `docs/decisoes/`, com as
      alternativas descartadas e o motivo — é o que a `0003` fez pelo cloze
- [ ] Se o mecanismo novo mudar a premissa ou revelar limite dela, registrar em
      `docs/premissas.md`
- [ ] Registrar a sessão em `docs/sessoes/`, com evidência e números

---

## Referência

Antes de implementar o prompt, ler `docs/ai-rules.md` inteiro.
Para o fluxo de dados, ler `docs/arquitetura.md`.
Para o critério de valor do exercício, ler `docs/premissas.md`.

Precedente útil: `docs/decisoes/0003-cloze-como-producao-ativa.md` registra as três
candidatas avaliadas quando o cloze foi escolhido, e por que as outras duas foram
descartadas.
