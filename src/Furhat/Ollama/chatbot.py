from __future__ import annotations

import json
import logging
import os
import re
from typing import Generator
from urllib import error as urlerror
from urllib import request as urlrequest

import ollama

from . import config

logger = logging.getLogger(__name__)

PROVIDER_OLLAMA = "ollama"
PROVIDER_OPENAI_COMPATIBLE = "openai_compatible"
SUPPORTED_PROVIDERS = (PROVIDER_OLLAMA, PROVIDER_OPENAI_COMPATIBLE)
PROVIDER_LABELS = {
    PROVIDER_OLLAMA: "Ollama",
    PROVIDER_OPENAI_COMPATIBLE: "External API",
}
DEFAULT_EXTERNAL_API_BASE_URL = "https://api.openai.com/v1"
EXTERNAL_API_TIMEOUT = float(os.getenv("EXTERNAL_API_TIMEOUT", "30"))

system_prompt: str | None = None
_chat_model_ok: set[tuple[str, str]] = set()
MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "120"))
MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "16"))
MAX_HISTORY_CHARS = int(os.getenv("CHAT_MAX_HISTORY_CHARS", "8000"))

client = ollama.Client()
messages: list[dict[str, str]] = []
current_provider: str = PROVIDER_OLLAMA
current_model: str = config.DEFAULT_MODEL
current_temperature: float = config.DEFAULT_TEMPERATURE
current_api_base_url: str = ""
current_api_key: str = ""


def _normalize_provider(provider: str) -> str:
    value = str(provider).strip().lower() or PROVIDER_OLLAMA
    if value not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported provider '{provider}'. Choose one of: {', '.join(SUPPORTED_PROVIDERS)}."
        )
    return value


def get_provider_options() -> tuple[str, ...]:
    return SUPPORTED_PROVIDERS


def get_provider() -> str:
    return current_provider


def get_provider_label(provider: str | None = None) -> str:
    key = _normalize_provider(provider or current_provider)
    return PROVIDER_LABELS.get(key, key)


def is_ollama_provider() -> bool:
    return current_provider == PROVIDER_OLLAMA


def set_provider(provider: str) -> None:
    global current_provider
    current_provider = _normalize_provider(provider)


def get_api_base_url() -> str:
    return current_api_base_url


def set_api_base_url(value: str) -> None:
    global current_api_base_url
    current_api_base_url = str(value).strip().rstrip("/")


def get_api_key() -> str:
    return current_api_key


def set_api_key(value: str) -> None:
    global current_api_key
    current_api_key = str(value).strip()


def _effective_api_base_url() -> str:
    base_url = current_api_base_url.strip().rstrip("/")
    if base_url:
        return base_url
    return DEFAULT_EXTERNAL_API_BASE_URL


def _effective_api_key() -> str:
    return (
        current_api_key.strip()
        or os.getenv("LLM_API_KEY", "").strip()
        or os.getenv("OPENAI_API_KEY", "").strip()
    )


def _require_api_key() -> str:
    api_key = _effective_api_key()
    if not api_key:
        raise ValueError(
            "External API key is required. Set it in Settings or via LLM_API_KEY / OPENAI_API_KEY."
        )
    return api_key


def _external_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_require_api_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Furhat-Realtime/0.2",
    }


def _external_request(path: str, *, payload: dict[str, object] | None = None) -> dict[str, object]:
    url = f"{_effective_api_base_url()}/{path.lstrip('/')}"
    body = None
    method = "GET"
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        method = "POST"
    request = urlrequest.Request(
        url,
        data=body,
        headers=_external_headers(),
        method=method,
    )
    try:
        with urlrequest.urlopen(request, timeout=EXTERNAL_API_TIMEOUT) as response:
            raw = response.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"External API HTTP {exc.code}: {detail or exc.reason}") from exc
    except urlerror.URLError as exc:
        raise RuntimeError(f"External API request failed: {exc.reason}") from exc

    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("External API returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("External API returned an unexpected response shape.")
    return data


def _extract_external_text(data: dict[str, object]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("External API response missing choices.")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("External API response choice is invalid.")
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("External API response missing message.")
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value)
        return "\n".join(parts).strip()
    return ""


def check_for_model(model: str) -> None:
    if not is_ollama_provider():
        return

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


def set_model(model: str) -> None:
    model = model.strip()
    if not model:
        raise ValueError("Model name cannot be empty.")
    if is_ollama_provider():
        check_for_model(model)
        _validate_chat_model(model)
    global current_model
    current_model = model


def get_model() -> str:
    return current_model


def load_saved_settings(
    model: str,
    temperature: float,
    provider: str = PROVIDER_OLLAMA,
    api_base_url: str = "",
    api_key: str = "",
) -> None:
    global current_model
    global current_temperature
    set_provider(provider)
    set_api_base_url(api_base_url)
    set_api_key(api_key)
    model = model.strip()
    if model:
        current_model = model
    current_temperature = float(temperature)


def set_temperature(value: float) -> None:
    if value <= 0:
        raise ValueError("Temperature must be > 0.")
    global current_temperature
    current_temperature = float(value)


def get_temperature() -> float:
    return current_temperature


def list_models() -> list[str]:
    if is_ollama_provider():
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

    data = _external_request("models")
    items = data.get("data", [])
    if not isinstance(items, list):
        raise RuntimeError("External API models response missing data list.")
    names: list[str] = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("id")
            if isinstance(name, str) and name.strip():
                names.append(name.strip())
    return names


def _validate_chat_model(model: str) -> None:
    cache_key = (current_provider, model)
    if cache_key in _chat_model_ok:
        return

    if is_ollama_provider():
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
    else:
        available = list_models()
        if available and model not in available:
            raise ValueError(
                f"Model '{model}' was not returned by the external API models endpoint."
            )

    _chat_model_ok.add(cache_key)


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


def _trim_history() -> None:
    if MAX_HISTORY_MESSAGES > 0 and len(messages) > MAX_HISTORY_MESSAGES:
        system = [m for m in messages if m.get("role") == "system"]
        rest = [m for m in messages if m.get("role") != "system"]
        messages[:] = system + rest[-MAX_HISTORY_MESSAGES:]

    if MAX_HISTORY_CHARS > 0:
        system = [m for m in messages if m.get("role") == "system"]
        rest = [m for m in messages if m.get("role") != "system"]
        total_chars = sum(len(m.get("content", "")) for m in rest)
        while rest and total_chars > MAX_HISTORY_CHARS:
            removed = rest.pop(0)
            total_chars -= len(removed.get("content", ""))
        messages[:] = system + rest


def get_full_response(prompt: str) -> str:
    _ensure_system_prompt()
    _validate_chat_model(current_model)
    messages.append({"role": "user", "content": prompt})
    _trim_history()

    if is_ollama_provider():
        stream = client.chat(
            model=current_model,
            messages=messages,
            stream=False,
            options={"temperature": current_temperature, "num_predict": MAX_TOKENS},
        )
        response = stream.message.content
    else:
        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": current_temperature,
            "max_tokens": MAX_TOKENS,
        }
        response = _extract_external_text(_external_request("chat/completions", payload=payload))

    if response:
        messages.append({"role": "assistant", "content": response})
        _trim_history()
    return response


def get_response_by_token(prompt: str) -> Generator[str, None, None]:
    """
    Stream each token from the current model.

    :param prompt: the message from the user
    :type prompt: str
    :return: Generator of every token
    :rtype: Generator[str, None, None]
    """
    if not is_ollama_provider():
        response = get_full_response(prompt)
        if response:
            yield response
        return

    _ensure_system_prompt()
    _validate_chat_model(current_model)
    messages.append({"role": "user", "content": prompt})
    _trim_history()
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
        _trim_history()


def get_response_by_regex(prompt: str, regex: str) -> Generator[str, None, None]:
    """
    Modification of get_response_by_token(), to split up the generation into
    easier sections of text for furhat.

    :param prompt: the message from the user
    :type prompt: str
    :param regex: A regex to split send_token()
    :type regex: str
    :rtype: Generator[str, None, None]
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
