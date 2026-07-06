"""Типы данных для интеграции с Roboflow API."""

from __future__ import annotations

from typing import Any, TypedDict


class ScaleMeta(TypedDict):
    """Метаданные масштаба для пересчёта пикселей в CAD-координаты."""

    x_min: float
    y_min: float
    cad_width: float
    cad_height: float


class RoboflowPrediction(TypedDict, total=False):
    """Одно предсказание из ответа Roboflow API."""

    x: float
    y: float
    width: float
    height: float
    class_id: int
    confidence: float
    # Ключ "class" в JSON Roboflow — строковое имя класса (window/door/wall).


class RoboflowResponse(TypedDict, total=False):
    """Ответ Roboflow Inference API."""

    predictions: list[dict[str, Any]]
    image: dict[str, Any]


CLASS_LAYER_CONFIG: dict[str, tuple[str, int]] = {
    "wall": ("AI_WALLS", 9),
    "window": ("AI_WINDOWS", 5),
    "door": ("AI_DOORS", 1),
}
