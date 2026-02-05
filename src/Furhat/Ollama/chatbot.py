import asyncio
import logging
import os
import re
from typing import Generator

import ollama

try:
    from . import config
except ImportError:
    import config

logger = logging.getLogger(__name__)

system_prompt: str | None = None
_chat_model_ok: set[str] = set()
MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "120"))


def check_for_model(model: str) -> None:
    response = ollama.list()
    models = getattr(response, "models", None)
    if models is None:
        models = response.model_dump().get("models", [])
    installed_models = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("model")
        else:
            name = getattr(item, "model", None)
        if name:
            installed_models.append(name)
    if model in installed_models:
        return

    logger.info("Model %s not found locally; pulling...", model)
    try:
        ollama.pull(model)
    except ollama.ResponseError:
        logger.exception(
            "Failed to download model %s. Check connectivity or model name.", model
        )
        raise


client = ollama.Client()
messages: list[dict[str, str]] = []
current_model: str = config.DEFAULT_MODEL
current_temperature: float = config.DEFAULT_TEMPERATURE


def set_model(model: str) -> None:
    model = model.strip()
    if not model:
        raise ValueError("Model name cannot be empty.")
    check_for_model(model)
    _validate_chat_model(model)
    global current_model
    current_model = model


def get_model() -> str:
    return current_model


def set_temperature(value: float) -> None:
    if value <= 0:
        raise ValueError("Temperature must be > 0.")
    global current_temperature
    current_temperature = float(value)


def get_temperature() -> float:
    return current_temperature


def list_models() -> list[str]:
    response = ollama.list()
    models = getattr(response, "models", None)
    if models is None:
        models = response.model_dump().get("models", [])
    names: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("model")
        else:
            name = getattr(item, "model", None)
        if name:
            names.append(name)
    return names


def _validate_chat_model(model: str) -> None:
    if model in _chat_model_ok:
        return
    try:
        client.chat(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            stream=False,
            options={"num_predict": 1},
        )
    except ollama.ResponseError as exc:
        message = str(exc).lower()
        if "does not support chat" in message:
            raise ValueError(
                f"Model '{model}' does not support chat. Please select a chat model."
            ) from exc
        raise
    _chat_model_ok.add(model)


def clear_messages() -> None:
    messages.clear()
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})


def set_system_prompt(prompt: str) -> None:
    global system_prompt
    prompt = prompt.strip()
    system_prompt = prompt or None
    _ensure_system_prompt()


def _ensure_system_prompt() -> None:
    if not system_prompt:
        return
    non_system = [m for m in messages if m.get("role") != "system"]
    messages[:] = [{"role": "system", "content": system_prompt}, *non_system]


async def get_full_response(prompt: str) -> str:
    # Offload the heavy network call to a background thread
    return await asyncio.to_thread(_sync_get_full_response, prompt)

def _sync_get_full_response(prompt: str) -> str:
    _ensure_system_prompt()
    _validate_chat_model(current_model)
    messages.append({"role": "user", "content": prompt})
    stream = client.chat(
        model=current_model,
        messages=messages,
        stream=False,
        options={"temperature": current_temperature, "num_predict": MAX_TOKENS},
    )
    response = stream.message.content
    if response:
        messages.append({"role": "assistant", "content": response})
    return response


def get_response_by_token(prompt: str) -> Generator[str, None, None]:
    """
    Stream each token from the current Ollama model.

    :param prompt: the message from the user
    :type prompt: str
    :return: Generator of every token
    :rtype: Generator[str, None, None]
    """
    _ensure_system_prompt()
    _validate_chat_model(current_model)
    messages.append({"role": "user", "content": prompt})
    full_response: str = ""
    stream = client.chat(
        model=current_model,
        messages=messages,
        stream=True,
        options={"temperature": current_temperature, "num_predict": MAX_TOKENS},
    )

    for chunk in stream:
        if "message" in chunk and "content" in chunk["message"]:
            token = chunk["message"]["content"]
            full_response += token
            yield token

    if full_response:
        messages.append({"role": "assistant", "content": full_response})


def get_response_by_regex(prompt: str, regex: str) -> Generator[str, None, None]:
    """
    Modification of get_response_by_token(), to split up the generation into
    easier sections of text for furhat.
    
    :param prompt: the message from the user
    :type prompt: str
    :param regex: A regex to split send_token()
    :type regex: str
    :rtype: Generator[str, None. None]
    """
    buffer = ""
    for token in get_response_by_token(prompt):
        buffer += token
        match = re.search(regex, buffer)
        while match:
            end_index = match.end()
            sentence = buffer[:end_index]
            yield sentence
            buffer = buffer[end_index:]

            match = re.search(regex, buffer)

    if buffer:
        yield re.sub(r"[^a-zA-Z0-9]", "", buffer)


def get_response_by_punctuation(prompt: str) -> Generator[str, None, None]:
    return get_response_by_regex(prompt, r"(?<=[.!?])\s+")

