"""Проверка и разрешение путей к входным DXF-файлам."""

from __future__ import annotations

from pathlib import Path


def resolve_dxf_path(file_path: str | Path) -> Path:
    """
    Проверяет существование файла и возвращает абсолютный путь.
    Поддерживается только формат DXF.
    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    if path.suffix.lower() != ".dxf":
        raise ValueError(f"Поддерживаются только DXF-файлы, получен: {path.suffix}")

    return path
