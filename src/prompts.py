def _format_cards_block(cards: list[tuple[str, str]]) -> str:
    cards_block = ""
    for i, (front, back) in enumerate(cards):
        cards_block += f"Card {i + 1}:\n  Front: {front}\n  Back: {back}\n\n"
    return cards_block


def build_quiz_prompt(cards: list[tuple[str, str]], n: int) -> str:
    """Builds the prompt that sends a pool of cards and requests n quizzes."""
    cards_block = _format_cards_block(cards)

    return f"""You are a quiz designer for intermediate-to-advanced English learners whose native language is Brazilian Portuguese.

You will receive a pool of {len(cards)} flashcards from the learner's Anki deck. Your job is to generate exactly {n} quiz questions that test DEEP understanding — not surface recognition.

## Quiz Strategy Types

You MUST vary the strategy across the session. Use as many different types as possible. Each quiz must declare its type.

### discrimination
Use when the pool contains cards that share a root word, similar structure, or related concept (e.g., "settle into" vs "settle for" vs "settle on"; or "get off" vs "get on" vs "get over").
Present a context and force the learner to pick the correct variant.
The wrong options MUST be real expressions from other cards in the pool when possible.

### production
Describe a situation, a communicative intent, or a meaning — then ask which expression fits.
Do NOT give the expression and ask for the meaning. That is passive recognition and forbidden in this type.
Example: "You want to tell someone to stop insisting on a topic. Which expression fits?" → Drop it

### interference
Design a question that exploits a common error a Brazilian Portuguese speaker would make.
One of the wrong options MUST be the literal Portuguese translation trap — the answer the learner's L1 brain wants to pick.
Example: "'She walked down the street' means:" with a trap option "She descended the street".

### polysemy
Use when a word in the pool has multiple distinct meanings (e.g., "sound" = healthy/safe vs noise vs to seem).
Present 2-3 short sentences using the same word and ask in which sentence it carries a specific meaning.

### contextual
Present a realistic conversational or written scenario and ask what a speaker means, what would be the appropriate response, or what the pragmatic implication is.
This tests reading between the lines, tone, register, and pragmatic competence.
Example: "Your boss emails: 'Going forward, let's loop in the whole team.' What is the pragmatic implication?"

## Rules

1. Each quiz MUST have exactly 4 options.
2. answer_index is the 0-based index of the correct option.
3. Wrong options must be PLAUSIBLE. They must represent real confusions, not absurd fillers. Whenever possible, derive distractors from other cards in the pool.
4. All questions must be written in English.
5. Explanations must be concise, useful, and teach something the learner can retain. If relevant, mention the Portuguese interference or the common mistake.
6. Each quiz must include a "used_cards" field: an array of 1-based card indices from the pool that were used to build that quiz. This lets the system trace the source.
6b. Each quiz must include a "source_expression" field: the expression the quiz is anchored on, copied VERBATIM from the Front of one of the cards you listed in used_cards. Copy it exactly as written there — do not conjugate it, translate it, or rephrase it. The quiz itself should test a VARIATION of that expression (another sense, a derived form, a different particle, a different register); the anchor names where it came from, not what is being tested.
7. Vary quiz types. Do not use the same type for consecutive quizzes.
8. You may combine concepts from multiple cards in a single quiz.
9. Prioritize concepts that have nuances, polysemy, or structural patterns over simple vocabulary.

## Output Format

Return a JSON object:
{{
  "quizzes": [
    {{
      "quiz_type": "discrimination | production | interference | polysemy | contextual",
      "concept": "Brief label of the concept being tested",
      "source_expression": "the expression copied verbatim from a card's Front",
      "question": "The question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer_index": 0,
      "explanation": "Why the answer is correct. Mention traps or common errors if applicable.",
      "used_cards": [1, 3]
    }}
  ]
}}

## Card Pool

{cards_block}

Generate exactly {n} quizzes. Output ONLY valid JSON, no markdown fences."""


def build_cloze_prompt(cards: list[tuple[str, str]], n: int) -> str:
    """Builds the prompt for cloze (fill-in-the-blank) exercises."""
    cards_block = _format_cards_block(cards)

    return f"""You are generating fill-in-the-blank exercises for an intermediate-to-advanced English learner whose native language is Brazilian Portuguese.

You will receive a pool of {len(cards)} flashcards from the learner's Anki deck. These cards were mined from varied sources — movies, TV series, articles, books, conversations. Because of this, some expressions may be highly context-specific, archaic, or uncommon in everyday English.

Your job is to generate exactly {n} cloze exercises. Each exercise presents a sentence with one blank (marked as _____) that the learner must fill in by producing the correct expression from memory — without any options to choose from.

## For each exercise:

1. Pick a concept from the card pool (phrasal verb, idiom, collocation, or structurally interesting expression).
2. Write a sentence that uses that concept naturally, replacing it with _____. The sentence must create a DIFFERENT context from the original card — do not reuse the same scenario.
3. Provide the target_expression: the exact expected answer.
4. List 1-3 acceptable_alternatives: genuinely valid substitutions in this specific sentence context, not loose synonyms.
5. Write a hint that nudges toward the answer without giving it away (e.g., "Think of a phrasal verb meaning 'to accommodate oneself'" — NOT "starts with 's'").
6. Rate the commonality of the target expression:
   - "common": used regularly in everyday spoken/written English
   - "moderate": recognized and used, but not frequent in casual conversation
   - "niche": context-specific, literary, regional, slang, or specialized usage
7. Write a context_note: If the expression is moderate or niche, briefly explain WHY (e.g., "This usage of 'camp' appears mainly in political/media contexts" or "Common in legal English but rare in casual speech"). Leave empty for common expressions.
8. Write an explanation that teaches something about the expression — its nuance, common mistakes by Portuguese speakers, or why the alternatives also work.
9. Include used_cards: array of 1-based card indices from the pool that were used.

## Rules:
- The blank must target a SINGLE meaningful expression — not a generic word like "the" or "very".
- Sentences must sound natural, not contrived to force the expression in.
- Acceptable alternatives must be genuinely interchangeable in the given sentence without changing the core meaning significantly.
- Be HONEST in commonality ratings. Do not inflate niche expressions to "common". The learner mines content from TV series and movies — some of that material is colloquial, character-specific, or stylized. Flag it.
- context_note must be genuinely informative when the expression is not "common".
- The hint should be useful but not a giveaway.
- Prioritize expressions that have nuance, structural patterns, or are prone to Portuguese interference.

## Output Format

Return a JSON object:
{{
  "exercises": [
    {{
      "concept": "Brief label of the concept",
      "sentence": "She decided to _____ the project after months of frustration.",
      "target_expression": "give up on",
      "acceptable_alternatives": ["abandon", "walk away from"],
      "hint": "A common phrasal verb meaning to stop trying",
      "commonality": "common",
      "context_note": "",
      "explanation": "'Give up on' means to stop trying to achieve or improve something...",
      "used_cards": [2, 5]
    }}
  ]
}}

## Card Pool

{cards_block}

Generate exactly {n} exercises. Output ONLY valid JSON, no markdown fences."""
