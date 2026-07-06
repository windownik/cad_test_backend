"""Публичный API фичи распознавания объектов на чертеже."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib.common.io import resolve_dxf_path
from lib.converter.png_export import PngExportMeta, dxf_to_png
from lib.recognition.windows import ObjectDetection, PngObjectDetection, detect_and_draw_objects, infer_objects_on_png

# ---------------------------------------------------------------------------
# Настройки распознавания
# ---------------------------------------------------------------------------

OUTPUT_FILE: str | None = None
MODEL_PATH: str = "models/floor_plan_best.pt"
CONFIDENCE_THRESHOLD: float = 0.25


def _load_png_meta(meta_path: Path) -> PngExportMeta:
    with meta_path.open(encoding="utf-8") as file:
        payload: dict[str, Any] = json.load(file)

    if "png_export" in payload:
        payload = payload["png_export"]

    required_keys = {
        "x_min",
        "y_min",
        "x_max",
        "y_max",
        "cad_width",
        "cad_height",
        "image_width_px",
        "image_height_px",
    }
    missing = required_keys - payload.keys()
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"В метаданных отсутствуют поля: {missing_list}")

    return PngExportMeta(
        x_min=float(payload["x_min"]),
        y_min=float(payload["y_min"]),
        x_max=float(payload["x_max"]),
        y_max=float(payload["y_max"]),
        cad_width=float(payload["cad_width"]),
        cad_height=float(payload["cad_height"]),
        image_width_px=int(payload["image_width_px"]),
        image_height_px=int(payload["image_height_px"]),
    )


def detect_objects_in_png(
    png_path: str | Path,
    *,
    model_path: str | Path | None = None,
    output_png: str | Path | None = None,
) -> tuple[Path, list[PngObjectDetection]]:
    """
    Распознаёт двери, стены и окна на PNG.

    Возвращает путь к превью с bbox и список детекций. DXF не создаётся.
    """
    return infer_objects_on_png(
        png_path,
        model_path or MODEL_PATH,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        output_png=output_png,
    )


def detect_objects_in_dxf(
    dxf_path: str | Path,
    png_path: str | Path | None = None,
    *,
    model_path: str | Path | None = None,
    meta: PngExportMeta | None = None,
    meta_path: str | Path | None = None,
) -> tuple[Path, list[ObjectDetection]]:
    """
    Распознаёт двери, стены и окна на PNG и сохраняет DXF с AI-заливкой.

    Если PNG не передан, он генерируется из DXF через dxf_to_png.
    """
    resolved_dxf = resolve_dxf_path(dxf_path)

    if png_path is None:
        png_target = resolved_dxf.with_suffix(".png")
        png_meta = dxf_to_png(resolved_dxf, png_target)
    else:
        png_target = Path(png_path).expanduser().resolve()
        if meta is not None:
            png_meta = meta
        elif meta_path is not None:
            png_meta = _load_png_meta(Path(meta_path).expanduser().resolve())
        else:
            raise ValueError("Передайте meta или meta_path, если PNG уже существует.")

    output_dxf = (
        Path(OUTPUT_FILE).expanduser().resolve()
        if OUTPUT_FILE is not None
        else resolved_dxf.with_name(f"{resolved_dxf.stem}_detected.dxf")
    )

    detections = detect_and_draw_objects(
        resolved_dxf,
        png_target,
        model_path or MODEL_PATH,
        png_meta,
        output_dxf,
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )
    return output_dxf, detections


def detect_windows_in_dxf(
    dxf_path: str | Path,
    png_path: str | Path | None = None,
    *,
    model_path: str | Path | None = None,
    meta: PngExportMeta | None = None,
    meta_path: str | Path | None = None,
) -> tuple[Path, list[ObjectDetection]]:
    """Распознаёт только окна (class_id=4) и сохраняет DXF с заливкой."""
    resolved_dxf = resolve_dxf_path(dxf_path)

    if png_path is None:
        png_target = resolved_dxf.with_suffix(".png")
        png_meta = dxf_to_png(resolved_dxf, png_target)
    else:
        png_target = Path(png_path).expanduser().resolve()
        if meta is not None:
            png_meta = meta
        elif meta_path is not None:
            png_meta = _load_png_meta(Path(meta_path).expanduser().resolve())
        else:
            raise ValueError("Передайте meta или meta_path, если PNG уже существует.")

    output_dxf = (
        Path(OUTPUT_FILE).expanduser().resolve()
        if OUTPUT_FILE is not None
        else resolved_dxf.with_name(f"{resolved_dxf.stem}_with_windows.dxf")
    )

    detections = detect_and_draw_objects(
        resolved_dxf,
        png_target,
        model_path or MODEL_PATH,
        png_meta,
        output_dxf,
        class_ids={4},
        confidence_threshold=CONFIDENCE_THRESHOLD,
    )
    return output_dxf, detections
