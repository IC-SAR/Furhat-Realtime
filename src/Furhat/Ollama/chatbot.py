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
RECOMMENDED_REMOTE_CHAT_MODELS = ("openai/gpt-5-mini", "openai/gpt-4.1-mini")
UNSUPPORTED_EXTERNAL_CHAT_MODEL_PATTERNS = (
    re.compile(r"(?:^|/)(?:o1|o3|o4)(?:[-_].*|$)", re.IGNORECASE),
)

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
last_completion_info: dict[str, object] = {
    "provider": PROVIDER_OLLAMA,
    "model": current_model,
    "finish_reason": "",
    "truncated": False,
}


def configure_chat_settings(
    *,
    max_tokens: int | None = None,
    max_history_messages: int | None = None,
    max_history_chars: int | None = None,
    external_api_timeout: float | None = None,
) -> None:
    global EXTERNAL_API_TIMEOUT, MAX_TOKENS, MAX_HISTORY_MESSAGES, MAX_HISTORY_CHARS
    if max_tokens is not None:
        MAX_TOKENS = int(max_tokens)
    if max_history_messages is not None:
        MAX_HISTORY_MESSAGES = int(max_history_messages)
    if max_history_chars is not None:
        MAX_HISTORY_CHARS = int(max_history_chars)
    if external_api_timeout is not None:
        EXTERNAL_API_TIMEOUT = float(external_api_timeout)


def get_chat_settings() -> dict[str, float | int]:
    return {
        "max_tokens": MAX_TOKENS,
        "max_history_messages": MAX_HISTORY_MESSAGES,
        "max_history_chars": MAX_HISTORY_CHARS,
        "external_api_timeout": EXTERNAL_API_TIMEOUT,
    }


def get_last_completion_info() -> dict[str, object]:
    return dict(last_completion_info)


def _set_last_completion_info(*, finish_reason: str = "", truncated: bool = False) -> None:
    global last_completion_info
    last_completion_info = {
        "provider": current_provider,
        "model": current_model,
        "finish_reason": finish_reason,
        "truncated": bool(truncated),
    }


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


def _external_stream_events(payload: dict[str, object]) -> Generator[dict[str, object], None, None]:
    url = f"{_effective_api_base_url()}/chat/completions"
    body = json.dumps(payload).encode("utf-8")
    headers = _external_headers()
    headers["Accept"] = "text/event-stream"
    request = urlrequest.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urlrequest.urlopen(request, timeout=EXTERNAL_API_TIMEOUT) as response:
            event_lines: list[str] = []
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if not line:
                    if not event_lines:
                        continue
                    data_lines = []
                    for event_line in event_lines:
                        if event_line.startswith("data:"):
                            data_lines.append(event_line[5:].lstrip())
                    event_lines.clear()
                    if not data_lines:
                        continue
                    payload_text = "\n".join(data_lines).strip()
                    if payload_text == "[DONE]":
                        break
                    try:
                        data = json.loads(payload_text)
                    except json.JSONDecodeError as exc:
                        raise RuntimeError("External API returned invalid streamed JSON.") from exc
                    if not isinstance(data, dict):
                        raise RuntimeError("External API returned an unexpected streamed response.")
                    yield data
                    continue
                event_lines.append(line)
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"External API HTTP {exc.code}: {detail or exc.reason}") from exc
    except urlerror.URLError as exc:
        raise RuntimeError(f"External API request failed: {exc.reason}") from exc


def _unsupported_remote_model_message(model: str) -> str:
    recommended = " or ".join(RECOMMENDED_REMOTE_CHAT_MODELS)
    return f"Unsupported remote model for speech: {model}. Use {recommended}."


def _is_unsupported_external_chat_model(model: str) -> bool:
    value = str(model).strip()
    if not value:
        return False
    return any(pattern.search(value) for pattern in UNSUPPORTED_EXTERNAL_CHAT_MODEL_PATTERNS)


def _extract_external_text(data: dict[str, object]) -> str:
    error_payload = data.get("error")
    if isinstance(error_payload, dict):
        message_value = error_payload.get("message")
        code_value = error_payload.get("code")
        if isinstance(message_value, str) and message_value.strip():
            if isinstance(code_value, str) and code_value.strip():
                raise RuntimeError(f"External API error ({code_value}): {message_value.strip()}")
            raise RuntimeError(f"External API error: {message_value.strip()}")
        raise RuntimeError(f"External API error: {error_payload}")
    if isinstance(error_payload, str) and error_payload.strip():
        raise RuntimeError(f"External API error: {error_payload.strip()}")

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        keys = ", ".join(sorted(str(key) for key in data.keys())) or "<none>"
        raise RuntimeError(f"External API response missing choices. Top-level keys: {keys}.")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("External API response choice is invalid.")
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("External API response missing message.")
    content = message.get("content", "")
    if isinstance(content, str):
        content = content.strip()
        if content:
            return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value)
        merged = "\n".join(parts).strip()
        if merged:
            return merged

    reasoning_value = message.get("reasoning")
    reasoning_details = message.get("reasoning_details")
    if (
        (isinstance(reasoning_value, str) and reasoning_value.strip())
        or (isinstance(reasoning_details, list) and len(reasoning_details) > 0)
    ):
        raise RuntimeError(
            f"{_unsupported_remote_model_message(current_model)} "
            "The provider returned reasoning output without assistant text."
        )

    raise RuntimeError("External API response missing assistant text.")


def _extract_external_finish_reason(data: dict[str, object]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    value = first.get("finish_reason")
    return value.strip() if isinstance(value, str) else ""


def _extract_external_stream_delta(data: dict[str, object]) -> tuple[str, str]:
    error_payload = data.get("error")
    if isinstance(error_payload, dict):
        message_value = error_payload.get("message")
        if isinstance(message_value, str) and message_value.strip():
            raise RuntimeError(f"External API error: {message_value.strip()}")
        raise RuntimeError(f"External API error: {error_payload}")
    if isinstance(error_payload, str) and error_payload.strip():
        raise RuntimeError(f"External API error: {error_payload.strip()}")

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return "", ""
    first = choices[0]
    if not isinstance(first, dict):
        return "", ""
    finish_reason = first.get("finish_reason")
    normalized_finish = finish_reason.strip() if isinstance(finish_reason, str) else ""
    delta = first.get("delta")
    if not isinstance(delta, dict):
        return "", normalized_finish
    content = delta.get("content")
    if isinstance(content, str):
        return content, normalized_finish
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    parts.append(text_value)
        return "".join(parts), normalized_finish
    return "", normalized_finish


def _extract_ollama_finish_reason(response: object) -> str:
    for attr_name in ("done_reason", "finish_reason"):
        value = getattr(response, attr_name, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if hasattr(response, "model_dump"):
        try:
            payload = response.model_dump()
        except Exception:
            payload = None
        if isinstance(payload, dict):
            for key in ("done_reason", "finish_reason"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    if isinstance(response, dict):
        for key in ("done_reason", "finish_reason"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _log_if_completion_truncated(*, finish_reason: str) -> None:
    normalized = str(finish_reason).strip().lower()
    truncated = normalized in {"length", "max_tokens"}
    _set_last_completion_info(finish_reason=finish_reason, truncated=truncated)
    if truncated:
        logger.warning(
            "LLM output hit max token limit: provider=%s model=%s max_tokens=%s finish_reason=%s",
            current_provider,
            current_model,
            MAX_TOKENS,
            finish_reason,
        )


def _rollback_last_user_message(prompt: str) -> None:
    if not messages:
        return
    last_message = messages[-1]
    if (
        isinstance(last_message, dict)
        and last_message.get("role") == "user"
        and last_message.get("content") == prompt
    ):
        messages.pop()


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
        check_for_model(model)
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
        if _is_unsupported_external_chat_model(model):
            raise ValueError(_unsupported_remote_model_message(model))
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
    _set_last_completion_info()
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
        _log_if_completion_truncated(finish_reason=_extract_ollama_finish_reason(stream))
    else:
        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": current_temperature,
            "max_tokens": MAX_TOKENS,
        }
        data = _external_request("chat/completions", payload=payload)
        response = _extract_external_text(data)
        _log_if_completion_truncated(finish_reason=_extract_external_finish_reason(data))

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
    _ensure_system_prompt()
    _validate_chat_model(current_model)
    _set_last_completion_info()
    messages.append({"role": "user", "content": prompt})
    _trim_history()
    full_response: str = ""
    finish_reason = ""

    if is_ollama_provider():
        stream = client.chat(
            model=current_model,
            messages=messages,
            stream=True,
            options={"temperature": current_temperature, "num_predict": MAX_TOKENS},
        )

        for chunk in stream:
            chunk_finish_reason = _extract_ollama_finish_reason(chunk)
            if chunk_finish_reason:
                finish_reason = chunk_finish_reason
            token = ""
            if isinstance(chunk, dict):
                token = str(chunk.get("message", {}).get("content", "") or "")
            elif hasattr(chunk, "message") and getattr(chunk.message, "content", None):
                token = str(chunk.message.content)
            if token:
                full_response += token
                yield token
    else:
        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": current_temperature,
            "max_tokens": MAX_TOKENS,
            "stream": True,
        }
        try:
            for event in _external_stream_events(payload):
                token, event_finish_reason = _extract_external_stream_delta(event)
                if event_finish_reason:
                    finish_reason = event_finish_reason
                if token:
                    full_response += token
                    yield token
        except Exception as exc:
            logger.info("External streaming unavailable; falling back to full response: %s", exc)
            _rollback_last_user_message(prompt)
            response = get_full_response(prompt)
            if response:
                yield response
            return

    _log_if_completion_truncated(finish_reason=finish_reason)

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

    final_chunk = buffer.strip()
    if final_chunk:
        yield final_chunk


def get_response_by_punctuation(prompt: str) -> Generator[str, None, None]:
    return get_response_by_regex(prompt, r"(?<=[.!?])\s+")
