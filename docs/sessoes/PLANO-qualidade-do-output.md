# Plano — melhorar a qualidade do que a IA gera a partir dos cards

**Tipo: plano.** Escrito antes da sessão, para ser consumido por ela. Quando a
sessão terminar, este arquivo é substituído pelo registro dela, datado.

Branch: `feat/card-quality-audit`. **É isto que a branch existe para fazer.** As
sessões de 2026-08-29 e 2026-08-30 construíram o auditor, a linha de base e a
documentação. Nenhuma melhorou um único exercício.

---

## Objetivo

Reduzir os defeitos medidos nos exercícios que o sistema gera, corrigindo os
**prompts**, e provar a redução comparando contra a linha de base.

Não é "mexer nos prompts". É baixar número que já foi medido.

## Definição de pronto

1. As cinco correções do índice de `debito-tecnico.md` aplicadas, ou
   explicitamente descartadas com motivo escrito.
2. Rodada nova comparada com `--compare docs/audit/baseline-*.json`, no **mesmo
   pool congelado**, para não misturar melhora de prompt com sorte de sorteio.
3. `clean_rate` maior e nenhuma checagem de ERRO nova onde não havia.
4. Amostra lida por humano (`--sample`), porque `clean_rate` mede conformidade
   com regra, não valor pedagógico — é o achado 4 de 2026-08-29 e ele não
   caducou.
5. Nova linha de base gravada e `docs/sessoes/README.md` apontando para ela.

## Sequência

**1. Medir antes de tocar em qualquer coisa.**
Congelar um pool (`--save-cards`), rodar quiz e cloze, e **ler os exercícios**,
não só o `clean_rate`. Sem isso a sessão corrige defeito de planilha em vez de
defeito de exercício.

**2. Investigar o item 12 antes de corrigi-lo.**
A contagem de grounding não separa "o modelo inventou, ignorando o pool" de "o
modelo usou o pool e o `used_cards` veio errado". São correções diferentes — uma
é prompt, outra é contrato. Ler os itens marcados no `.raw.json`.

**3. Corrigir, na ordem do índice de `debito-tecnico.md`.**
Item 12, depois 10, 9, 11, 8. Ordem por evidência: **26 dos 37 defeitos da linha
de base estão no quiz.** Quatro das cinco correções são no prompt de quiz.

Cuidado no item 8: a rotação das estratégias existe para impedir o "flashcard
disfarçado" da Alpha v2 — ver [`0002`](../decisoes/0002-rotacao-de-estrategias.md).
Preservar o antídoto, remover a diluição da premissa. Não é remover a regra.

**4. Remedir e comparar.** Iterar no Ollama, que não gasta cota: `qwen3:8b`
responde uma sessão de 5 exercícios em ~22s com o modelo frio.

## O que esta sessão NÃO é

- Não é documentação. Está feita.
- Não é ferramental. Os seis achados do ultrareview estão fechados.
- Não é o núcleo n+1 (classificação, lista de conceitos, memória). Aquilo é
  grande, tem pendências de desenho registradas e pede sessão própria — ver
  [`0010`](../decisoes/0010-lista-de-conceitos.md) e as pendências de
  `premissas.md`.

Se a sessão terminar sem número novo, ela não cumpriu o objetivo.

## Ressalvas herdadas

- **Mudar prompt exige confirmação do autor** (`CLAUDE.md`).
- **O 6/56 do item 11 foi medido com a checagem `does_not_fit_the_blank`
  defeituosa**, corrigida em 2026-08-30. Reconfirmar, não assumir.
- **Pool congelado é obrigatório para comparar.** A linha de base de 2026-08-29
  sorteou pool a cada rodada, então parte da diferença entre modelos vem do
  material. Para medir prompt, o material tem que ser o mesmo.
- **`clean_rate` pode inverter a ordenação real de qualidade** — item 4 do
  `debito-tecnico.md`, com o caso medido.
