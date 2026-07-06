"""Константы классов YOLOv8-seg для floor_plan_best.pt (5 классов Roboflow)."""

from __future__ import annotations

# Имена классов внутри .pt: {0: '-_-', 1: 'background', 2: 'door', 3: 'wall', 4: 'window'}
IGNORED_CLASS_IDS: frozenset[int] = frozenset({0, 1})

# class_id -> (слой DXF, цвет ACI, имя класса)
CLASS_LAYER_CONFIG: dict[int, tuple[str, int, str]] = {
    2: ("AI_DOORS", 1, "door"),
    3: ("AI_WALLS", 9, "wall"),
    4: ("AI_WINDOWS", 5, "window"),
}

DOOR_CLASS_ID: int = 2
WALL_CLASS_ID: int = 3
WINDOW_CLASS_ID: int = 4

# По умолчанию — только двери и окна (без background и стен)
INFERENCE_CLASS_IDS: list[int] = [DOOR_CLASS_ID, WINDOW_CLASS_ID]

# door + wall + window (если нужны все три типа)
ALL_STRUCTURE_CLASS_IDS: list[int] = [DOOR_CLASS_ID, WALL_CLASS_ID, WINDOW_CLASS_ID]
