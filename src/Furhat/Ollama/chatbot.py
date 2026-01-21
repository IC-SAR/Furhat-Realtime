import logging

import ollama

from . import config

logger = logging.getLogger(__name__)


def check_for_model(model: str) -> None:
    response = ollama.list()
    installed_models = [item["model"] for item in response["models"]]
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
check_for_model(current_model)


def set_model(model: str) -> None:
    model = model.strip()
    if not model:
        raise ValueError("Model name cannot be empty.")
    check_for_model(model)
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
    return [item["model"] for item in response.get("models", [])]


def clear_messages() -> None:
    messages.clear()

