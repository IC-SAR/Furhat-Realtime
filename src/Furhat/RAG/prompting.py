from __future__ import annotations


def build_prompt(user_prompt: str, context: str) -> str:
    if not context.strip():
        return user_prompt
    return f"Context:\\n{context}\\n\\nUser question: {user_prompt}"
