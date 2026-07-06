"""Счётчики статистики этапов очистки."""

from __future__ import annotations

from dataclasses import dataclass, field

from lib.common.logging_config import logger


@dataclass
class CleanupStats:
    """Счётчики найденных и удалённых объектов по типам."""

    found: dict[str, int] = field(default_factory=dict)
    removed: dict[str, int] = field(default_factory=dict)
    skipped_errors: int = 0

    def add_found(self, entity_type: str, count: int = 1) -> None:
        self.found[entity_type] = self.found.get(entity_type, 0) + count

    def add_removed(self, entity_type: str, count: int = 1) -> None:
        self.removed[entity_type] = self.removed.get(entity_type, 0) + count

    def log_summary(self, step_name: str) -> None:
        """Выводит сводку по этапу в консоль."""
        logger.info("=== Итоги этапа: %s ===", step_name)
        all_types = sorted(set(self.found) | set(self.removed))
        for entity_type in all_types:
            found = self.found.get(entity_type, 0)
            removed = self.removed.get(entity_type, 0)
            logger.info("  %-20s найдено: %5d | удалено: %5d", entity_type, found, removed)
        if self.skipped_errors:
            logger.warning("  Пропущено повреждённых объектов: %d", self.skipped_errors)
