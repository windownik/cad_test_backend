"""Сохранение и загрузка JSON-метаданных (тексты, маркеры помещений)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.common.logging_config import logger


def load_metadata(path: Path) -> dict[str, Any]:
    """Загружает JSON метаданных или создаёт пустую структуру."""
    if path.exists():
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    return {
        "source_file": "",
        "text_annotations": [],
        "room_markers": [],
    }


def save_metadata(path: Path, metadata: dict[str, Any]) -> None:
    """Сохраняет метаданные в JSON с читаемым форматированием."""
    with path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)
    logger.info("Метаданные сохранены: %s", path.name)
