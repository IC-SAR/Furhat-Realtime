from __future__ import annotations

import textwrap
from collections.abc import Mapping


BASE_GUARDRAILS = textwrap.dedent(
    """
    You are speaking through a Furhat robot.
    Keep responses short, natural, and conversational.
    Avoid bullet lists unless the user explicitly asks for one.
    Use clear language and explain jargon briefly when needed.
    If the request is unclear, ask a short clarifying question.
    Only use information from the supplied context and the active character instructions.
    Do not invent facts, locations, time of day, current events, or scene details.
    If the answer is not supported by the available context, say you are not sure and direct the visitor to staff.
    """
).strip()


def _coerce_character_info(character_info: object) -> dict[str, str]:
    if isinstance(character_info, Mapping):
        return {
            str(key): str(value)
            for key, value in character_info.items()
            if value is not None
        }
    if hasattr(character_info, "to_dict"):
        payload = getattr(character_info, "to_dict")()
        if isinstance(payload, Mapping):
            return {
                str(key): str(value)
                for key, value in payload.items()
                if value is not None
            }
    return {}


def build_system_prompt(character_info: object) -> str:
    info = _coerce_character_info(character_info)
    character_name = info.get("name", "").strip()
    agent_name = info.get("agent_name", "").strip() or character_name
    description = info.get("description", "").strip()

    sections = [BASE_GUARDRAILS]
    if agent_name:
        sections.append(f"You are currently portraying the character {agent_name}.")
    if character_name and character_name != agent_name:
        sections.append(f"The character profile title is {character_name}.")
    if description:
        sections.append(f"Character role and scope: {description}")

    return "\n\n".join(section for section in sections if section).strip()
