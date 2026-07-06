"""Запросы к Roboflow Inference API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lib.common.logging_config import logger
from lib.roboflow.config import ROBOFLOW_API_URL, require_roboflow_credentials
from lib.roboflow.types import RoboflowResponse


class RoboflowAPIError(RuntimeError):
    """Ошибка при обращении к Roboflow Inference API."""


def get_api_predictions(
    png_path: str | Path,
    *,
    api_key: str | None = None,
    model_id: str | None = None,
    api_url: str = ROBOFLOW_API_URL,
) -> RoboflowResponse:
    """
    Отправляет PNG в Roboflow API и возвращает JSON с предсказаниями.

    Args:
        png_path: Путь к PNG-изображению плана.
        api_key: API-ключ Roboflow. По умолчанию — из переменной окружения.
        model_id: ID модели (например, 'floor-plan/3'). По умолчанию — из env.
        api_url: URL Inference API (по умолчанию https://detect.roboflow.com).

    Returns:
        Словарь ответа API с ключом ``predictions``.

    Raises:
        FileNotFoundError: PNG не найден.
        RoboflowAPIError: API вернуло ошибку или недоступно.
        ValueError: Не заданы учётные данные.
    """
    image_path = Path(png_path).expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"PNG не найден: {image_path}")

    default_key, default_model = require_roboflow_credentials()
    resolved_key = api_key or default_key
    resolved_model = model_id or default_model

    try:
        from inference_sdk import InferenceHTTPClient
    except ImportError as exc:
        raise ImportError(
            "Пакет inference-sdk не установлен. Выполните: pip install inference-sdk"
        ) from exc

    client = InferenceHTTPClient(api_url=api_url, api_key=resolved_key)

    try:
        result: dict[str, Any] = client.infer(str(image_path), model_id=resolved_model)
    except Exception as exc:
        raise RoboflowAPIError(f"Roboflow API вернуло ошибку: {exc}") from exc

    if not isinstance(result, dict):
        raise RoboflowAPIError(f"Неожиданный формат ответа API: {type(result)!r}")

    predictions = result.get("predictions")
    if predictions is None:
        raise RoboflowAPIError("В ответе API отсутствует ключ 'predictions'.")

    logger.info(
        "Roboflow: получено предсказаний — %d (модель %s)",
        len(predictions),
        resolved_model,
    )
    return RoboflowResponse(predictions=predictions, image=result.get("image", {}))
