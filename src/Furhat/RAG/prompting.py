from __future__ import annotations


def build_prompt(user_prompt: str, context: str) -> str:
    context_value = context.strip()
    question_value = user_prompt.strip()
    return (
        "Answer the visitor using only the active character instructions and any grounded context below.\n"
        "Do not invent facts, locations, time of day, current events, or scene details.\n"
        "If you do not have enough grounded information to answer, say you are not sure and direct the visitor to staff.\n"
        "Keep the answer short and conversational.\n\n"
        f"Grounded context:\n{context_value or '<none>'}\n\n"
        f"User question: {question_value}"
    )
