"""Публичный API пайплайна Roboflow → DXF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lib.common.io import resolve_dxf_path
from lib.common.logging_config import logger
from lib.roboflow.api import get_api_predictions
from lib.roboflow.dxf_draw import draw_zones_to_dxf
from lib.roboflow.png_render import (
    compute_scale_meta_from_dxf,
    dxf_to_png,
    load_scale_meta,
    save_scale_meta,
)
from lib.roboflow.types import ScaleMeta


def _read_image_size(png_path: Path) -> tuple[int, int]:
    try:
        import cv2
    except ImportError as exc:
        raise ImportError(
            "Пакет opencv-python не установлен. Выполните: pip install opencv-python"
        ) from exc

    image = cv2.imread(str(png_path))
    if image is None:
        raise ValueError(f"Не удалось прочитать изображение: {png_path}")

    height_px, width_px = image.shape[:2]
    return width_px, height_px


def _default_meta_path(png_path: Path) -> Path:
    return png_path.with_name(f"{png_path.stem}_scale_meta.json")


def _default_output_dxf_path(dxf_path: Path) -> Path:
    return dxf_path.with_name(f"{dxf_path.stem}_ai_zones.dxf")


def _resolve_dxf_for_png(png_path: Path, dxf_path: str | Path | None) -> Path:
    if dxf_path is not None:
        return resolve_dxf_path(dxf_path)

    candidate = png_path.with_suffix(".dxf")
    if candidate.exists():
        return candidate

    raise FileNotFoundError(
        f"DXF не найден для PNG: {candidate}. Передайте dxf_path явно."
    )


def _resolve_scale_meta(
    png_path: Path,
    dxf_path: Path,
    scale_meta: ScaleMeta | None,
) -> ScaleMeta:
    if scale_meta is not None:
        return scale_meta

    meta_path = _default_meta_path(png_path)
    if meta_path.exists():
        return load_scale_meta(meta_path)

    logger.info("Метаданные масштаба вычисляются из DXF: %s", dxf_path.name)
    return compute_scale_meta_from_dxf(dxf_path)


def run_roboflow_pipeline(
    dxf_path: str | Path,
    png_path: str | Path | None = None,
    *,
    output_dxf_path: str | Path | None = None,
    dpi: int = 300,
    api_key: str | None = None,
    model_id: str | None = None,
) -> Path:
    """
    Полный конвейер: DXF → PNG → Roboflow API → DXF с AI-зонами.

    Returns:
        Путь к результирующему DXF.
    """
    resolved_dxf = resolve_dxf_path(dxf_path)
    png_target = (
        Path(png_path).expanduser().resolve()
        if png_path is not None
        else resolved_dxf.with_suffix(".png")
    )

    scale_meta = dxf_to_png(resolved_dxf, png_target, dpi=dpi)
    save_scale_meta(scale_meta, _default_meta_path(png_target))

    response = get_api_predictions(png_target, api_key=api_key, model_id=model_id)
    predictions: list[dict[str, Any]] = list(response.get("predictions", []))

    image_width_px, image_height_px = _read_image_size(png_target)
    output_path = (
        Path(output_dxf_path).expanduser().resolve()
        if output_dxf_path is not None
        else _default_output_dxf_path(resolved_dxf)
    )

    draw_zones_to_dxf(
        resolved_dxf,
        predictions,
        scale_meta,
        output_path,
        image_width_px=image_width_px,
        image_height_px=image_height_px,
    )
    return output_path


def recognize_from_image(
    image_path: str | Path,
    *,
    dxf_path: str | Path | None = None,
    output_dxf_path: str | Path | None = None,
    scale_meta: ScaleMeta | None = None,
    api_key: str | None = None,
    model_id: str | None = None,
) -> Path:
    """
    Распознаёт объекты на готовом PNG и наносит зоны на связанный DXF.

    Ожидается PNG, полученный из того же DXF через ``dxf_to_png``,
    либо наличие файла ``{имя_png}_scale_meta.json`` рядом с изображением.
    """
    png_target = Path(image_path).expanduser().resolve()
    if not png_target.exists():
        raise FileNotFoundError(f"Изображение не найдено: {png_target}")

    resolved_dxf = _resolve_dxf_for_png(png_target, dxf_path)
    resolved_scale_meta = _resolve_scale_meta(png_target, resolved_dxf, scale_meta)

    response = get_api_predictions(png_target, api_key=api_key, model_id=model_id)
    predictions: list[dict[str, Any]] = list(response.get("predictions", []))

    image_width_px, image_height_px = _read_image_size(png_target)
    output_path = (
        Path(output_dxf_path).expanduser().resolve()
        if output_dxf_path is not None
        else _default_output_dxf_path(resolved_dxf)
    )

    draw_zones_to_dxf(
        resolved_dxf,
        predictions,
        resolved_scale_meta,
        output_path,
        image_width_px=image_width_px,
        image_height_px=image_height_px,
    )
    return output_path
