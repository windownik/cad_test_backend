"""Отрисовка зон распознавания в DXF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import BaseLayout

from lib.common.io import resolve_dxf_path
from lib.common.logging_config import logger
from lib.roboflow.coordinates import prediction_to_cad_vertices
from lib.roboflow.types import CLASS_LAYER_CONFIG, RoboflowPrediction, ScaleMeta


def _ensure_ai_layers(doc: Drawing) -> None:
    for layer_name, color in (
        ("AI_WALLS", 9),
        ("AI_WINDOWS", 5),
        ("AI_DOORS", 1),
    ):
        if layer_name not in doc.layers:
            doc.layers.new(name=layer_name, dxfattribs={"color": color})


def _normalize_class_name(raw_class: Any) -> str:
    if raw_class is None:
        return ""
    return str(raw_class).strip().lower()


def _add_solid_hatch(
    msp: BaseLayout,
    vertices: list[tuple[float, float]],
    *,
    layer_name: str,
    color: int,
) -> None:
    hatch = msp.add_hatch(color=color, dxfattribs={"layer": layer_name})
    hatch.paths.add_polyline_path(vertices, is_closed=True)
    hatch.set_solid_fill(color=color)


def draw_zones_to_dxf(
    dxf_path: str | Path,
    predictions: list[dict[str, Any]] | list[RoboflowPrediction],
    scale_meta: ScaleMeta,
    output_path: str | Path,
    *,
    image_width_px: int,
    image_height_px: int,
) -> int:
    """
    Добавляет SOLID-штриховку распознанных зон в DXF на слои AI_WALLS / AI_WINDOWS / AI_DOORS.

    Args:
        dxf_path: Исходный DXF-файл.
        predictions: Список предсказаний Roboflow (центр + width/height в пикселях).
        scale_meta: Метаданные масштаба (x_min, y_min, cad_width, cad_height).
        output_path: Путь для сохранения результата.
        image_width_px: Ширина PNG в пикселях.
        image_height_px: Высота PNG в пикселях.

    Returns:
        Количество успешно добавленных зон.

    Raises:
        ValueError: DXF повреждён или некорректен.
    """
    resolved_dxf = resolve_dxf_path(dxf_path)
    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        doc = ezdxf.readfile(str(resolved_dxf))
    except ezdxf.DXFStructureError as exc:
        raise ValueError(f"Повреждённый или некорректный DXF: {resolved_dxf}") from exc

    msp = doc.modelspace()
    _ensure_ai_layers(doc)

    drawn_count = 0
    skipped_count = 0

    for raw_prediction in predictions:
        class_name = _normalize_class_name(raw_prediction.get("class"))
        layer_config = CLASS_LAYER_CONFIG.get(class_name)
        if layer_config is None:
            skipped_count += 1
            logger.debug("Пропущен неизвестный класс: %s", class_name)
            continue

        layer_name, color = layer_config
        try:
            prediction = RoboflowPrediction(
                x=float(raw_prediction["x"]),
                y=float(raw_prediction["y"]),
                width=float(raw_prediction["width"]),
                height=float(raw_prediction["height"]),
            )
            vertices = prediction_to_cad_vertices(
                prediction,
                scale_meta,
                image_width_px=image_width_px,
                image_height_px=image_height_px,
            )
            _add_solid_hatch(msp, vertices, layer_name=layer_name, color=color)
            drawn_count += 1
        except (KeyError, TypeError, ValueError) as exc:
            skipped_count += 1
            logger.warning("Не удалось обработать предсказание: %s", exc)

    try:
        doc.saveas(str(destination))
    except OSError as exc:
        raise ValueError(f"Не удалось сохранить DXF: {destination}") from exc

    logger.info(
        "DXF с AI-зонами сохранён: %s (добавлено %d, пропущено %d)",
        destination.name,
        drawn_count,
        skipped_count,
    )
    return drawn_count
