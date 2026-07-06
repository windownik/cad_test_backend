"""Рендер DXF в PNG и извлечение метаданных масштаба."""

from __future__ import annotations

import json
from pathlib import Path

import ezdxf
from ezdxf import bbox as ezdxf_bbox

from lib.common.io import resolve_dxf_path
from lib.common.logging_config import logger
from lib.converter.png_export import PngExportMeta, dxf_to_png as _dxf_to_png
from lib.roboflow.types import ScaleMeta


def dxf_to_png(
    dxf_path: str | Path,
    png_path: str | Path,
    dpi: int = 300,
) -> ScaleMeta:
    """
    Рендерит modelspace DXF в PNG и возвращает метаданные масштаба.

    Использует ezdxf.addons.drawing + matplotlib с фиксированным bbox
    (без лишних полей по краям изображения).
    """
    try:
        full_meta: PngExportMeta = _dxf_to_png(dxf_path, png_path, dpi=dpi)
    except ezdxf.DXFStructureError as exc:
        raise ValueError(f"Повреждённый или некорректный DXF: {dxf_path}") from exc
    except OSError as exc:
        raise ValueError(f"Не удалось сохранить PNG: {png_path}") from exc

    scale_meta: ScaleMeta = {
        "x_min": full_meta["x_min"],
        "y_min": full_meta["y_min"],
        "cad_width": full_meta["cad_width"],
        "cad_height": full_meta["cad_height"],
    }
    return scale_meta


def save_scale_meta(scale_meta: ScaleMeta, meta_path: str | Path) -> Path:
    """Сохраняет метаданные масштаба рядом с PNG для последующего инференса."""
    destination = Path(meta_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as file:
        json.dump(scale_meta, file, ensure_ascii=False, indent=2)
    logger.info("Метаданные масштаба сохранены: %s", destination.name)
    return destination


def load_scale_meta(meta_path: str | Path) -> ScaleMeta:
    """Загружает ранее сохранённые метаданные масштаба."""
    path = Path(meta_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Файл метаданных не найден: {path}")

    with path.open(encoding="utf-8") as file:
        payload = json.load(file)

    required = {"x_min", "y_min", "cad_width", "cad_height"}
    missing = required - payload.keys()
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"В метаданных отсутствуют поля: {missing_list}")

    return ScaleMeta(
        x_min=float(payload["x_min"]),
        y_min=float(payload["y_min"]),
        cad_width=float(payload["cad_width"]),
        cad_height=float(payload["cad_height"]),
    )


def compute_scale_meta_from_dxf(dxf_path: str | Path) -> ScaleMeta:
    """Вычисляет метаданные масштаба из bbox DXF без повторного рендера PNG."""
    resolved = resolve_dxf_path(dxf_path)
    try:
        doc = ezdxf.readfile(str(resolved))
        bbox = ezdxf_bbox.extents(doc.modelspace())
    except ezdxf.DXFStructureError as exc:
        raise ValueError(f"Повреждённый или некорректный DXF: {resolved}") from exc

    x_min, y_min = bbox.extmin[0], bbox.extmin[1]
    x_max, y_max = bbox.extmax[0], bbox.extmax[1]
    return ScaleMeta(
        x_min=x_min,
        y_min=y_min,
        cad_width=x_max - x_min,
        cad_height=y_max - y_min,
    )
