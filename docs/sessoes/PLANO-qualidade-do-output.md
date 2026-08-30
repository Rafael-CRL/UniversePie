# Plano — baixar os defeitos medidos, corrigindo os prompts

**Tipo: plano.** Escrito antes da sessão, para ser consumido por ela. Ao terminar,
este arquivo é **apagado** e substituído pelo registro datado da sessão.

> **Leia primeiro:** `2026-08-30-linha-de-base-g1.md`. Ele tem a linha de base,
> os números por modelo e o achado que reordenou tudo. Este plano assume que você
> leu.

---

## O estado, sem rodeio

A branch `feat/card-quality-audit` tem **onze commits e zero exercício
melhorado.** Três sessões construíram o auditor, a linha de base, a documentação
e consertaram o instrumento. Nenhuma tocou num prompt.

**Esta sessão existe para mudar prompt e baixar número. Se terminar sem número
novo, falhou.**

---

## Regras que não se negociam

1. **Mudar prompt exige confirmação do autor** (`CLAUDE.md`). Proponha a mudança,
   mostre o texto exato do antes e depois, espere o sim. Uma de cada vez.
2. **Não comece pelo cloze.** O modelo tende a derivar para lá porque o cloze é
   mecanicamente mais verificável. Quatro dos cinco itens são do prompt de quiz.
   Se você estiver mexendo em cloze antes de 9 e 10 estarem medidos, parou de
   seguir este plano.
3. **Uma correção por vez, medida isolada.** Duas juntas e não se sabe qual moveu
   o número.
4. **Não invente item novo.** A lista está em `debito-tecnico.md`. Se achar algo
   fora dela, registre lá e siga o plano.

---

## Sequência

### Passo 0 — reconhecer o terreno (10 min, sem gastar cota)

```bash
python3 -m pytest -q                      # tem que dar 121 passed
sed -n '1,45p' docs/debito-tecnico.md     # o índice, ordenado por evidência
```

A linha de base já existe. **Não meça de novo antes de mudar nada** — a sessão
anterior já fez isso e os arquivos estão em `docs/audit/base-g1-*.json`.

### Passo 1 — item 9, a resposta nunca na última posição

**Por que primeiro:** 0 em 122 quizzes, seis configurações de modelo, dois pools,
dois dias. É o defeito mais reproduzível do projeto e aparece no Gemini. A
correção é uma instrução de distribuição no prompt de quiz.

**Onde:** `src/prompts.py`, seção `## Rules` de `build_quiz_prompt`.

**Cuidado:** não basta mandar "varie a posição". O modelo já obedece a rotação de
estratégias à risca (5/5 em todos), então instrução explícita funciona neste
prompt — mas instrução vaga vira ruído. Considere pedir a posição explicitamente
antes de escrever as opções.

**Como medir:**
```bash
python3 scripts/audit_exercises.py --provider gemini \
  --cards docs/audit/pool-exemplo.json --mode both --runs 3 --n 5 \
  --tag v2-item9-gemini
python3 scripts/audit_exercises.py --compare \
  docs/audit/base-g1-gemini.json docs/audit/v2-item9-gemini.json
```

**Pronto quando:** a posição 3 deixa de ser zero, `answer_position_top_share` cai,
e nenhuma checagem de ERRO nova aparece.

### Passo 2 — item 10, a numeração do pool vazando na explicação

**Por que segundo:** 6 em 60 no pool congelado, e **3 das 6 no Gemini**. É o único
outro item que aparece no modelo que roda em produção.

**Cuidado, isto mudou:** a hipótese antiga era que combinar cards dirigia o
vazamento (73% em 4 cards). **Não reproduz** — no pool congelado é 4% contra 8%.
Não corrija "combinar cards". Corrija o vazamento: proibir referência a card no
texto visível, ou mudar `_format_cards_block` (`prompts.py:4`) para não sugerir
numeração citável.

**Como medir:** igual ao passo 1, `--tag v2-item10-gemini`.

### Passo 3 — decidir sobre 11 e 12 com o autor

**Não execute estes sem conversar.** Os dois são condicionais ao modelo:

- **Item 12** — 18 achados em modelo local, **0 em API**. Causa identificada: o
  modelo pequeno copia os exemplos literais das descrições de estratégia
  (`prompts.py:36` e `:42`). Correção candidata barata: tirar as expressões
  literais dos exemplos, ou marcá-las como ilustração proibida de reusar.
- **Item 11** — 7 no Groq, **0 no Gemini**. Medir a correção em Gemini daria zero
  antes e zero depois.

**A pergunta para o autor:** o produto precisa funcionar bem em modelo local? Se
sim, estes dois valem a sessão e a medição é no Ollama. Se não, descarte-os
explicitamente com motivo escrito — que é uma das formas de "pronto" válidas.

### Passo 4 — item 8, só se sobrar sessão

Não tem número. Medi-lo exige dois campos novos (`sense_on_card`, `sense_tested`),
o que é outra mudança de contrato. O caminho está escrito no próprio item.
**Preserve o antídoto** da decisão [0002](../decisoes/0002-rotacao-de-estrategias.md):
a rotação existe contra o "flashcard disfarçado" da Alpha v2. Remova a diluição,
não a regra.

### Passo 5 — fechar

```bash
# nova linha de base, os quatro modelos, mesmo pool
for m in gemini groq; do python3 scripts/audit_exercises.py --provider $m \
  --cards docs/audit/pool-exemplo.json --mode both --runs 3 --n 5 --tag v2-$m; done
# ollama: subir antes, DESLIGAR depois
```

1. Amostra cega para leitura humana (`--sample 10`) — **é do autor, não sua.**
2. `docs/sessoes/README.md` apontando para a linha de base nova.
3. Registro datado da sessão, com os números antes e depois.
4. **Apague este arquivo.** Ele cumpriu a função.
5. `git add -f docs/audit/v2-*.json` — os relatórios são versionados, os `.raw` e
   `.md` não (regra do `.gitignore`).

---

## Definição de pronto

- [ ] Itens 9 e 10 corrigidos e **medidos no Gemini**, com número antes e depois
- [ ] Itens 11 e 12 corrigidos **ou descartados com motivo escrito**
- [ ] Item 8 corrigido, adiado com motivo, ou instrumentado
- [ ] `clean_rate` maior no Gemini e nenhum ERRO novo onde não havia
- [ ] Amostra cega gerada e entregue ao autor
- [ ] Linha de base nova gravada, `sessoes/README.md` atualizado
- [ ] Este arquivo apagado, registro da sessão no lugar

---

## Armadilhas conhecidas

- **`--from-raw` sobrescreve no lugar** se você não passar `--out-dir` ou `--tag`.
  Ele avisa. Leia o aviso.
- **`--compare docs/audit/*.json`** ignora os `.raw.json` sozinho desde
  2026-08-30, mas continua casando `-amostra.json`. Liste os arquivos.
- **Ollama:** `ollama serve` antes, **desligar depois**. O autor pediu
  explicitamente.
- **Groq estoura TPM** (8000 tokens/min) com `--runs 3 --mode both`. O `--retries`
  cobre; é condição normal, não defeito.
- **A linha de base de 2026-08-29 não serve de comparação.** Pool sorteado e
  anterior ao campo `source_expression` — reanalisá-la soma 62
  `empty_source_expression`, que é o campo novo aparecendo, não regressão.
- **`clean_rate` pode inverter a ordenação real de qualidade** — item 4 do
  `debito-tecnico.md`, com o caso medido.
