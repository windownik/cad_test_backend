"""Фича распознавания объектов на чертеже."""

from lib.recognition.constants import (
    ALL_STRUCTURE_CLASS_IDS,
    CLASS_LAYER_CONFIG,
    DOOR_CLASS_ID,
    INFERENCE_CLASS_IDS,
    WALL_CLASS_ID,
    WINDOW_CLASS_ID,
)
from lib.recognition.service import (
    detect_objects_in_dxf,
    detect_objects_in_png,
    detect_windows_in_dxf,
)
from lib.recognition.training import train_floor_plan_model
from lib.recognition.windows import (
    ObjectDetection,
    PngObjectDetection,
    WindowDetection,
    detect_and_draw_objects,
    detect_and_draw_windows,
    detect_objects,
    detect_windows,
    infer_objects_on_png,
)

__all__ = [
    "ALL_STRUCTURE_CLASS_IDS",
    "CLASS_LAYER_CONFIG",
    "DOOR_CLASS_ID",
    "INFERENCE_CLASS_IDS",
    "ObjectDetection",
    "PngObjectDetection",
    "WALL_CLASS_ID",
    "WINDOW_CLASS_ID",
    "WindowDetection",
    "detect_and_draw_objects",
    "detect_and_draw_windows",
    "detect_objects",
    "detect_objects_in_dxf",
    "detect_objects_in_png",
    "detect_windows",
    "detect_windows_in_dxf",
    "infer_objects_on_png",
    "train_floor_plan_model",
]
