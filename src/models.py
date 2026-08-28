from pydantic import BaseModel, field_validator


class SourceCard(BaseModel):
    front: str
    back: str


class QuizItem(BaseModel):
    quiz_type: str
    concept: str
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
