"""Детекция пучков параллельных линий — след «взорванной» штриховки."""

from __future__ import annotations

from collections import defaultdict

from ezdxf.entities.dxfgfx import DXFGraphic

from lib.cleaning.constants import HATCH_ANGLE_BUCKET_RAD, HATCH_LINE_MIN_COUNT, HATCH_LINE_MAX_SPACING
from lib.cleaning.geometry import line_angle_rad, line_perpendicular_offset, spacing_is_uniform


def find_parallel_line_clusters(lines: list[DXFGraphic]) -> list[list[DXFGraphic]]:
    """
    Находит группы близко расположенных параллельных линий —
    типичный след «взорванной» штриховки.
    """
    buckets: dict[int, list[DXFGraphic]] = defaultdict(list)
    for line in lines:
        try:
            angle = line_angle_rad(line)
            bucket_key = int(round(angle / HATCH_ANGLE_BUCKET_RAD))
            buckets[bucket_key].append(line)
        except Exception:
            continue

    clusters: list[list[DXFGraphic]] = []

    for bucket_lines in buckets.values():
        if len(bucket_lines) < HATCH_LINE_MIN_COUNT:
            continue

        try:
            reference_angle = line_angle_rad(bucket_lines[0])
        except Exception:
            continue

        sorted_lines = sorted(
            bucket_lines,
            key=lambda entity: line_perpendicular_offset(entity, reference_angle),
        )

        current_cluster: list[DXFGraphic] = [sorted_lines[0]]
        spacings: list[float] = []

        for index in range(1, len(sorted_lines)):
            prev_offset = line_perpendicular_offset(sorted_lines[index - 1], reference_angle)
            curr_offset = line_perpendicular_offset(sorted_lines[index], reference_angle)
            spacing = abs(curr_offset - prev_offset)

            if spacing <= HATCH_LINE_MAX_SPACING:
                current_cluster.append(sorted_lines[index])
                spacings.append(spacing)
            else:
                if len(current_cluster) >= HATCH_LINE_MIN_COUNT and spacing_is_uniform(spacings):
                    clusters.append(current_cluster)
                current_cluster = [sorted_lines[index]]
                spacings = []

        if len(current_cluster) >= HATCH_LINE_MIN_COUNT and spacing_is_uniform(spacings):
            clusters.append(current_cluster)

    return clusters
