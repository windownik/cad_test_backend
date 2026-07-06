"""Настройки подключения к Roboflow Inference API."""

from __future__ import annotations

import os

ROBOFLOW_API_URL: str = os.getenv("ROBOFLOW_API_URL", "https://detect.roboflow.com")
ROBOFLOW_API_KEY: str = os.getenv("ROBOFLOW_API_KEY", "a1hnc0z8nDNRQH6OAmfy")
ROBOFLOW_MODEL_ID: str = os.getenv("ROBOFLOW_MODEL_ID", "")


def require_roboflow_credentials() -> tuple[str, str]:
    """Возвращает API-ключ и ID модели или выбрасывает понятную ошибку."""
    if not ROBOFLOW_API_KEY:
        raise ValueError(
            "Не задан ROBOFLOW_API_KEY. Установите переменную окружения "
            "или пропишите ключ в lib/roboflow/config.py."
        )

    if not ROBOFLOW_MODEL_ID:
        raise ValueError(
            "Не задан ROBOFLOW_MODEL_ID. Укажите model_id с сайта Roboflow "
            "(например, 'project-name/1')."
        )
    return ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID
