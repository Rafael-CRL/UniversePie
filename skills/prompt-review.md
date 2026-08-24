# Skill: Revisão de Prompt do Gemini

Use antes de modificar qualquer prompt existente ou criar um novo.
Leia `docs/AI_RULES.md` antes de executar esta skill.

---

## O que verificar

### Alinhamento com a filosofia
- [ ] O prompt ancora no conhecimento existente do usuário, ou gera conteúdo genérico?
- [ ] Nuances são condicionais — o prompt instrui a IA a só capturar nuances quando elas existem?
- [ ] O prompt instrui honestidade sobre `commonality` (não tratar expressões de nicho como uso geral)?

### Qualidade dos exercícios
- [ ] O prompt exige produção ativa, não só reconhecimento passivo?
- [ ] Para quiz: as 5 estratégias rotativas estão presentes (`discrimination`, `production`, `interference`, `polysemy`, `contextual`)?
- [ ] Para quiz: distratores exploram interferência L1 (português) e confusões reais — não são absurdos óbvios?
- [ ] Para cloze: `acceptable_alternatives` são suficientes para cobrir variações legítimas da resposta?

### Contrato JSON
- [ ] O prompt especifica o schema JSON exato esperado?
- [ ] Campos com enum estão restritos explicitamente (`commonality`: apenas `common`, `moderate`, `niche`)?
- [ ] O prompt instrui a não incluir comentários dentro do JSON?
- [ ] `answer_index` está restrito a 0-3 para quiz?

### Pool e referências
- [ ] O prompt instrui a IA a usar `used_cards` para referenciar os cards que embasaram cada exercício?
- [ ] O prompt deixa claro que o pool é maior que `n` para dar superfície de correlação?

---

## Red flags — se encontrar algum, corrigir antes de prosseguir

- Prompt que instrui a gerar nuances para toda expressão indiscriminadamente
- Distratores que são obviamente errados (não há confusão possível com o português)
- JSON sem schema explícito (deixa a IA "adivinhar" a estrutura)
- Ausência de instrução sobre `commonality` em prompts de cloze
- Prompt que não referencia o pool de cards como contexto
