from pydantic import BaseModel, field_validator


class SourceCard(BaseModel):
    front: str
    back: str


class QuizItem(BaseModel):
    quiz_type: str
    concept: str
    # A expressão do pool em que este quiz se apoia, copiada do card. O cloze
    # sempre teve `target_expression` e é por isso que dá para checá-lo de forma
    # objetiva; o quiz declarava o que testa só em prosa (`concept`), e aí saber
    # se ele nasceu de um card do usuário virava sobreposição de palavras.
    #
    # Nome diferente do cloze de propósito: lá `target_expression` é a resposta,
    # e aqui é a ÂNCORA. O quiz existe para testar uma variação dela — outro
    # sentido, forma derivada, troca de partícula. Chamar os dois de "target"
    # convidaria a portar checagem de um para o outro invertendo o sentido.
    #
    # Opcional com default: campo novo que os modelos ainda não emitem de forma
    # comprovada. Se fosse obrigatório, `build_items` descartaria o item inteiro
    # e a falha sumiria em vez de virar número — foi exatamente o que aconteceu
    # com `used_cards`. O auditor mede quem não declara.
    source_expression: str = ""
    # Que tipo de variação este quiz apresenta sobre a expressão do card.
    #
    # Item 8 do `debito-tecnico.md`: das cinco estratégias, só `polysemy` e
    # `discrimination` apresentam variação, e a regra 7 do prompt manda rodar
    # todas. O sistema portanto GARANTE que parte de cada sessão reapresente o
    # sentido que o card já ensina — que é o oposto da premissa n+1 — e a métrica
    # de cobertura 5/5 registra isso como saúde.
    #
    # Enum e não prosa livre de propósito. Dois campos de texto ("sentido do
    # card" e "sentido testado") seriam mais expressivos e reproduziriam o item
    # 7: `concept` já é rótulo livre e por isso não agrega. Um enum agrega e
    # cruza com `quiz_type`.
    #
    # A ressalva honesta: isto é DECLARATIVO. Verifica o modelo contra si mesmo,
    # pega contradição, não pega erro — diferente de `source_expression`, que é
    # verificável contra o card.
    #
    # Opcional com default pela mesma razão do `source_expression`: campo novo
    # que os modelos ainda não emitem de forma comprovada, e obrigatório faria
    # `build_items` descartar o item inteiro, apagando a falha em vez de
    # transformá-la em número.
    variation_type: str = ""
    question: str
    options: list[str]
    answer_index: int
    explanation: str
    source_cards: list[SourceCard]

    @field_validator("quiz_type")
    @classmethod
    def valid_quiz_type(cls, v):
        allowed = {"discrimination", "production", "interference", "polysemy", "contextual"}
        if v not in allowed:
            raise ValueError(f"quiz_type deve ser um de {allowed}, recebeu '{v}'")
        return v

    @field_validator("variation_type")
    @classmethod
    def valid_variation_type(cls, v):
        # Vazio é aceito: quem não declara vira alerta no auditor, não item
        # descartado. Valor inventado, porém, quebraria a agregação que o campo
        # existe para permitir, e aí é melhor perder o item que sujar a chave.
        allowed = {
            "",
            "same_sense",
            "other_sense",
            "derived_form",
            "different_particle",
            "different_register",
        }
        if v not in allowed:
            raise ValueError(f"variation_type deve ser um de {sorted(allowed)}, recebeu '{v}'")
        return v

    @field_validator("options")
    @classmethod
    def exactly_four_options(cls, v):
        if len(v) != 4:
            raise ValueError(f"Esperado 4 opções, recebeu {len(v)}")
        return v

    @field_validator("answer_index")
    @classmethod
    def valid_answer_index(cls, v):
        if v not in (0, 1, 2, 3):
            raise ValueError(f"answer_index deve ser 0-3, recebeu {v}")
        return v


class QuizSession(BaseModel):
    quizzes: list[QuizItem]
    total: int


class ClozeItem(BaseModel):
    concept: str
    sentence: str
    target_expression: str
    acceptable_alternatives: list[str]
    hint: str
    commonality: str
    context_note: str
    explanation: str
    source_cards: list[SourceCard]

    @field_validator("commonality")
    @classmethod
    def valid_commonality(cls, v):
        allowed = {"common", "moderate", "niche"}
        if v not in allowed:
            raise ValueError(f"commonality deve ser um de {allowed}, recebeu '{v}'")
        return v


class ClozeSession(BaseModel):
    exercises: list[ClozeItem]
    total: int
