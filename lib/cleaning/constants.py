"""Константы этапов очистки и пороговые значения детекции."""

from __future__ import annotations

import math

# Порог длины «мелкой» линии (стрелки, засечки размеров), мм
SHORT_LINE_MAX_LENGTH: float = 150.0

# Диапазон радиуса кругов-маркеров номеров помещений, мм
ROOM_MARKER_RADIUS_MIN: float = 200.0
ROOM_MARKER_RADIUS_MAX: float = 400.0

# Максимальная площадь залитого треугольника-стрелки, мм²
ARROW_SOLID_MAX_AREA: float = 25_000.0

# Параметры детекции «взорванных» штриховок (пучки параллельных линий)
HATCH_LINE_MIN_COUNT: int = 3
HATCH_LINE_MAX_SPACING: float = 300.0
HATCH_LINE_SPACING_TOLERANCE: float = 0.25
HATCH_ANGLE_BUCKET_RAD: float = math.radians(3.0)

# Слои с маркерами осей здания (CIRCLE, ELLIPSE, ARC) по умолчанию
DEFAULT_AXIS_LAYERS: tuple[str, ...] = (
    "Новый_0_Ном._пера__7",
    "Новый_0_Ном._пера__8",
)

# Ключевые слова в имени типа линии для детекции пунктира
DASHED_LINETYPE_KEYWORDS: tuple[str, ...] = (
    "штрих",
    "пунктир",
    "dash",
    "dot",
    "hidden",
    "center",
    "phantom",
)

# Суффикс итогового очищенного файла: floor1_cleaned.dxf
OUTPUT_SUFFIX: str = "_cleaned"

STEP_LABELS: dict[int, str] = {
    1: "Удаление аннотаций (TEXT, MTEXT)",
    2: "Удаление размеров и стрелок (DIMENSION, мелкие линии, SOLID/TRACE)",
    3: "Удаление кругов-маркеров помещений (CIRCLE)",
    4: "Удаление штриховок (HATCH и пучки параллельных линий)",
    5: "Удаление осей (маркеры, пунктирные линии)",
}
