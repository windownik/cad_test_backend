"""Основной класс конвейера очистки DXF-чертежа."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.document import Drawing
from ezdxf.entities.dxfgfx import DXFGraphic
from ezdxf.layouts import BaseLayout

from lib.cleaning.constants import (
    DEFAULT_AXIS_LAYERS,
    ROOM_MARKER_RADIUS_MAX,
    ROOM_MARKER_RADIUS_MIN,
    SHORT_LINE_MAX_LENGTH,
)
from lib.cleaning.entities import count_entities_by_type, delete_entity_safe, query_entities_safe
from lib.cleaning.geometry import is_dashed_linetype, is_small_arrow_solid, line_length
from lib.cleaning.hatch_detection import find_parallel_line_clusters
from lib.cleaning.metadata import load_metadata, save_metadata
from lib.cleaning.stats import CleanupStats
from lib.common.logging_config import logger


class DXFCleaner:
    """
    Конвейер поэтапной очистки DXF-чертежа.

    Каждый метод очистки независим: можно вызывать отдельно или в произвольном порядке.
    Метаданные текстов и маркеров накапливаются в JSON-файле рядом с исходником.
    """

    def __init__(
        self,
        source_path: str | Path,
        axis_layers: list[str] | tuple[str, ...] | None = None,
        *,
        remove_axis_markers: bool = True,
        remove_dashed_axes: bool = True,
    ) -> None:
        resolved = Path(source_path).expanduser().resolve()
        self.source_path: Path = resolved
        self.metadata_path: Path = resolved.with_name(f"{resolved.stem}_metadata.json")
        self.metadata: dict[str, Any] = load_metadata(self.metadata_path)
        self.metadata["source_file"] = resolved.name
        self.axis_layers: set[str] = set(axis_layers or DEFAULT_AXIS_LAYERS)
        self.remove_axis_markers = remove_axis_markers
        self.remove_dashed_axes = remove_dashed_axes

        logger.info("Загрузка DXF: %s", resolved.name)
        self.doc: Drawing = ezdxf.readfile(str(resolved))
        self.layout: BaseLayout = self.doc.modelspace()

        initial_counts = count_entities_by_type(self.layout)
        total = sum(initial_counts.values())
        logger.info("Объектов в modelspace: %d (%d типов)", total, len(initial_counts))

    def save(self, output_path: str | Path) -> Path:
        """Сохраняет текущее состояние чертежа на диск."""
        destination = Path(output_path).expanduser().resolve()
        self.doc.saveas(str(destination))
        logger.info("DXF сохранён: %s", destination.name)
        return destination

    def _extract_text_content(self, entity: DXFGraphic) -> str:
        """Извлекает текстовое содержимое из TEXT или MTEXT."""
        try:
            if entity.dxftype() == "MTEXT":
                return entity.plain_text()  # type: ignore[attr-defined]
            return str(entity.dxf.text)
        except Exception:
            return ""

    def _extract_insert_point(self, entity: DXFGraphic) -> tuple[float, float]:
        """Возвращает координаты вставки/позиции текста."""
        try:
            if entity.dxftype() == "MTEXT":
                point = entity.dxf.insert
            else:
                point = entity.dxf.insert if hasattr(entity.dxf, "insert") else entity.dxf.start
            return float(point.x), float(point.y)
        except Exception:
            return 0.0, 0.0

    def _layer_linetype(self, layer_name: str) -> str:
        """Возвращает тип линии, назначенный слою."""
        try:
            layer = self.doc.layers.get(layer_name)
            if layer is not None:
                return str(layer.dxf.linetype)
        except Exception:
            pass
        return "Continuous"

    def _entity_is_dashed(self, entity: DXFGraphic) -> bool:
        """Проверяет, нарисована ли сущность пунктирным типом линии."""
        try:
            linetype = str(entity.dxf.linetype)
            layer_linetype = self._layer_linetype(str(entity.dxf.layer))
            return is_dashed_linetype(linetype, layer_linetype)
        except Exception:
            return False

    def clean_text_and_labels(self) -> CleanupStats:
        """
        Этап 1: удаление аннотаций TEXT и MTEXT.
        Перед удалением сохраняет содержимое, координаты и слой в JSON.
        """
        stats = CleanupStats()
        logger.info("--- Этап 1: удаление аннотаций ---")

        for entity_type in ("TEXT", "MTEXT"):
            entities = query_entities_safe(self.layout, entity_type)
            stats.add_found(entity_type, len(entities))
            logger.info("Найдено %s: %d", entity_type, len(entities))

            for entity in list(entities):
                try:
                    x, y = self._extract_insert_point(entity)
                    record = {
                        "type": entity_type,
                        "content": self._extract_text_content(entity),
                        "x": round(x, 3),
                        "y": round(y, 3),
                        "layer": str(entity.dxf.layer),
                    }
                    self.metadata["text_annotations"].append(record)
                except Exception as exc:
                    stats.skipped_errors += 1
                    logger.debug("Ошибка чтения %s: %s", entity_type, exc)
                    continue

                if delete_entity_safe(self.layout, entity, stats):
                    stats.add_removed(entity_type)

        save_metadata(self.metadata_path, self.metadata)
        stats.log_summary("Удаление аннотаций")
        return stats

    def clean_dimensions(self) -> CleanupStats:
        """Этап 2: удаление размеров, мелких линий и залитых стрелок."""
        stats = CleanupStats()
        logger.info("--- Этап 2: удаление размеров и стрелок ---")

        dimensions = query_entities_safe(self.layout, "DIMENSION")
        stats.add_found("DIMENSION", len(dimensions))
        logger.info("Найдено DIMENSION: %d", len(dimensions))
        for entity in list(dimensions):
            if delete_entity_safe(self.layout, entity, stats):
                stats.add_removed("DIMENSION")

        lines = query_entities_safe(self.layout, "LINE")
        short_lines: list[DXFGraphic] = []
        for entity in lines:
            try:
                if line_length(entity) < SHORT_LINE_MAX_LENGTH:
                    short_lines.append(entity)
            except Exception:
                stats.skipped_errors += 1

        stats.add_found("SHORT_LINE", len(short_lines))
        logger.info("Найдено коротких LINE (< %.0f мм): %d", SHORT_LINE_MAX_LENGTH, len(short_lines))
        for entity in short_lines:
            if delete_entity_safe(self.layout, entity, stats):
                stats.add_removed("SHORT_LINE")

        for entity_type in ("SOLID", "TRACE"):
            solids = query_entities_safe(self.layout, entity_type)
            arrow_solids = [entity for entity in solids if is_small_arrow_solid(entity)]
            stats.add_found(entity_type, len(arrow_solids))
            logger.info("Найдено %s-стрелок: %d", entity_type, len(arrow_solids))
            for entity in arrow_solids:
                if delete_entity_safe(self.layout, entity, stats):
                    stats.add_removed(entity_type)

        stats.log_summary("Удаление размеров и стрелок")
        return stats

    def clean_room_markers(self) -> CleanupStats:
        """
        Этап 3: удаление кругов-маркеров помещений (CIRCLE, радиус 200–400 мм).
        Координаты центров сохраняются в JSON.
        """
        stats = CleanupStats()
        logger.info("--- Этап 3: удаление кругов-маркеров ---")

        circles = query_entities_safe(self.layout, "CIRCLE")
        markers: list[DXFGraphic] = []

        for entity in circles:
            try:
                radius = float(entity.dxf.radius)
                if ROOM_MARKER_RADIUS_MIN <= radius <= ROOM_MARKER_RADIUS_MAX:
                    markers.append(entity)
            except Exception:
                stats.skipped_errors += 1

        stats.add_found("ROOM_MARKER_CIRCLE", len(markers))
        logger.info(
            "Найдено CIRCLE-маркеров (r %.0f–%.0f): %d",
            ROOM_MARKER_RADIUS_MIN,
            ROOM_MARKER_RADIUS_MAX,
            len(markers),
        )

        for entity in markers:
            try:
                center = entity.dxf.center
                record = {
                    "x": round(float(center.x), 3),
                    "y": round(float(center.y), 3),
                    "radius": round(float(entity.dxf.radius), 3),
                    "layer": str(entity.dxf.layer),
                }
                self.metadata["room_markers"].append(record)
            except Exception as exc:
                stats.skipped_errors += 1
                logger.debug("Ошибка чтения CIRCLE: %s", exc)
                continue

            if delete_entity_safe(self.layout, entity, stats):
                stats.add_removed("ROOM_MARKER_CIRCLE")

        save_metadata(self.metadata_path, self.metadata)
        stats.log_summary("Удаление кругов-маркеров")
        return stats

    def clean_hatches(self) -> CleanupStats:
        """Этап 4: удаление HATCH и пучков параллельных линий (взорванные штриховки)."""
        stats = CleanupStats()
        logger.info("--- Этап 4: удаление штриховок ---")

        hatches = query_entities_safe(self.layout, "HATCH")
        stats.add_found("HATCH", len(hatches))
        logger.info("Найдено HATCH: %d", len(hatches))
        for entity in list(hatches):
            if delete_entity_safe(self.layout, entity, stats):
                stats.add_removed("HATCH")

        remaining_lines = query_entities_safe(self.layout, "LINE")
        clusters = find_parallel_line_clusters(remaining_lines)
        stats.add_found("HATCH_LINE_CLUSTER", len(clusters))
        logger.info("Найдено пучков параллельных линий: %d", len(clusters))

        removed_lines = 0
        for cluster in clusters:
            for entity in cluster:
                if delete_entity_safe(self.layout, entity, stats):
                    removed_lines += 1
        stats.add_removed("HATCH_LINE", removed_lines)

        stats.log_summary("Удаление штриховок")
        return stats

    def clean_axis_markers(self) -> CleanupStats:
        """
        Этап 5: удаление маркеров осей и пунктирных осевых линий на заданных слоях.
        """
        stats = CleanupStats()
        logger.info("--- Этап 5: удаление осей ---")
        logger.info("Слои осей: %s", ", ".join(sorted(self.axis_layers)))

        if self.remove_axis_markers:
            for entity_type in ("CIRCLE", "ELLIPSE", "ARC"):
                entities = query_entities_safe(self.layout, entity_type)
                to_remove: list[DXFGraphic] = []

                for entity in entities:
                    try:
                        if str(entity.dxf.layer) in self.axis_layers:
                            to_remove.append(entity)
                    except Exception:
                        stats.skipped_errors += 1

                stats.add_found(entity_type, len(to_remove))
                logger.info("Найдено %s на слоях осей: %d", entity_type, len(to_remove))

                for entity in to_remove:
                    if delete_entity_safe(self.layout, entity, stats):
                        stats.add_removed(entity_type)

        if self.remove_dashed_axes:
            for entity_type in ("LINE", "LWPOLYLINE"):
                entities = query_entities_safe(self.layout, entity_type)
                to_remove: list[DXFGraphic] = []

                for entity in entities:
                    try:
                        if str(entity.dxf.layer) not in self.axis_layers:
                            continue
                        if self._entity_is_dashed(entity):
                            to_remove.append(entity)
                    except Exception:
                        stats.skipped_errors += 1

                stats.add_found(f"DASHED_{entity_type}", len(to_remove))
                logger.info("Найдено пунктирных %s на слоях осей: %d", entity_type, len(to_remove))

                for entity in to_remove:
                    if delete_entity_safe(self.layout, entity, stats):
                        stats.add_removed(f"DASHED_{entity_type}")

        stats.log_summary("Удаление осей")
        return stats
