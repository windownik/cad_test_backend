"""Оркестрация конвейера: последовательная обработка и сохранение результата."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from lib.cleaning.cleaner import DXFCleaner
from lib.cleaning.constants import OUTPUT_SUFFIX, STEP_LABELS
from lib.cleaning.stats import CleanupStats
from lib.common.logging_config import logger


STEP_METHODS: dict[int, tuple[str, Callable[[DXFCleaner], CleanupStats]]] = {
    1: ("clean_text_and_labels", DXFCleaner.clean_text_and_labels),
    2: ("clean_dimensions", DXFCleaner.clean_dimensions),
    3: ("clean_room_markers", DXFCleaner.clean_room_markers),
    4: ("clean_hatches", DXFCleaner.clean_hatches),
    5: ("clean_axis_markers", DXFCleaner.clean_axis_markers),
}


def build_output_path(source: Path, output_file: str | Path | None = None) -> Path:
    """
    Формирует путь итогового файла.
    Если output_file не задан — {имя_исходника}_cleaned.dxf рядом с исходником.
    """
    if output_file is not None:
        return Path(output_file).expanduser().resolve()
    return source.with_name(f"{source.stem}{OUTPUT_SUFFIX}.dxf")


def run_pipeline(
    source_path: str | Path,
    selected_steps: list[int],
    output_file: str | Path | None = None,
    axis_layers: list[str] | tuple[str, ...] | None = None,
    *,
    remove_axis_markers: bool = True,
    remove_dashed_axes: bool = True,
) -> Path:
    """
    Последовательно применяет выбранные этапы к одному DXF в памяти.
    Сохраняет результат один раз в конце.
    """
    source = Path(source_path).expanduser().resolve()
    cleaner = DXFCleaner(
        source,
        axis_layers=axis_layers,
        remove_axis_markers=remove_axis_markers,
        remove_dashed_axes=remove_dashed_axes,
    )

    for step_id in selected_steps:
        method_name, method = STEP_METHODS[step_id]
        label = STEP_LABELS[step_id]
        logger.info("Этап %d: %s (%s)...", step_id, label, method_name)

        try:
            method(cleaner)
        except Exception as exc:
            logger.error("Критическая ошибка на этапе %d: %s", step_id, exc, exc_info=True)
            raise

    output_path = build_output_path(source, output_file)
    cleaner.save(output_path)
    return output_path
