"""Пересчёт координат между пикселями PNG и CAD-моделью DXF."""

from __future__ import annotations

from lib.converter.png_export import PngExportMeta


def pixel_box_to_cad_vertices(
    px1: float,
    py1: float,
    px2: float,
    py2: float,
    meta: PngExportMeta,
    *,
    image_width_px: int,
    image_height_px: int,
) -> list[tuple[float, float]]:
    """
    Преобразует bounding box YOLO (пиксели, Y сверху вниз) в вершины
    прямоугольника в CAD-координатах (Y снизу вверх).
    """
    if image_width_px <= 0 or image_height_px <= 0:
        raise ValueError("Размеры изображения должны быть положительными.")

    cad_x1 = meta["x_min"] + (px1 / image_width_px) * meta["cad_width"]
    cad_x2 = meta["x_min"] + (px2 / image_width_px) * meta["cad_width"]
    cad_y1 = meta["y_min"] + ((image_height_px - py1) / image_height_px) * meta["cad_height"]
    cad_y2 = meta["y_min"] + ((image_height_px - py2) / image_height_px) * meta["cad_height"]

    return [
        (cad_x1, cad_y1),
        (cad_x2, cad_y1),
        (cad_x2, cad_y2),
        (cad_x1, cad_y2),
    ]
