"""Безопасная работа с сущностями DXF в modelspace."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterator

from ezdxf.entities.dxfgfx import DXFGraphic
from ezdxf.layouts import BaseLayout

from lib.cleaning.stats import CleanupStats
from lib.common.logging_config import logger


def iter_layout_entities(layout: BaseLayout) -> Iterator[DXFGraphic]:
    """Итерирует сущности пространства, пропуская повреждённые элементы."""
    for entity in layout:
        try:
            if entity.dxftype():
                yield entity
        except Exception as exc:
            logger.debug("Пропущена повреждённая сущность: %s", exc)


def query_entities_safe(layout: BaseLayout, query: str) -> list[DXFGraphic]:
    """Выполняет ezdxf-запрос, возвращая только валидные сущности."""
    result: list[DXFGraphic] = []
    try:
        for entity in layout.query(query):
            try:
                _ = entity.dxftype()
                result.append(entity)
            except Exception as exc:
                logger.debug("Повреждённый объект в запросе '%s': %s", query, exc)
    except Exception as exc:
        logger.warning("Ошибка запроса '%s': %s", query, exc)
    return result


def delete_entity_safe(layout: BaseLayout, entity: DXFGraphic, stats: CleanupStats) -> bool:
    """Удаляет сущность, не прерывая конвейер при ошибке."""
    try:
        layout.delete_entity(entity)
        return True
    except Exception as exc:
        stats.skipped_errors += 1
        logger.debug("Не удалось удалить %s: %s", entity.dxftype(), exc)
        return False


def count_entities_by_type(layout: BaseLayout) -> dict[str, int]:
    """Подсчитывает количество объектов каждого типа в пространстве модели."""
    counts: dict[str, int] = defaultdict(int)
    for entity in iter_layout_entities(layout):
        try:
            counts[entity.dxftype()] += 1
        except Exception:
            continue
    return dict(counts)
