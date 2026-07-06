"""Публичный API фичи очистки DXF."""

from __future__ import annotations

from pathlib import Path

from lib.cleaning.constants import DEFAULT_AXIS_LAYERS
from lib.cleaning.pipeline import run_pipeline
from lib.common.io import resolve_dxf_path

# ---------------------------------------------------------------------------
# Настройки очистки
# ---------------------------------------------------------------------------

OUTPUT_FILE: str | None = None

REMOVE_TEXT_AND_LABELS: bool = True
REMOVE_DIMENSIONS: bool = True
REMOVE_ROOM_MARKERS: bool = True
REMOVE_HATCHES: bool = True
REMOVE_AXIS_MARKERS: bool = True
REMOVE_DASHED_AXES: bool = True

AXIS_LAYERS: list[str] = list(DEFAULT_AXIS_LAYERS)


def _build_selected_steps() -> list[int]:
    """Собирает список этапов из bool-флагов в порядке 1 → 5."""
    steps: list[int] = []
    if REMOVE_TEXT_AND_LABELS:
        steps.append(1)
    if REMOVE_DIMENSIONS:
        steps.append(2)
    if REMOVE_ROOM_MARKERS:
        steps.append(3)
    if REMOVE_HATCHES:
        steps.append(4)
    if REMOVE_AXIS_MARKERS or REMOVE_DASHED_AXES:
        steps.append(5)
    return steps


def clean_dxf(file_path: str | Path) -> Path:
    """
    Очищает DXF-чертеж по настроенным этапам и возвращает путь к результату.
    """
    dxf_path = resolve_dxf_path(file_path)
    selected_steps = _build_selected_steps()

    if not selected_steps:
        raise ValueError("Ни один этап очистки не выбран.")

    return run_pipeline(
        dxf_path,
        selected_steps,
        OUTPUT_FILE,
        axis_layers=AXIS_LAYERS,
        remove_axis_markers=REMOVE_AXIS_MARKERS,
        remove_dashed_axes=REMOVE_DASHED_AXES,
    )
