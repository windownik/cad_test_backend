"""Геометрические утилиты для анализа DXF-сущностей."""

from __future__ import annotations

import math

from ezdxf.entities.dxfgfx import DXFGraphic

from lib.cleaning.constants import ARROW_SOLID_MAX_AREA, DASHED_LINETYPE_KEYWORDS, HATCH_LINE_MAX_SPACING, HATCH_LINE_SPACING_TOLERANCE


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def line_length(entity: DXFGraphic) -> float:
    """Вычисляет длину LINE-сущности."""
    start = entity.dxf.start
    end = entity.dxf.end
    return distance(start.x, start.y, end.x, end.y)


def line_angle_rad(entity: DXFGraphic) -> float:
    """Возвращает угол линии в радианах в диапазоне [0, π)."""
    dx = entity.dxf.end.x - entity.dxf.start.x
    dy = entity.dxf.end.y - entity.dxf.start.y
    return math.atan2(dy, dx) % math.pi


def line_perpendicular_offset(entity: DXFGraphic, angle: float) -> float:
    """Расстояние от начала координат до середины линии вдоль нормали."""
    mx = (entity.dxf.start.x + entity.dxf.end.x) / 2.0
    my = (entity.dxf.start.y + entity.dxf.end.y) / 2.0
    nx = -math.sin(angle)
    ny = math.cos(angle)
    return mx * nx + my * ny


def solid_triangle_area(entity: DXFGraphic) -> float:
    """
    Вычисляет площадь SOLID/TRACE, трактуя объект как треугольник или четырёхугольник.
    Возвращает 0 при ошибке чтения вершин.
    """
    points: list[tuple[float, float]] = []
    for index in range(4):
        try:
            vertex = entity.dxf.get(f"vtx{index}")
            if vertex is None:
                continue
            point = (float(vertex.x), float(vertex.y))
            if point not in points:
                points.append(point)
        except Exception:
            continue

    if len(points) < 3:
        return 0.0

    area = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def is_small_arrow_solid(entity: DXFGraphic) -> bool:
    """Проверяет, является ли SOLID/TRACE маленькой заливкой-стрелкой."""
    try:
        area = solid_triangle_area(entity)
        return 0.0 < area <= ARROW_SOLID_MAX_AREA
    except Exception:
        return False


def spacing_is_uniform(spacings: list[float]) -> bool:
    """Проверяет, что промежутки между линиями примерно одинаковы."""
    if len(spacings) < 2:
        return True
    avg = sum(spacings) / len(spacings)
    if avg <= 0 or avg > HATCH_LINE_MAX_SPACING:
        return False
    tolerance = avg * HATCH_LINE_SPACING_TOLERANCE
    return all(abs(value - avg) <= tolerance for value in spacings)


def is_dashed_linetype(linetype_name: str, layer_linetype: str = "Continuous") -> bool:
    """
    Определяет, является ли тип линии пунктирным.
    Учитывает ByLayer — смотрит тип линии, назначенный слою.
    """
    name = linetype_name.strip()
    upper = name.upper()

    if upper == "BYBLOCK":
        return False
    if upper == "BYLAYER":
        return is_dashed_linetype(layer_linetype)
    if upper == "CONTINUOUS":
        return False

    lower = name.lower()
    return any(keyword in lower for keyword in DASHED_LINETYPE_KEYWORDS)
