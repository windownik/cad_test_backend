"""Публичный API фичи конвертации DXF → PNG."""

from __future__ import annotations

from pathlib import Path

from lib.common.io import resolve_dxf_path
from lib.converter.png_export import dxf_to_png

# ---------------------------------------------------------------------------
# Настройки конвертации
# ---------------------------------------------------------------------------

OUTPUT_FILE: str | None = None
DPI: int = 300
MAX_SIDE_PX: int = 4096


def convert_dxf_to_png(file_path: str | Path) -> Path:
    """
    Конвертирует DXF-чертеж в PNG и возвращает путь к изображению.
    """
    dxf_path = resolve_dxf_path(file_path)
    png_path = (
        Path(OUTPUT_FILE).expanduser().resolve()
        if OUTPUT_FILE is not None
        else dxf_path.with_suffix(".png")
    )
    dxf_to_png(dxf_path, png_path, dpi=DPI, max_side_px=MAX_SIDE_PX)
    return png_path
