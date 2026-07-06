"""Пересчёт координат Roboflow (центр + размер) в CAD-вершины."""

from __future__ import annotations

from lib.roboflow.types import RoboflowPrediction, ScaleMeta


def prediction_center_to_pixel_box(
    prediction: RoboflowPrediction,
) -> tuple[float, float, float, float]:
    """
    Преобразует центр и размеры объекта (Roboflow) в угловые пиксельные координаты.

    Returns:
        Кортеж (x1, y1, x2, y2) в системе координат изображения (Y сверху вниз).
    """
    center_x = float(prediction["x"])
    center_y = float(prediction["y"])
    half_w = float(prediction["width"]) / 2.0
    half_h = float(prediction["height"]) / 2.0

    return (
        center_x - half_w,
        center_y - half_h,
        center_x + half_w,
        center_y + half_h,
    )


def pixel_box_to_cad_vertices(
    px1: float,
    py1: float,
    px2: float,
    py2: float,
    scale_meta: ScaleMeta,
    *,
    image_width_px: int,
    image_height_px: int,
) -> list[tuple[float, float]]:
    """
    Пересчитывает пиксельный bbox в четыре вершины прямоугольника в CAD.

    Ось Y инвертируется: в изображении Y растёт сверху вниз, в CAD — снизу вверх.
    """
    if image_width_px <= 0 or image_height_px <= 0:
        raise ValueError("Размеры изображения должны быть положительными.")

    x_min = scale_meta["x_min"]
    y_min = scale_meta["y_min"]
    cad_width = scale_meta["cad_width"]
    cad_height = scale_meta["cad_height"]

    cad_x1 = x_min + (px1 / image_width_px) * cad_width
    cad_x2 = x_min + (px2 / image_width_px) * cad_width
    cad_y1 = y_min + ((image_height_px - py1) / image_height_px) * cad_height
    cad_y2 = y_min + ((image_height_px - py2) / image_height_px) * cad_height

    return [
        (cad_x1, cad_y1),
        (cad_x2, cad_y1),
        (cad_x2, cad_y2),
        (cad_x1, cad_y2),
    ]


def prediction_to_cad_vertices(
    prediction: RoboflowPrediction,
    scale_meta: ScaleMeta,
    *,
    image_width_px: int,
    image_height_px: int,
) -> list[tuple[float, float]]:
    """Полный пересчёт одного предсказания Roboflow в CAD-вершины."""
    px1, py1, px2, py2 = prediction_center_to_pixel_box(prediction)
    return pixel_box_to_cad_vertices(
        px1,
        py1,
        px2,
        py2,
        scale_meta,
        image_width_px=image_width_px,
        image_height_px=image_height_px,
    )
