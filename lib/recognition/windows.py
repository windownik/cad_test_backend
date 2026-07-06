"""Поиск объектов через YOLO и отрисовка заливки в DXF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import BaseLayout

from lib.common.io import resolve_dxf_path
from lib.common.logging_config import logger
from lib.converter.png_export import PngExportMeta
from lib.recognition.constants import (
    CLASS_LAYER_CONFIG,
    INFERENCE_CLASS_IDS,
    WINDOW_CLASS_ID,
)
from lib.recognition.coordinates import pixel_box_to_cad_vertices


@dataclass(frozen=True)
class PngObjectDetection:
    """Результат детекции на PNG (только пиксельные координаты)."""

    class_id: int
    class_name: str
    confidence: float
    pixel_box: tuple[float, float, float, float]


@dataclass(frozen=True)
class ObjectDetection:
    """Результат детекции одного объекта."""

    class_id: int
    class_name: str
    confidence: float
    pixel_box: tuple[float, float, float, float]
    cad_vertices: list[tuple[float, float]]


# Обратная совместимость
WindowDetection = ObjectDetection


def _resolve_class_ids(class_ids: set[int] | None) -> list[int]:
    allowed = sorted(class_ids or set(INFERENCE_CLASS_IDS))
    unknown = set(allowed) - set(CLASS_LAYER_CONFIG)
    if unknown:
        raise ValueError(f"Неизвестные class_id для инференса: {sorted(unknown)}")
    return allowed


def _ensure_layers(doc: Drawing, class_ids: set[int]) -> None:
    for class_id in class_ids:
        layer_name, color, _ = CLASS_LAYER_CONFIG[class_id]
        if layer_name not in doc.layers:
            doc.layers.new(name=layer_name, dxfattribs={"color": color})


def _add_object_hatch(
    msp: BaseLayout,
    vertices: list[tuple[float, float]],
    *,
    layer_name: str,
    hatch_color: int,
) -> None:
    hatch = msp.add_hatch(color=hatch_color, dxfattribs={"layer": layer_name})
    hatch.paths.add_polyline_path(vertices, is_closed=True)
    hatch.set_solid_fill(color=hatch_color)


def _run_yolo_on_png(
    png_path: str | Path,
    model_path: str | Path,
    *,
    class_ids: set[int] | None = None,
    confidence_threshold: float = 0.25,
) -> tuple[list[PngObjectDetection], object]:
    """Запускает YOLO с фильтром classes=[...] и возвращает детекции."""
    import cv2
    from ultralytics import YOLO

    image_path = Path(png_path).expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"PNG не найден: {image_path}")

    model_file = Path(model_path).expanduser().resolve()
    if not model_file.exists():
        raise FileNotFoundError(f"Модель YOLO не найдена: {model_file}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Не удалось прочитать изображение: {image_path}")

    yolo_classes = _resolve_class_ids(class_ids)
    model = YOLO(str(model_file))
    results = model(
        str(image_path),
        classes=yolo_classes,
        verbose=False,
    )
    result = results[0]

    detections: list[PngObjectDetection] = []
    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0])
            if class_id not in CLASS_LAYER_CONFIG:
                continue

            confidence = float(box.conf[0])
            if confidence < confidence_threshold:
                continue

            _, _, class_name = CLASS_LAYER_CONFIG[class_id]
            px1, py1, px2, py2 = box.xyxy[0].tolist()
            detections.append(
                PngObjectDetection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    pixel_box=(px1, py1, px2, py2),
                )
            )

    return detections, result


def infer_objects_on_png(
    png_path: str | Path,
    model_path: str | Path,
    *,
    class_ids: set[int] | None = None,
    confidence_threshold: float = 0.25,
    output_png: str | Path | None = None,
) -> tuple[Path, list[PngObjectDetection]]:
    """
    Распознаёт объекты на PNG и сохраняет изображение с bbox для проверки.

    DXF не используется — только инференс и визуализация результата.
    """
    import cv2

    image_path = Path(png_path).expanduser().resolve()
    detections, result = _run_yolo_on_png(
        image_path,
        model_path,
        class_ids=class_ids,
        confidence_threshold=confidence_threshold,
    )

    preview_path = (
        Path(output_png).expanduser().resolve()
        if output_png is not None
        else image_path.with_name(f"{image_path.stem}_detected.png")
    )
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(preview_path), result.plot())

    counts: dict[str, int] = {}
    for det in detections:
        counts[det.class_name] = counts.get(det.class_name, 0) + 1
    logger.info("Найдено объектов: %s", counts or "0")
    logger.info("Превью сохранено: %s", preview_path.name)
    return preview_path, detections


def detect_objects(
    png_path: str | Path,
    model_path: str | Path,
    meta: PngExportMeta,
    *,
    class_ids: set[int] | None = None,
    confidence_threshold: float = 0.25,
) -> list[ObjectDetection]:
    """Запускает YOLO на PNG и возвращает объекты с CAD-координатами."""
    import cv2

    image_path = Path(png_path).expanduser().resolve()
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Не удалось прочитать изображение: {image_path}")

    image_height_px, image_width_px = image.shape[:2]
    png_detections, _ = _run_yolo_on_png(
        image_path,
        model_path,
        class_ids=class_ids,
        confidence_threshold=confidence_threshold,
    )

    detections: list[ObjectDetection] = []
    for item in png_detections:
        px1, py1, px2, py2 = item.pixel_box
        vertices = pixel_box_to_cad_vertices(
            px1,
            py1,
            px2,
            py2,
            meta,
            image_width_px=image_width_px,
            image_height_px=image_height_px,
        )
        detections.append(
            ObjectDetection(
                class_id=item.class_id,
                class_name=item.class_name,
                confidence=item.confidence,
                pixel_box=item.pixel_box,
                cad_vertices=vertices,
            )
        )

    counts: dict[str, int] = {}
    for det in detections:
        counts[det.class_name] = counts.get(det.class_name, 0) + 1
    logger.info("Найдено объектов: %s", counts or "0")
    return detections


def detect_windows(
    png_path: str | Path,
    model_path: str | Path,
    meta: PngExportMeta,
    *,
    window_class_id: int = WINDOW_CLASS_ID,
    confidence_threshold: float = 0.25,
) -> list[ObjectDetection]:
    """Запускает YOLO и возвращает только окна."""
    return detect_objects(
        png_path,
        model_path,
        meta,
        class_ids={window_class_id},
        confidence_threshold=confidence_threshold,
    )


def detect_and_draw_objects(
    dxf_path: str | Path,
    png_path: str | Path,
    model_path: str | Path,
    meta: PngExportMeta,
    output_dxf_path: str | Path,
    *,
    class_ids: set[int] | None = None,
    confidence_threshold: float = 0.25,
) -> list[ObjectDetection]:
    """Находит объекты на PNG через YOLO и добавляет SOLID-заливку в DXF."""
    resolved_dxf = resolve_dxf_path(dxf_path)
    destination = Path(output_dxf_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    allowed_classes = class_ids or set(INFERENCE_CLASS_IDS)
    detections = detect_objects(
        png_path,
        model_path,
        meta,
        class_ids=allowed_classes,
        confidence_threshold=confidence_threshold,
    )

    doc = ezdxf.readfile(str(resolved_dxf))
    msp = doc.modelspace()
    found_class_ids = {det.class_id for det in detections}
    _ensure_layers(doc, found_class_ids)

    for detection in detections:
        layer_name, color, _ = CLASS_LAYER_CONFIG[detection.class_id]
        _add_object_hatch(
            msp,
            detection.cad_vertices,
            layer_name=layer_name,
            hatch_color=color,
        )

    doc.saveas(str(destination))
    logger.info("DXF с найденными объектами сохранён: %s", destination.name)
    return detections


def detect_and_draw_windows(
    dxf_path: str | Path,
    png_path: str | Path,
    model_path: str | Path,
    meta: PngExportMeta,
    output_dxf_path: str | Path,
    *,
    window_class_id: int = WINDOW_CLASS_ID,
    confidence_threshold: float = 0.25,
    layer_name: str = "AI_WINDOWS",
    layer_color: int = 5,
) -> list[ObjectDetection]:
    """Находит только окна на PNG через YOLO и добавляет заливку в DXF."""
    del layer_name, layer_color
    return detect_and_draw_objects(
        dxf_path,
        png_path,
        model_path,
        meta,
        output_dxf_path,
        class_ids={window_class_id},
        confidence_threshold=confidence_threshold,
    )
